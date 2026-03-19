import os
import json
import time

try:
    from gtts import gTTS
except ImportError:
    print("❌ 'gTTS' 라이브러리가 설치되어 있지 않습니다.")
    print("명령프롬프트에서 다음을 실행해주세요: pip install gTTS")
    exit(1)

import whisper
from stt_parser import parse_voice_command

# 경고 무시
import warnings
warnings.filterwarnings("ignore")

# 1. 평가할 테스트 데이터셋 정의
# 형식: {"text": "발화 문장", "expected": { "action": "", "target_room": "", "module": "", "state": "" }}
TEST_CASES = [
    {
        "text": "거실로 가서 공기청정기 켜줘",
        "expected": {"action": "move_and_operate", "target_room": "living_room", "module": "air_purifier", "state": "on"}
    },
    {
        "text": "안방 가습기 좀 꺼줄래",
        "expected": {"action": "move_and_operate", "target_room": "bedroom", "module": "humidifier", "state": "off"}
    },
    {
        "text": "그냥 주방으로 이동해",
        "expected": {"action": "move", "target_room": "kitchen", "module": None, "state": None}
    },
    {
        "text": "제습기 작동",
        "expected": {"action": "operate_module", "target_room": None, "module": "dehumidifier", "state": "on"}
    },
    {
        "text": "침실 공기청정기 멈춰",
        "expected": {"action": "move_and_operate", "target_room": "bedroom", "module": "air_purifier", "state": "off"}
    },
    {
        "text": "내방으로 와",
        "expected": {"action": "move", "target_room": "my_room", "module": None, "state": None}
    },
    # 예외 상황 테스트 (등록되지 않은 기기)
    {
        "text": "보일러 켜",
        "expected": {"action": "none", "target_room": None, "module": None, "state": None} 
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

def run_benchmark(model_size="base"):
    """
    Whisper 모델로 텍스트를 인식하고, 파서로 파싱한 뒤 정확도(Accuracy)를 측정합니다.
    """
    # 1. 오디오 파일 생성/확인
    generate_test_audios()
    
    # 2. 모델 로드
    print(f"Loading Whisper model '{model_size}'...")
    # 테스트 스크립트 특성상 GPU가 사용 가능하다면 GPU, 아니면 CPU를 쓰게끔 유연하게 처리
    device = "cuda" if whisper.torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("⚠️ GPU를 찾을 수 없어 CPU 환경에서 실행합니다. 속도가 느릴 수 있습니다.")
    else:
        print(f"✅ GPU 환견 감지됨. (장치: {device})")
        
    model = whisper.load_model(model_size, device=device)
    print("✅ Model loaded!\n")
    
    print("=== 정확도 테스트 시작 ===")
    total_cases = len(TEST_CASES)
    success_count = 0
    parsing_success_count = 0
    
    for idx, case in enumerate(TEST_CASES):
        audio_path = case["audio_path"]
        expected = case["expected"]
        original_text = case["text"]
        
        start_time = time.time()
        
        # [Step 1] Whisper 추론
        result = model.transcribe(audio_path, language="ko")
        recognized_text = result["text"].strip()
        
        # [Step 2] 로봇 명령어 파싱
        parsed_str = parse_voice_command(recognized_text)
        parsed_json = json.loads(parsed_str)
        
        elapsed_time = round(time.time() - start_time, 2)
        
        # [Step 3] 검증 로직
        # 1) 텍스트 전사(STT)가 의도된 핵심 키워드를 포함했는가? (간단 검증)
        # 2) 파싱된 JSON이 기대한 JSON과 일치하는가?
        
        # 파싱 오류가 있는 경우({"error": ...})를 포함하므로, 'error' 키가 있으면 기본 구조 포맷팅
        if "error" in parsed_json:
             actual_parsed = {"action": "none", "target_room": None, "module": None, "state": None}
        else:
             actual_parsed = {
                 "action": parsed_json.get("action"),
                 "target_room": parsed_json.get("target_room"),
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

if __name__ == "__main__":
    run_benchmark(model_size="base")
