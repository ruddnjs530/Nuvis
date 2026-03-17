import requests
import json
import time

# GPU 서버의 IP 주소와 포트를 입력하세요. (현재는 로컬호스트로 설정)
# 실제 테스트 시에는 '127.0.0.1' 대신 '192.168.x.x' 등 GPU 서버의 IP로 변경해야 합니다.
SERVER_IP = "127.0.0.1" 
REC_SERVER_PORT = "8000"
STT_SERVER_PORT = "8001"

import os

def test_recommendation_api():
    """
    추천 시스템(recommendation/main.py)의 동작 상태를 확인하는 테스트 함수
    메인 서버나 로봇 내부에서 이런 형태로 GPU 서버에 데이터를 요청합니다.
    """
    url = f"http://{SERVER_IP}:{REC_SERVER_PORT}/api/event/ai-suggestions"
    
    print(f"📡 [추천 시스템] GPU 서버로 데이터 요청 중... ({url})")
    start_time = time.time()
    
    try:
        # GPU 서버로 최대 5초간 응답 대기 (timeout)
        response = requests.get(url, timeout=5)
        
        # HTTP 응답 코드가 200번대(성공)인지 확인
        response.raise_for_status() 
        
        # 응답 시간을 계산
        elapsed_time = round(time.time() - start_time, 2)
        print(f"✅ 서버 응답 완료! ({elapsed_time}초 소요)\n")
        
        # JSON 결과 파싱
        result = response.json()
        print("=== 🤖 AI 분석 결과 ===")
        print(json.dumps(result, indent=4, ensure_ascii=False))
        
        # 실제 시연 코드 작성 팁: 파싱된 데이터 활용법
        if result.get("status") == "success":
            data = result.get("data", {})
            threshold = data.get("pm25_alert_threshold")
            print(f"\n[클라이언트 동작 예시] 받은 임계값 {threshold}을 메인 로직 변수에 업데이트했습니다.")
        else:
            print("\n⚠️ AI 서버 측에서 분석 도중 오류가 발생한 것 같습니다.")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 연결 실패: '{SERVER_IP}:{REC_SERVER_PORT}' 서버에 접속할 수 없습니다.")
        print("-> 팁: GPU 서버에서 recommendation/main.py (uvicorn)가 실행 중인지 확인하세요.")
    except requests.exceptions.Timeout:
        print("\n❌ 타임아웃: 서버 응답이 너무 오래 걸립니다.")
    except Exception as e:
        print(f"\n❌ 알 수 없는 에러 발생: {e}")

def test_stt_api():
    """
    음성 인식(stt/main.py)의 동작 상태를 확인하는 테스트 함수
    녹음된 음성 파일을 POST 방식으로 GPU 서버에 전송합니다.
    """
    url = f"http://{SERVER_IP}:{STT_SERVER_PORT}/api/stt/transcribe"
    dummy_audio_file = "test_command.wav"
    
    # 더미 파일 생성 (테스트용)
    if not os.path.exists(dummy_audio_file):
        with open(dummy_audio_file, "w") as f:
            f.write("dummy audio content")
    
    print(f"\n📡 [STT 시스템] GPU 서버로 음성 텍스트 변환 및 파싱 명령 요청 중... ({url})")
    start_time = time.time()
    
    try:
        # 파일을 multipart/form-data 형식으로 전송
        with open(dummy_audio_file, "rb") as f:
            files = {"audio": (dummy_audio_file, f, "audio/wav")}
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
            print(f"  - {cmd.get('target_room')} 쪽으로 이동하여 {cmd.get('module')} 기기를 {cmd.get('state')} 상태로 만들겠습니다.")
                
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 연결 실패: '{SERVER_IP}:{STT_SERVER_PORT}' 서버에 접속할 수 없습니다.")
        print("-> 팁: GPU 서버에서 stt/main.py (uvicorn)가 실행 중인지 확인하세요.")
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
