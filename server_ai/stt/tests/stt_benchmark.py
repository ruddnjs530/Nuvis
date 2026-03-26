import os
import json
import time
import argparse
from pathlib import Path

# ==============================================================================
# [교육용 주석] STT 모델 & 파서 벤치마크 (성능 측정/비교) 도구
# ==============================================================================
# 목적: 파인튜닝 하기 전의 멍청한 'base 모델'과, AI Hub 데이터를 먹인 'v2 모델'이
#       실제 로봇 제어 명령어에 대해 인식율이 얼마나 향상되었는지 정량 비교(Accuracy %)하고
#       stt_parser가 정확히 키워드를 매핑하는지 통합 검증하는 평가용 프레임워크입니다.
# ==============================================================================

# TTS(글자->음성 변환) 라이브러리가 없으면 이 스크립트의 핵심인 
# '성우 음성 자동 합성 평가'가 불가하므로 친절히 안내 후 종료합니다.
try:
    from gtts import gTTS
except ImportError:
    print("❌ 'gTTS' 라이브러리가 설치되어 있지 않습니다.")
    print("명령프롬프트에서 다음을 실행해주세요: pip install gTTS")
    exit(1)

import librosa
import torch
from stt_parser import parse_voice_command
from transformers import WhisperForConditionalGeneration, WhisperProcessor

# 보기 싫은 시스템 경고성 로그들을 숨겨서 터미널 출력을 깔끔하게 만듭니다.
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).parent
MODEL_V2 = BASE_DIR / "model" / "v2_full"
MODEL_V1 = BASE_DIR / "model" / "whisper-smarthome"
BASE_MODEL = "openai/whisper-small" # 기초 공사. 순정 모델

# CLI(명령프롬프트)로 어떤 모델을 로드할지 옵션을 선택하는 구조
MODEL_CHOICES = {
    "auto": "auto",
    "base": BASE_MODEL,
    "v1": str(MODEL_V1),
    "v2": str(MODEL_V2),
}

# ─────────────────────────────────────────
# 1. 평가할 테스트 데이터셋 객체 (그라운드 트루스 - 정답지)
# ─────────────────────────────────────────
# 형식: {"text": "AI에게 들려줄 한국어 문장 (발화)", "expected": { 파서가 최종적으로 내뱉어야 할 기계적 JSON 정답 형태 }}
TEST_CASES = [
    {
        "text": "거실로 가서 공기청정기 켜줘",
        "expected": {"action": "move_and_operate", "roomId": 2, "module": "air_purifier", "state": "on"}
    },
    {
        "text": "안방 가습기 좀 꺼줄래",
        "expected": {"action": "move_and_operate", "roomId": 3, "module": "humidifier", "state": "off"}
    },
    {
        "text": "그냥 주방으로 이동해",
        "expected": {"action": "move", "roomId": 4, "module": None, "state": None}
    },
    {
        "text": "제습기 작동", # 주어(방)가 생략된 경우
        "expected": {"action": "operate_module", "roomId": None, "module": "dehumidifier", "state": "on"}
    },
    {
        "text": "침실 공기청정기 멈춰",
        "expected": {"action": "move_and_operate", "roomId": 3, "module": "air_purifier", "state": "off"}
    },
    {
        "text": "내방으로 와",
        "expected": {"action": "move", "roomId": 3, "module": None, "state": None}
    },
    {
        "text": "스테이션으로 돌아가",
        "expected": {"action": "move", "roomId": 1, "module": None, "state": None}
    },
    # 예외 상황 및 복합명령 헷갈리는 테스트 (과연 가습기를 켤까?)
    {
        "text": "거실 말고 안방 가습기 편하게 켜줄래",
        "expected": {"action": "move_and_operate", "roomId": 3, "module": "humidifier", "state": "on"}
    },
    {
        "text": "주방 공기청정기 켜지마",
        "expected": {"action": "move_and_operate", "roomId": 4, "module": "air_purifier", "state": "off"}
    },
    # 예외 상황 테스트 (아예 스마트홈 로봇이 지원 안하는 등록되지 않은 기기 '보일러')
    {
        "text": "보일러 켜",
        "expected": {"action": "none", "roomId": None, "module": None, "state": None} 
    }
]

AUDIO_DIR = "test_audio"

