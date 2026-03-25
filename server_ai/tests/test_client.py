import requests
import json
import time
from pathlib import Path

# ==============================================================================
# [교육용 주석] 통합 종단간 테스트 클라이언트 (Integration / E2E Test Client)
# ==============================================================================
# 역할: 클라이언트(프론트엔드/메인 백엔드) 입장에 빙의해서, 방금 전 띄워놓은 거대한 
#       추천 서버(9000), STT 음성인식 서버(9001) API들이 제대로 살아있는지, 포트 통신이 되는지,
#       에러 없이 올바른 JSON 규격을 잘 응답해주는지 한 번에 검증하는 시뮬레이터 봇입니다.
# ==============================================================================

# GPU 서버의 IP 주소와 포트 세팅. 
# (로컬에서 띄웠으면 127.0.0.1 이고, 원격지 서버 모의통신이면 192.x.x.x 로 변경해야 합니다.)
SERVER_IP = "127.0.0.1" 
REC_SERVER_PORT = "9000"
STT_SERVER_PORT = "9001"

import os

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


def resolve_stt_test_audio() -> tuple[str | None, str | None]:
    """
    STT API에 던져볼 더미 음성(WAV/MP3) 샘플 테스트 파일이 도대체 폴더 어딘가에 숨어있는지 
    세 군데의 후보지를 뒤져서 찾아오는 똑똑한 유틸 함수.
    """
    candidates = [
        PROJECT_DIR / "stt" / "tests" / "test_audio" / "test_00.mp3",
        PROJECT_DIR / "test_audio" / "test_00.mp3",
        PROJECT_DIR / "test_command.wav",
    ]

    mime_types = {
        ".mp3": "audio/mpeg", # 웹 통신상에서 MP3를 규정하는 MIME Type 포맷
        ".wav": "audio/wav",
    }

    for path in candidates:
        if path.exists():
            # 파일이 하나라도 존재하면 그 절대경로와 해당하는 MIME 타입을 반환하고 바로 탈출(최적화)
            return str(path), mime_types.get(path.suffix.lower(), "application/octet-stream")

    return None, None

def test_recommendation_api():
    """
    [추천 시스템 API 검증]
    미리 만들어둔 mock_payload.json(가짜 2주치 데이터) 파일 덩어리를 파이썬으로 읽어서 HTTP POST 통신을 보낸 후 
    FastAPI 서버가 머신러닝 임계값을 잘 추천해주는지 모의 테스트합니다.
    """
    mock_file = PROJECT_DIR / "recommendation" / "data" / "mock_payload.json"
    if not mock_file.exists():
        print(f"❌ '{mock_file}' 파일이 없습니다. 먼저 generate_mock_data.py를 실행하세요.")
        return
        
    # JSON 텍스트 파일을 통째로 읽어들임
    with open(mock_file, 'r', encoding='utf-8') as f:
        payload = json.load(f)

    # 1. 이벤트 추천 테스트 (특정 환경 수치를 찍었을 때 자동화)
    event_url = f"http://{SERVER_IP}:{REC_SERVER_PORT}/api/event/ai-suggestions"
    print(f"\n📡 [추천 시스템] 이벤트 기반 센서 임계값 추천 요청... ({event_url})")
    
    try:
        start_time = time.time()
        # 파이썬 requests 모듈로 아주 쉽게 HTTP POST 발송. 서버 지연대비 타임아웃 10초 설정으로 무한 멈춤 현상(Hang) 방지.
        response = requests.post(event_url, json=payload, timeout=10)
        response.raise_for_status()  # 200번대 OK 응답 외에 400~500이 뜨면 즉각 에러 뱉게 만듦
        print(f"✅ 서버 응답 완료! ({round(time.time() - start_time, 2)}초 소요)")
        
        # 서버 응답 데이터(JSON) 언패킹
        result = response.json()
        print("=== 🤖 1. AI 임계값 분석 결과 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ 이벤트 추천 통신 실패: {e}")

    # 2. 스케줄 추천 테스트 (주기적으로 항상 일어나는 시간 패턴 도출)
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
    [음성 인식 STT API 검증]
    녹음된 음성 파일을 HTTP POST 방식의 Multi-part Form 데이터 전송 체계로 GPU 서버에 업로드 파이프라인으로 태우고 
    어떤 텍스트와 파싱 명령어로 회신되는지 확인합니다.
    """
    url = f"http://{SERVER_IP}:{STT_SERVER_PORT}/api/stt/transcribe"
    audio_file_path, mime_type = resolve_stt_test_audio()

    if not audio_file_path:
        print("\n❌ STT 테스트용 오디오 파일을 찾지 못했습니다.")
        print("-> 우선순위: stt/tests/test_audio/test_00.mp3 -> test_audio/test_00.mp3 -> test_command.wav")
        print("-> 팁: GPU 서버에서 stt_benchmark.py --model v2 를 한 번 실행하면 테스트 음성이 자동으로 생성됩니다.")
        return
    
    print(f"\n📡 [STT 시스템] GPU 서버로 음성 텍스트 변환 및 파싱 명령 요청 중... ({url})")
    print(f"   - 사용 파일: {audio_file_path}")
    start_time = time.time()
    
    try:
        # 파일을 multipart/form-data 스트림 형식으로 로드하여 전송
        with open(audio_file_path, "rb") as f:
            files = {"audio": (os.path.basename(audio_file_path), f, mime_type)}
            # STT는 음성 길이가 길면 인공지능 추론이 수초 이상이 걸리므로 timeout을 10초로 넉넉히 줍니다.
            response = requests.post(url, files=files, timeout=10)
        
        response.raise_for_status() 
        elapsed_time = round(time.time() - start_time, 2)
        print(f"✅ 서버 응답 완료! ({elapsed_time}초 소요)\n")
        
        result = response.json()
        print("=== 🎤 음성 명령 인식 및 파싱 결과 ===")
        print(json.dumps(result, indent=4, ensure_ascii=False)) # API가 보낸 최종 통합 응답 덩어리 출력
        
        # 만약 STT 서버가 성공 코드를 줬을 경우, 클라이언트 프론트엔드/백엔드에서 변수를 꺼내 어떻게 처리점(뷰)을 잡을 수 있는지 시나리오 예시
        if result.get("status") == "success":
            text = result.get("recognized_text", "")
            cmd = result.get("robot_command", {})
            print(f"\n[클라이언트 단 애플리케이션 동작 제어 예시] 로봇에게 음성 인식 파싱 결과가 도착했습니다!")
            print(f"  - 원본 명령어: '{text}'")
            print(f"  - roomId={cmd.get('roomId')} 위치로 바퀴를 이동하여 {cmd.get('module')} 기기를 {cmd.get('state')} 상태로 만들겠습니다.")
                
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 연결 실패: '{SERVER_IP}:{STT_SERVER_PORT}' 서버에 접속할 수 없습니다.")
        print("-> 팁: GPU 서버에서 stt/api/main.py (uvicorn)가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"\n❌ STT 테스트 중 통합 에러 발생: {e}")

if __name__ == "__main__":
    print("===========================================")
    print("클라이언트 -> GPU AI 서버 네트워크 분산 통신 통합(E2E) 테스트 시작")
    print("===========================================")
    
    # 1. 추천 API 통신 시험
    test_recommendation_api()
    print("-" * 40)
    
    # 2. STT API 통신 시험
    test_stt_api()
    
    print("===========================================")
