import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_data(filename="mock_sensor_data.csv", days=14):
    print(f"Generating {days} days of mock sensor data...")
    
    start_time = datetime.now() - timedelta(days=days)
    end_time = datetime.now()
    
    # 10분 단위의 시계열 데이터 생성
    timestamps = pd.date_range(start=start_time, end=end_time, freq='10min')
    num_records = len(timestamps)
    
    # 기본 환경 데이터 생성 (온도, 습도)
    # 온도: 20도 ~ 30도 사이 변동
    temperature = 25.0 + np.sin(np.linspace(0, 14 * np.pi, num_records)) * 5 + np.random.normal(0, 0.5, num_records)
    
    # 습도: 40% ~ 70% 사이 변동
    humidity = 55.0 + np.cos(np.linspace(0, 14 * np.pi, num_records)) * 15 + np.random.normal(0, 2, num_records)
    
    # 미세먼지 (PM2.5): 기본 10~30, 가끔씩 외부 요인으로 80 이상 치솟음
    pm25 = np.clip(np.random.normal(20, 10, num_records), 0, None)
    
    # 임의의 시점에 미세먼지 스파이크 추가 (요리, 환기 등)
    spike_indices = np.random.choice(num_records, size=int(num_records * 0.05), replace=False)
    pm25[spike_indices] += np.random.uniform(50, 120, size=len(spike_indices))
    
    # 유저 행동 패턴 시뮬레이션:
    # 1. 환경 기반 패턴: 미세먼지가 75 이상일 때 수동으로 켜는 경향 (기존)
    air_purifier_manual_on = np.where(pm25 + np.random.normal(0, 10, num_records) > 75, 1, 0)
    
    # 2. 스케줄 기반 패턴: 미세먼지와 무관하게, 매일 저녁 18:00 ~ 19:30 사이에 기기를 켜는 습관 추가
    for i, ts in enumerate(timestamps):
        # 18시 ~ 19시 30분 사이일 때 (80% 확률로 켜짐)
        if 18 <= ts.hour <= 19 and ts.minute <= 30:
            if np.random.random() < 0.8:
                air_purifier_manual_on[i] = 1
                
    # 데이터프레임 생성
    df = pd.DataFrame({
        'timestamp': timestamps,
        'room': 'living_room',
        'temperature': temperature.round(1),
        'humidity': humidity.round(1),
        'pm25': pm25.round(1),
        'user_air_purifier_on': air_purifier_manual_on
    })
    
    # CSV 저장
    df.to_csv(filename, index=False)
    print(f"✅ Generated {num_records} records to '{filename}'.")
    
if __name__ == "__main__":
    generate_mock_data()