def generate_test_audios():
    """
    [구글 TTS 기믹]
    매번 연구원이 직접 문장을 녹음할 수 없으니, gTTS(Google Text-to-Speech)를 활용하여
    위 TEST_CASES에 적어둔 "거실로 가서..." 텍스트를 진짜 사람 목소리가 담긴 mp3 파일로 뚝딱 오토매틱하게 뱉어냅니다.
    """
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
        
    print(f"[{AUDIO_DIR}] 디렉토리에 테스트용 오디오 파일을 생성합니다...")
    
    for idx, case in enumerate(TEST_CASES):
        filename = os.path.join(AUDIO_DIR, f"test_{idx:02d}.mp3")
        case["audio_path"] = filename
        
        # mp3 파일이 이미 만들어져 있으면 재생성 트래픽을 아낍니다. (캐싱)
        if not os.path.exists(filename):
            tts = gTTS(text=case["text"], lang='ko')
            tts.save(filename)
            print(f"  - 생성 완료: {filename} ('{case['text']}')")
    
    print("✅ 오디오 생성 완료!\n")

def resolve_model_path(model_choice: str = "auto") -> tuple[str, str]:
    """사용자가 고른 옵션(v1이냐 v2냐)에 따라 어떤 가중치 폴더 경로를 읽어올지 스위칭해주는 라우터"""
    if model_choice == "base":
        print(f"📡 Loading Base Model: {BASE_MODEL}")
        return BASE_MODEL, "base"

    if model_choice == "v2":
        if not MODEL_V2.exists():
            raise FileNotFoundError(f"Model path not found: {MODEL_V2}")
        print(f"🔥 Loading Fine-tuned Model V2: {MODEL_V2}")
        return str(MODEL_V2), "v2"

    if model_choice == "v1":
        if not MODEL_V1.exists():
            raise FileNotFoundError(f"Model path not found: {MODEL_V1}")
        print(f"🔥 Loading Fine-tuned Model V1: {MODEL_V1}")
        return str(MODEL_V1), "v1"

    # auto 모드일 때 최신 모델부터 역순으로 찾아 내려오는 폴백(Fallback) 구조
    if MODEL_V2.exists():
        print(f"🔥 Loading Fine-tuned Model V2: {MODEL_V2}")
        return str(MODEL_V2), "v2"

    if MODEL_V1.exists():
        print(f"🔥 Loading Fine-tuned Model V1: {MODEL_V1}")
        return str(MODEL_V1), "v1"

    print(f"📡 Loading Base Model: {BASE_MODEL}")
    return BASE_MODEL, "base"


