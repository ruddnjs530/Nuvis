import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_json_payload(filename="mock_payload.json", days=14):
    print(f"Generating {days} days of mock sensor payload...")
    
    start_time = datetime.now() - timedelta(days=days)
    end_time = datetime.now()
    
    # 30분 단위 시계열 데이터
    timestamps = pd.date_range(start=start_time, end=end_time, freq='30min')
    num_records = len(timestamps)
    
    records = []
    
    for ts in timestamps:
        hour = ts.hour
        is_weekend = ts.weekday() >= 5
        
        # 1. 기본 환경 데이터 시뮬레이션
        temp = 22.0 + np.sin(hour / 24.0 * 2 * np.pi - np.pi/2) * 5 + np.random.normal(0, 0.5)
        hum = 45.0 + np.cos(hour / 24.0 * 2 * np.pi) * 10 + np.random.normal(0, 2)
        pm25 = np.clip(np.random.normal(25, 10), 0, None)
        
        # 간헐적 미세먼지 스파이크
        if np.random.random() < 0.05:
            pm25 += np.random.uniform(50, 100)
            
        # 2. 기기 작동 로직 (생활 패턴 반영)
        air_on = 0
        hum_on = 0
        dehum_on = 0
        
        # [패턴 A: 퇴근 후 공기청정기] 평일 18시~20시 사이에 공기 청정기를 자주 켬
        if not is_weekend and 18 <= hour <= 20 and np.random.random() < 0.8:
            air_on = 1
            
        # [패턴 B: 수면 중 가습기] 매일 23시~06시 건조하면(습도<50) 가습기 켬
        if (hour >= 23 or hour <= 6) and hum < 50.0 and np.random.random() < 0.9:
            hum_on = 1
            
        # [패턴 C: 주말 대청소 제습기] 주말 오후 13시~15시, 습도 높으면 제습기 켬
        if is_weekend and 13 <= hour <= 15 and hum > 50.0 and np.random.random() < 0.85:
            dehum_on = 1
            
        # 환경적 의존성 (단순 스파이크 대비)
        if pm25 > 80: air_on = 1
        if hum < 30: hum_on = 1
        if hum > 70: dehum_on = 1
            
        records.append({
            "timestamp": ts.isoformat(),
            "temperature": round(temp, 1),
            "humidity": round(hum, 1),
            "pm25": round(pm25, 1),
            "air_purifier_on": air_on,
            "humidifier_on": hum_on,
            "dehumidifier_on": dehum_on
        })
        
    # JSON 파일 저장 (API 통신용 포맷 시뮬레이션)
    payload = {
        "user_id": "user_12345",
        "sensor_data": records
    }
    
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Generated {num_records} records to '{filename}'.")

if __name__ == "__main__":
    generate_mock_json_payload()
