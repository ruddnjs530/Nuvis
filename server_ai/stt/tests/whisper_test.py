import os

# GPU 번호 고정 세팅: 파이토치가 멋대로 서버의 모든 최상단 GPU를 점유하지 않고, 정확히 5번 그래픽카드만 편식하도록 강제 설정하는 국룰 옵션.
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "5"

import whisper
import json
import warnings
from stt_parser import parse_voice_command

# ==============================================================================
# [교육용 주석] 간단한 Whisper STT 찍먹 API 테스트용 스크립트
# ==============================================================================
# 실제 FastAPI 서버가 띄워지기 전에, 모델이 음성(마이크 녹음본)을 한국어 텍스트로 잘 바꾸고(STT 역할),
# 그 텍스트가 로봇이 이해하는 명령(JSON, 파싱 역할)으로 잘 이어지는지 연결을 확인하는 단일 실행 도구입니다.

# 시스템 특성상 뜨는 자잘한 파이토치 버전 경고 메시지 무시 (터미널 깔끔하게 유지 목적)
warnings.filterwarnings("ignore")

def setup_whisper_model(model_size="base"):
    """
    OpenAI Whisper 모델의 껍데기를 서버 메모리에 올립니다.
    model_size: 'tiny', 'base', 'small', 'medium', 'large' 등
    보통 스마트홈 컨트롤같이 짧은 단문에는 가볍고 반응성이 미친듯이 빠른 'base' 이나 'small'을 주로 사용합니다.
    """
    print(f"Loading Whisper model '{model_size}' on GPU (Visible device 5)...")
    # 처음 실행 시 인터넷 저장소에서 모델 가중치를 다운바다 ~/.cache 에 저장하며, 그 이후엔 캐시를 씁니다.
    model = whisper.load_model(model_size, device="cuda")
    print("✅ Model loaded successfully!")
    return model

def transcribe_audio(model, audio_file_path):
    """
    선탑재된 AI 뇌 모델과 실제 오디오 파일을 입력받아 '한국어 글씨'를 뱉어내는 핵심 추론기능입니다.
    """
    # 윈도우/리눅스에 해당 파일경로가 실제로 존재하는지부터 안전하게 검사
    if not os.path.exists(audio_file_path):
        print(f"❌ Error: Audio file '{audio_file_path}' not found.")
        return None
        
    print(f"Transcribing '{audio_file_path}'...")
    
    # [꿀팁] language="ko" 로 강제로 지정해주면, AI가 1~2초 동안 "이게 어느나라 언어지?" 고민(Language Detect)하는 과정을 생략해서
    # 첫 응답(First Bite) 속도를 훨씬 빠르게 최적화 할 수 있습니다. 스마트홈은 무조건 한국어 환경이니까요.
    result = model.transcribe(audio_file_path, language="ko")
    
    # 긴 딕셔너리에서 순수한 텍스트 문자열만 앞뒤 공백 날리고(strip) 가져옵니다.
    recognized_text = result["text"].strip()
    return recognized_text

if __name__ == "__main__":
    print("=== 스마트 홈 로봇 음성 인식(STT) 파이프라인 ===")
    
    # 1. 모델 로드 
    stt_model = setup_whisper_model("base")
    
    # 2. 테스트용 오디오 파일 지정 
    # (개발자가 직접 윈도우 녹음기/스마트폰으로 '거실 공기청정기 켜줘' 녹음해서 test_command.wav 로 던지면 됨)
    sample_audio_file = "test_command.wav"
    
    # 더미 파일 생성 유도 안내
    if not os.path.exists(sample_audio_file):
        print(f"\n[안내] 테스트를 진행하려면 '{sample_audio_file}' 파일이 필요합니다.")
        print("스마트폰이나 윈도우 녹음기로 '거실로 가서 공기청정기 켜줘'라고 녹음한 뒤")
        print(f"이 폴더({os.path.abspath('.')})에 '{sample_audio_file}' 이름으로 저장해주세요.")
    else:
        # 3. AI 연산 진행 (파형 음성 -> 한국어 텍스트)
        text_result = transcribe_audio(stt_model, sample_audio_file)
        
        if text_result:
            print("\n🎙️ 인식된 텍스트:")
            print(f"> \"{text_result}\"")
            
            # 4. 자연어 파싱 엔진 (한국어 텍스트 -> 기계가 아는 JSON 제원표 규격) 연동 테스트
            # 우리가 별도로 룰베이스 기반으로 짜둔 stt_parser 모듈에 던져서 의미를 발라냅니다.
            print("\n🤖 로봇 명령 변환 결과:")
            parsed_json = parse_voice_command(text_result)
            print(parsed_json)
