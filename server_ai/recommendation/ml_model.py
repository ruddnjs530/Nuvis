import pandas as pd
from sklearn.ensemble import IsolationForest
import os

def detect_anomalies_and_recommend(data_file="mock_sensor_data.csv"):
    """
    Scikit-learn의 Isolation Forest 머신러닝 모델을 사용하여
    평소와 다른 비정상적인 환경 상태(Anomaly)를 감지하고,
    그 시점의 평균 데이터를 바탕으로 임계값을 추천합니다.
    """
    if not os.path.exists(data_file):
        return {"error": f"Data file '{data_file}' not found."}
        
    try:
        df = pd.read_csv(data_file)
        
        # 순수한 환경 수치(온도, 습도, 미세먼지)만 평가 (행동 데이터 배제)
        features = ['temperature', 'humidity', 'pm25']
        X = df[features]
        
        # 상위 5%의 비정상적(극단적)인 환경 데이터를 찾도록 훈련
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        df['anomaly_score'] = model.fit_predict(X)
        
        # -1 로 분류된 라벨이 머신러닝이 판단한 이상치 (Anomaly)
        anomalies = df[df['anomaly_score'] == -1]
        
        if len(anomalies) == 0:
            return {"message": "No environmental anomalies detected."}
            
        # 머신러닝이 극단적(Anomaly)으로 판단한 시점들의 평균을 추출해 권장 임계값 산출
        ml_recommended_pm25 = anomalies['pm25'].mean()
        # 선제적 대응을 위해 Anomaly로 분류된 미세먼지 보다 살짝 아래(-5%)를 임계값으로 추천
        safe_margin_pm25 = round(ml_recommended_pm25 * 0.95, 1)
        
        return {
            "ml_pm25_alert_threshold": safe_margin_pm25,
            "anomaly_data_points_analyzed": len(anomalies),
            "reason": f"Isolation Forest 기반 이상 탐지 결과, 평소와 다른 비정상 대기 상태의 미세먼지 평균치는 {round(ml_recommended_pm25, 1)}입니다. 선제적 대응을 위해 {safe_margin_pm25}에 공기청정기 가동을 추천합니다."
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    result = detect_anomalies_and_recommend()
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