def load_stt_model(model_choice: str = "auto"):
    """
    결정된 모델 경로를 받아와서, HuggingFace Transformers를 통해 실제 GPU/CPU 메모리에 인공지능을 올려버리는 핵심 함수.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("⚠️ GPU를 찾을 수 없어 CPU 환경에서 실행합니다. 속도가 느릴 수 있습니다.")
    else:
        print(f"✅ GPU 환경 감지됨. (장치: {device})")

    model_path, resolved_choice = resolve_model_path(model_choice)
    # 텍스트와 음성을 매핑해주는 전처리기
    processor = WhisperProcessor.from_pretrained(model_path)
    # 진짜 딥러닝 뇌 신경망
    model = WhisperForConditionalGeneration.from_pretrained(model_path).to(device)
    
    # 벤치마크 모델 랭귀지 포커싱 설정
    model.generation_config.language = "korean"
    model.generation_config.task = "transcribe"
    model.generation_config.forced_decoder_ids = None

    print("✅ Model loaded!\n")
    return processor, model, device, resolved_choice


def transcribe_audio(processor, model, device: str, audio_path: str) -> str:
    """단일 오디오 파일 1개를 입력받아 한국어 텍스트 문장을 반환받아옵니다."""
    # librosa.load로 구글이 만들어준 mp3를 읽어서 16kHz로 리샘플링
    audio_input, _ = librosa.load(audio_path, sr=16000)
    
    # 텐서 모양잡기
    inputs = processor(
        audio_input,
        sampling_rate=16000,
        return_tensors="pt",
        return_attention_mask=True,
    )
    input_features = inputs.input_features.to(device)
    attention_mask = getattr(inputs, "attention_mask", None)
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)

    # torch.inference_mode(): "이제부터 훈련/학습을 안 할거고 추측만 할거니까 쓸데없이 역전파 미분값 계산(메모리 낭비) 하지마" 라는 옵션. 속도가 확 빨라집니다.
    with torch.inference_mode():
        predicted_ids = model.generate(
            input_features=input_features,
            attention_mask=attention_mask,
        )
        
    return processor.batch_decode(predicted_ids, skip_special_tokens=True)[0].strip()


def run_benchmark(model_choice: str = "auto") -> float:
    """
    STT 파이프라인의 핵심인 1) 음성인식 2) 파서 모듈 변환 의 양극단(E2E) 정확도(Accuracy)를 측정하는 감독관입니다.
    """
    # 1. 텍스트를 TTS 돌려 구글 목소리로 저장
    generate_test_audios()
    
    # 2. 평가받을 학생(모델) 소환
    processor, model, device, resolved_choice = load_stt_model(model_choice)
    
    print(f"=== 정확도 테스트 시작 ({resolved_choice}) ===")
    total_cases = len(TEST_CASES)
    parsing_success_count = 0
    
    # 9문제 연속 출제
    for idx, case in enumerate(TEST_CASES):
        audio_path = case["audio_path"]
        expected = case["expected"]
        original_text = case["text"]
        
        start_time = time.time()
        
        # [Step 1] Whisper 추론 (소리 -> 글씨)
        recognized_text = transcribe_audio(processor, model, device, audio_path)
        
        # [Step 2] 로봇 명령어 파싱 룰베이스 처리 (글씨 -> JSON)
        parsed_str = parse_voice_command(recognized_text)
        parsed_json = json.loads(parsed_str)
        
        elapsed_time = round(time.time() - start_time, 2)
        
        # [Step 3] 검증(Assertions) 채점 로직
        # 파싱 오류가 있는 경우("error")는 완전 엉터리 답(none, none)을 냈다고 간주시킴
        if "error" in parsed_json:
             actual_parsed = {"action": "none", "roomId": None, "module": None, "state": None}
        else:
             actual_parsed = {
                 "action": parsed_json.get("action"),
                 "roomId": parsed_json.get("roomId"),
                 "module": parsed_json.get("module"),
                 "state": parsed_json.get("state")
             }
        
        # 예상했던 키/밸류가 기계가 준 실제 키/밸류와 하나라도 다르면 틀린 문제로 취급 (Strict 모듈 매칭)
        is_exact_match = True
        for key, expected_val in expected.items():
            if actual_parsed[key] != expected_val:
                is_exact_match = False
                break
                
        # 채점 결과 예쁘게 화면 출력
        print(f"[{idx+1}/{total_cases}] 테스트 문장: '{original_text}'")
        print(f"  > STT 인식 결과 : '{recognized_text}' ({elapsed_time}s 소요)")
        if is_exact_match:
            print("  > 파싱 결과      : ✅ 완벽히 일치!")
            parsing_success_count += 1
        else:
            print("  > 파싱 결과      : ❌ 불일치!")
            print(f"    - 예상(Expected): {expected}")
            print(f"    - 실제(Actual)  : {actual_parsed}")
        print("-" * 50)
        
    # [Conclusion] 전체 집계
    accuracy = (parsing_success_count / total_cases) * 100
    print("\n" + "="*50)
    print(f"🏆 최종 STT 파이프라인 정확도(Accuracy): {accuracy:.1f}% ({parsing_success_count}/{total_cases})")
    print("="*50)
    print("💡 만약 불일치(❌)가 있다면:")
    print(" 1. STT가 글자를 잘못 인식했는지 확인 (예: '켜줘'를 '꺼줘'로 인식) -> 파인튜닝 부족")
    print(" 2. STT는 맞았는데 stt_parser.py 규칙이 부족한지 확인 -> Parser 정규식 수정 필요")
    return accuracy


def parse_args():
    """
    python stt_benchmark.py --compare
    터미널에서 스크립트를 실행할 때 뒤에 붙는 옵션/태그 명령어를 해석하는 유틸
    """
    parser = argparse.ArgumentParser(description="Benchmark smart-home STT models.")
    parser.add_argument(
        "--model",
        choices=MODEL_CHOICES.keys(),
        default="auto",
        help="Single model to benchmark. default: auto",
    )
    # --compare 옵션을 주면 베이스 모델과 파인튜닝을 두번 똑같이 돌려서 비교해줌
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run the same benchmark on both base and v2 models for direct comparison.",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # 옵션에 따른 분기 처리
    if args.compare:
        results = {}
        for model_choice in ("base", "v2"):
            print("\n" + "#" * 60)
            print(f"[비교 실행] model={model_choice}")
            print("#" * 60)
            results[model_choice] = run_benchmark(model_choice=model_choice)

        print("\n" + "=" * 60)
        print("📊 비교 요약 막대그래프")
        for model_choice, accuracy in results.items():
            print(f"- {model_choice}: {accuracy:.1f}%")
        print("=" * 60)
    else:
        run_benchmark(model_choice=args.model)
