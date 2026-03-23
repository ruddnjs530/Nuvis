import os
import json
import time
import argparse
from pathlib import Path

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

# 경고 무시
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).parent
MODEL_V2 = BASE_DIR / "model" / "v2_full"
MODEL_V1 = BASE_DIR / "model" / "whisper-smarthome"
BASE_MODEL = "openai/whisper-small"

MODEL_CHOICES = {
    "auto": "auto",
    "base": BASE_MODEL,
    "v1": str(MODEL_V1),
    "v2": str(MODEL_V2),
}

# 1. 평가할 테스트 데이터셋 정의
# 형식: {"text": "발화 문장", "expected": { "action": "", "roomId": "", "module": "", "state": "" }}
TEST_CASES = [
    {
        "text": "거실로 가서 공기청정기 켜줘",
        "expected": {"action": "move_and_operate", "roomId": 1, "module": "air_purifier", "state": "on"}
    },
    {
        "text": "안방 가습기 좀 꺼줄래",
        "expected": {"action": "move_and_operate", "roomId": 3, "module": "humidifier", "state": "off"}
    },
    {
        "text": "그냥 주방으로 이동해",
        "expected": {"action": "move", "roomId": 2, "module": None, "state": None}
    },
    {
        "text": "제습기 작동",
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
    # 예외 상황 및 복합명령 테스트
    {
        "text": "거실 말고 안방 가습기 편하게 켜줄래",
        "expected": {"action": "move_and_operate", "roomId": 3, "module": "humidifier", "state": "on"}
    },
    {
        "text": "주방 공기청정기 켜지마",
        "expected": {"action": "move_and_operate", "roomId": 2, "module": "air_purifier", "state": "off"}
    },
    # 예외 상황 테스트 (등록되지 않은 기기)
    {
        "text": "보일러 켜",
        "expected": {"action": "none", "roomId": None, "module": None, "state": None} 
    }
]

AUDIO_DIR = "test_audio"

def generate_test_audios():
    """
    gTTS를 사용해 테스트용 음성(.mp3) 파일을 자동 생성합니다.
    """
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
        
    print(f"[{AUDIO_DIR}] 디렉토리에 테스트용 오디오 파일을 생성합니다...")
    
    for idx, case in enumerate(TEST_CASES):
        filename = os.path.join(AUDIO_DIR, f"test_{idx:02d}.mp3")
        case["audio_path"] = filename
        
        # 파일이 이미 존재하면 생성 건너뜀 (시간 단축)
        if not os.path.exists(filename):
            tts = gTTS(text=case["text"], lang='ko')
            tts.save(filename)
            print(f"  - 생성 완료: {filename} ('{case['text']}')")
    
    print("✅ 오디오 생성 완료!\n")

def resolve_model_path(model_choice: str = "auto") -> tuple[str, str]:
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

    if MODEL_V2.exists():
        print(f"🔥 Loading Fine-tuned Model V2: {MODEL_V2}")
        return str(MODEL_V2), "v2"

    if MODEL_V1.exists():
        print(f"🔥 Loading Fine-tuned Model V1: {MODEL_V1}")
        return str(MODEL_V1), "v1"

    print(f"📡 Loading Base Model: {BASE_MODEL}")
    return BASE_MODEL, "base"


def load_stt_model(model_choice: str = "auto"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("⚠️ GPU를 찾을 수 없어 CPU 환경에서 실행합니다. 속도가 느릴 수 있습니다.")
    else:
        print(f"✅ GPU 환경 감지됨. (장치: {device})")

    model_path, resolved_choice = resolve_model_path(model_choice)
    processor = WhisperProcessor.from_pretrained(model_path)
    model = WhisperForConditionalGeneration.from_pretrained(model_path).to(device)
    model.generation_config.language = "korean"
    model.generation_config.task = "transcribe"
    model.generation_config.forced_decoder_ids = None

    print("✅ Model loaded!\n")
    return processor, model, device, resolved_choice


def transcribe_audio(processor, model, device: str, audio_path: str) -> str:
    audio_input, _ = librosa.load(audio_path, sr=16000)
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

    with torch.inference_mode():
        predicted_ids = model.generate(
            input_features=input_features,
            attention_mask=attention_mask,
        )
    return processor.batch_decode(predicted_ids, skip_special_tokens=True)[0].strip()


def run_benchmark(model_choice: str = "auto") -> float:
    """
    Whisper 모델로 텍스트를 인식하고, 파서로 파싱한 뒤 정확도(Accuracy)를 측정합니다.
    """
    # 1. 오디오 파일 생성/확인
    generate_test_audios()
    
    # 2. 모델 로드
    processor, model, device, resolved_choice = load_stt_model(model_choice)
    
    print(f"=== 정확도 테스트 시작 ({resolved_choice}) ===")
    total_cases = len(TEST_CASES)
    parsing_success_count = 0
    
    for idx, case in enumerate(TEST_CASES):
        audio_path = case["audio_path"]
        expected = case["expected"]
        original_text = case["text"]
        
        start_time = time.time()
        
        # [Step 1] Whisper 추론
        recognized_text = transcribe_audio(processor, model, device, audio_path)
        
        # [Step 2] 로봇 명령어 파싱
        parsed_str = parse_voice_command(recognized_text)
        parsed_json = json.loads(parsed_str)
        
        elapsed_time = round(time.time() - start_time, 2)
        
        # [Step 3] 검증 로직
        # 1) 텍스트 전사(STT)가 의도된 핵심 키워드를 포함했는가? (간단 검증)
        # 2) 파싱된 JSON이 기대한 JSON과 일치하는가?
        
        # 파싱 오류가 있는 경우({"error": ...})를 포함하므로, 'error' 키가 있으면 기본 구조 포맷팅
        if "error" in parsed_json:
             actual_parsed = {"action": "none", "roomId": None, "module": None, "state": None}
        else:
             actual_parsed = {
                 "action": parsed_json.get("action"),
                 "roomId": parsed_json.get("roomId"),
                 "module": parsed_json.get("module"),
                 "state": parsed_json.get("state")
             }
        
        # 예상 키와 실제 키 전부 검사
        is_exact_match = True
        for key, expected_val in expected.items():
            if actual_parsed[key] != expected_val:
                is_exact_match = False
                break
                
        # 출력
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
        
    # [Conclusion]
    accuracy = (parsing_success_count / total_cases) * 100
    print("\n" + "="*50)
    print(f"🏆 최종 STT 파이프라인 정확도(Accuracy): {accuracy:.1f}% ({parsing_success_count}/{total_cases})")
    print("="*50)
    print("💡 만약 불일치(❌)가 있다면:")
    print(" 1. STT가 글자를 잘못 인식했는지 확인 (예: '켜줘'를 '꺼줘'로 인식)")
    print(" 2. STT는 맞았는데 stt_parser.py 규칙이 부족한지 확인 (새로운 예외 처리 필요)")
    return accuracy


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark smart-home STT models.")
    parser.add_argument(
        "--model",
        choices=MODEL_CHOICES.keys(),
        default="auto",
        help="Single model to benchmark. default: auto",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run the same benchmark on both base and v2 models for direct comparison.",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if args.compare:
        results = {}
        for model_choice in ("base", "v2"):
            print("\n" + "#" * 60)
            print(f"[비교 실행] model={model_choice}")
            print("#" * 60)
            results[model_choice] = run_benchmark(model_choice=model_choice)

        print("\n" + "=" * 60)
        print("📊 비교 요약")
        for model_choice, accuracy in results.items():
            print(f"- {model_choice}: {accuracy:.1f}%")
        print("=" * 60)
    else:
        run_benchmark(model_choice=args.model)
