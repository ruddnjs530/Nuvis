import os
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "5"

import whisper
import json
import warnings
from stt_parser import parse_voice_command

# 경고 메시지 무시 (FP16 경고 등)
warnings.filterwarnings("ignore")

def setup_whisper_model(model_size="base"):
    """
    OpenAI Whisper 모델을 로드합니다.
    model_size: 'tiny', 'base', 'small', 'medium', 'large'
    """
    print(f"Loading Whisper model '{model_size}' on GPU (Visible device 5)...")
    # 처음 실행 시 모델을 자동으로 다운로드 받습니다. (~100MB for base)
    model = whisper.load_model(model_size, device="cuda")
    print("✅ Model loaded successfully!")
    return model

def transcribe_audio(model, audio_file_path):
    """
    오디오 파일을 읽어서 한국어 텍스트로 변환(STT)합니다.
    """
    if not os.path.exists(audio_file_path):
        print(f"❌ Error: Audio file '{audio_file_path}' not found.")
        return None
        
    print(f"Transcribing '{audio_file_path}'...")
    
    # language="ko" 로 강제 지정하면 한국어 인식률이 올라가고 속도가 빠름
    result = model.transcribe(audio_file_path, language="ko")
    
    recognized_text = result["text"].strip()
    return recognized_text

if __name__ == "__main__":
    print("=== 스마트 홈 로봇 음성 인식(STT) 파이프라인 ===")
    
    # 1. 모델 로드 (가벼운 base 모델 사용)
    stt_model = setup_whisper_model("base")
    
    # 2. 테스트용 오디오 파일 경로 (직접 녹음한 wav 파일을 여기에 넣으세요)
    # 예: "test_command.wav"
    sample_audio_file = "test_command.wav"
    
    # 더미 파일 생성 안내
    if not os.path.exists(sample_audio_file):
        print(f"\n[안내] 테스트를 진행하려면 '{sample_audio_file}' 파일이 필요합니다.")
        print("스마트폰이나 윈도우 녹음기로 '거실로 가서 공기청정기 켜줘'라고 녹음한 뒤")
        print(f"이 폴더({os.path.abspath('.')})에 '{sample_audio_file}' 이름으로 저장해주세요.")
    else:
        # 3. STT 변환
        text_result = transcribe_audio(stt_model, sample_audio_file)
        
        if text_result:
            print("\n🎙️ 인식된 텍스트:")
            print(f"> \"{text_result}\"")
            
            # 4. 자연어 파싱 (stt_parser 연동)
            print("\n🤖 로봇 명령 변환 결과:")
            parsed_json = parse_voice_command(text_result)
            print(parsed_json)
