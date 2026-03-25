import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# ==============================================================================
# [교육용 주석] 가짜(Mock) 센서 데이터 생성기
# ==============================================================================
# 목적: 실제 집의 사물인터넷(IoT) 센서 데이터가 클라우드로 수집되기 전 단계에서,
#       백엔드 시스템 또는 인공지능 모델(LSTM)을 미리 학습하고 테스트해볼 수 있도록
#       현실과 매우 유사한 패턴을 띄는(규칙적인) 가상 데이터를 대량으로 생성하는 스크립트입니다.
# ==============================================================================

def generate_mock_json_payload(filename=None, days=14):
    if filename is None:
        # __file__ 이란 이 파이썬 파일 자체의 물리적 경로를 의미합니다. 현재 스크립트 위치 기준으로 mock 파일 절대 경로를 잡습니다.
        filename = os.path.join(os.path.dirname(__file__), "mock_payload.json")
    
    print(f"Generating {days} days of mock sensor payload to {filename}...")
    
    # 현재 시간 기준으로 days 일(예: 14일) 전부터 시작해서 지금(end_time)까지의 시간 범위를 만듭니다.
    start_time = datetime.now() - timedelta(days=days)
    end_time = datetime.now()
    
    # Pandas의 date_range를 활용, freq='30min'를 통해 30분 단위 간격으로 타임라인 배열을 촘촘하게 찍습니다.
    timestamps = pd.date_range(start=start_time, end=end_time, freq='30min')
    num_records = len(timestamps)
    
    records = []
    
    # 각 시점(ts) 마다 환경 요소(온도/습도 등)와 기기 작동 여부를 조건문으로 시뮬레이션 합니다.
    for ts in timestamps:
        hour = ts.hour # 현재 시점의 '시간'
        is_weekend = ts.weekday() >= 5 # 요일 인덱스가 5,6 이면 주말 (0: 월요일, 6: 일요일)
        
        # ─────────────────────────────────────────
        # 1. 기본 환경 데이터 시뮬레이션 (삼각함수로 곡선 유도)
        # ─────────────────────────────────────────
        # 온도(Temperature): 하루 중 시간에 따라 사인 곡선(np.sin)을 그리며 오르내리게 만듭니다. + np.random.normal(정규분포)로 미세한 노이즈를 더해 현실감을 부여합니다.
        temp = 22.0 + np.sin(hour / 24.0 * 2 * np.pi - np.pi/2) * 5 + np.random.normal(0, 0.5)
        # 습도(Humidity): 코사인 곡선을 그리며 밤낮으로 변동되는 계절성/주기성을 모방합니다.
        hum = 45.0 + np.cos(hour / 24.0 * 2 * np.pi) * 10 + np.random.normal(0, 2)
        
        # 미세먼지(fine_dust): np.clip을 통해 0 미만(마이너스)이 되는 현상을 방지하면서 정규분포에 기반해 랜덤으로 뿌려줍니다.
        fine_dust = np.clip(np.random.normal(25, 10), 0, None) 
        
        # 간헐적 미세먼지 스파이크: 5% 확률(np.random.random() < 0.05)로 뜬금없이 미세먼지 수치가 급증
        # (이는 창문 열어둠, 요리 같은 일상적인 돌발 상황을 AI 모델에게 학습시키기 위한 인과적인 장치입니다.)
        if np.random.random() < 0.05:
            fine_dust += np.random.uniform(50, 100)
            
        # ─────────────────────────────────────────
        # 2. 기기 작동 로직 (생활 패턴 반영 -> 즉, 인공지능이 맞춰야 할 정답(Label) 생성)
        # ─────────────────────────────────────────
        # 처음에는 아무 제어가 없도록 모든 기기의 작동상태를 꺼짐(0)으로 셋팅합니다.
        air_on = 0
        hum_on = 0
        dehum_on = 0
        
        # [패턴 A: 퇴근 후 공기청정기] 평일(not 주말) 18시~20시 사이에 80% 확률로 켠다는 유저 페르소나
        if not is_weekend and 18 <= hour <= 20 and np.random.random() < 0.8:
            air_on = 1
            
        # [패턴 B: 수면 중 가습기] 매일 밤 23시~새벽 6시에 공기가 건조(습도 < 50)하면 90% 확률로 켠다는 방어적 루틴
        if (hour >= 23 or hour <= 6) and hum < 50.0 and np.random.random() < 0.9:
            hum_on = 1
            
        # [패턴 C: 주말 낮 제습기] 주말 오후 13시~15시, 공기가 무겁고 습하면(습도 > 50) 제습기를 높은 확률로 켠다는 패턴
        if is_weekend and 13 <= hour <= 15 and hum > 50.0 and np.random.random() < 0.85:
            dehum_on = 1
            
        # [환경적 의존성 긴급 룰] 단순히 시간에만 의존하지 않고, 수치가 너무 극단적으로 나쁘면 사용자가 즉각 반응(스위치 ON)하는 룰을 삽입합니다.
        if fine_dust > 80: air_on = 1
        if hum < 30: hum_on = 1
        if hum > 70: dehum_on = 1
            
        # 완성된 타임라인 한 줄(row)을 딕셔너리로 만들어 배열(records)에 넣습니다.
        records.append({
            "timestamp": ts.isoformat(),       # ISO 표준 문자열 ("2026-03-25T08:30:00") 포맷
            "room_id": 1,                      # 어떤 위치의 방인지 (예: 거실=1 등 Backend DB 제원에 맞춤)
            "temperature": round(temp, 1),     # 소수점 1자리까지 모형화 후 절삭
            "humidity": round(hum, 1),
            "fine_dust": round(fine_dust, 1),  
            "air_purifier_on": air_on,         # 0 또는 1이 들어감 (이 값들이 바로 AI에게 지도학습 시킬 정답 변수 Y 3종입니다)
            "humidifier_on": hum_on,
            "dehumidifier_on": dehum_on
        })
        
    # 마지막 JSON 통 포맷 구성 (Spring/Node 등 백엔드 API와 통신할 때 협의된 데이터 구조 시뮬레이션 형식)
    payload = {
        "user_id": 12345,      # 유저 아이디 (정수형)
        "sensor_data": records # 위에서 만들어둔 거대한 시계열 객체 리스트 전부가 이 value 영역에 들어가게 됨
    }
    
    import json
    # ensure_ascii=False 파라미터를 통해 나중에 혹시 모를 한글/유니코드 데이터가 깨지지 않고 저장되도록 합니다.
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2) # indent=2 옵션으로 JSON을 보기 좋게 들여쓰기해서 파일에 씁니다.
        
    print(f"✅ Generated {num_records} records to '{filename}'.")

if __name__ == "__main__":
    generate_mock_json_payload()
