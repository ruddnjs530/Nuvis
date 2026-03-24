import requests
import json
import time
from pathlib import Path

# GPU 서버의 IP 주소와 포트를 입력하세요. (현재는 로컬호스트로 설정)
# 실제 테스트 시에는 '127.0.0.1' 대신 '192.168.x.x' 등 GPU 서버의 IP로 변경해야 합니다.
SERVER_IP = "127.0.0.1" 
REC_SERVER_PORT = "9000"
STT_SERVER_PORT = "9001"

import os

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


def resolve_stt_test_audio() -> tuple[str | None, str | None]:
    candidates = [
        PROJECT_DIR / "stt" / "tests" / "test_audio" / "test_00.mp3",
        PROJECT_DIR / "test_audio" / "test_00.mp3",
        PROJECT_DIR / "test_command.wav",
    ]

    mime_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    }

    for path in candidates:
        if path.exists():
            return str(path), mime_types.get(path.suffix.lower(), "application/octet-stream")

    return None, None

def test_recommendation_api():
    """
    추천 시스템(recommendation/api/main.py) 동작 확인:
    생성된 mock_payload.json을 읽어서 POST 요청을 보냅니다.
    """
    mock_file = PROJECT_DIR / "recommendation" / "data" / "mock_payload.json"
    if not mock_file.exists():
        print(f"❌ '{mock_file}' 파일이 없습니다. 먼저 generate_mock_data.py를 실행하세요.")
        return
        
    with open(mock_file, 'r', encoding='utf-8') as f:
        payload = json.load(f)

    # 1. 이벤트 추천 테스트
    event_url = f"http://{SERVER_IP}:{REC_SERVER_PORT}/api/event/ai-suggestions"
    print(f"\n📡 [추천 시스템] 이벤트 기반 센서 임계값 추천 요청... ({event_url})")
    
    try:
        start_time = time.time()
        response = requests.post(event_url, json=payload, timeout=10)
        response.raise_for_status() 
        print(f"✅ 서버 응답 완료! ({round(time.time() - start_time, 2)}초 소요)")
        
        result = response.json()
        print("=== 🤖 1. AI 임계값 분석 결과 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ 이벤트 추천 통신 실패: {e}")

    # 2. 스케줄 추천 테스트
    schedule_url = f"http://{SERVER_IP}:{REC_SERVER_PORT}/api/schedule/ai-suggestions"
    print(f"\n📡 [추천 시스템] 생활 패턴 기반 스케줄 추천 요청... ({schedule_url})")
    
    try:
        start_time = time.time()
        response = requests.post(schedule_url, json=payload, timeout=10)
        response.raise_for_status() 
        print(f"✅ 서버 응답 완료! ({round(time.time() - start_time, 2)}초 소요)")
        
        result = response.json()
        print("=== 🤖 2. AI 스케줄 분석 결과 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ 스케줄 추천 통신 실패: {e}")

def test_stt_api():
    """
    음성 인식(stt/main.py)의 동작 상태를 확인하는 테스트 함수
    녹음된 음성 파일을 POST 방식으로 GPU 서버에 전송합니다.
    """
    url = f"http://{SERVER_IP}:{STT_SERVER_PORT}/api/stt/transcribe"
    audio_file_path, mime_type = resolve_stt_test_audio()

    if not audio_file_path:
        print("\n❌ STT 테스트용 오디오 파일을 찾지 못했습니다.")
        print("-> 우선순위: stt/tests/test_audio/test_00.mp3 -> test_audio/test_00.mp3 -> test_command.wav")
        print("-> 팁: GPU 서버에서 `python stt/tests/stt_benchmark.py --model v2`를 한 번 실행하면 테스트 음성이 생성됩니다.")
        return
    
    print(f"\n📡 [STT 시스템] GPU 서버로 음성 텍스트 변환 및 파싱 명령 요청 중... ({url})")
    print(f"   - 사용 파일: {audio_file_path}")
    start_time = time.time()
    
    try:
        # 파일을 multipart/form-data 형식으로 전송
        with open(audio_file_path, "rb") as f:
            files = {"audio": (os.path.basename(audio_file_path), f, mime_type)}
            # Whisper 모델 크기에 따라 시간이 걸릴 수 있어 timeout을 넉넉히 줍니다.
            response = requests.post(url, files=files, timeout=10)
        
        response.raise_for_status() 
        elapsed_time = round(time.time() - start_time, 2)
        print(f"✅ 서버 응답 완료! ({elapsed_time}초 소요)\n")
        
        result = response.json()
        print("=== 🎤 음성 명령 인식 및 파싱 결과 ===")
        print(json.dumps(result, indent=4, ensure_ascii=False))
        
        if result.get("status") == "success":
            text = result.get("recognized_text", "")
            cmd = result.get("robot_command", {})
            print(f"\n[클라이언트 동작 예시] 로봇에게 음성 인식 결과가 도착했습니다!")
            print(f"  - 원본 명령어: '{text}'")
            print(f"  - roomId={cmd.get('roomId')} 위치로 이동하여 {cmd.get('module')} 기기를 {cmd.get('state')} 상태로 만들겠습니다.")
                
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 연결 실패: '{SERVER_IP}:{STT_SERVER_PORT}' 서버에 접속할 수 없습니다.")
        print("-> 팁: GPU 서버에서 stt/api/main.py (uvicorn)가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"\n❌ STT 테스트 중 에러 발생: {e}")

if __name__ == "__main__":
    print("===========================================")
    print("클라이언트 -> GPU AI 서버 통신 테스트 시작")
    print("===========================================")
    
    test_recommendation_api()
    print("-" * 40)
    test_stt_api()
    
    print("===========================================")
