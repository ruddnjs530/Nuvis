import pandas as pd
from sklearn.ensemble import IsolationForest
import os

def detect_anomalies_and_recommend(data_file=None):
    if data_file is None:
        data_file = os.path.join(os.path.dirname(__file__), "mock_sensor_data.csv")
    
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
        features = ['temperature', 'humidity', 'fine_dust']
        X = df[features]
        
        # 상위 5%의 비정상적(극단적)인 환경 데이터를 찾도록 훈련
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        df['anomaly_score'] = model.fit_predict(X)
        
        # -1 로 분류된 라벨이 머신러닝이 판단한 이상치 (Anomaly)
        anomalies = df[df['anomaly_score'] == -1]
        
        if len(anomalies) == 0:
            return {"message": "No environmental anomalies detected."}
            
        # 머신러닝이 극단적(Anomaly)으로 판단한 시점들의 평균을 추출해 권장 임계값 산출
        ml_recommended_fine_dust = anomalies['fine_dust'].mean()
        # 선제적 대응을 위해 Anomaly로 분류된 미세먼지 보다 살짝 아래(-5%)를 임계값으로 추천
        safe_margin_fine_dust = round(ml_recommended_fine_dust * 0.95, 1)
        
        return {
            "fine_dust": safe_margin_fine_dust,
            "anomaly_data_points_analyzed": len(anomalies),
            "reason": f"Isolation Forest 기반 이상 탐지 결과, 평소와 다른 비정상 대기 상태의 미세먼지 평균치는 {round(ml_recommended_fine_dust, 1)}입니다. 선제적 대응을 위해 {safe_margin_fine_dust}에 공기청정기 가동을 추천합니다."
        }
        
    except Exception as e:
        return {"error": str(e)}

def train_predictive_model(data_file="mock_sensor_data.csv"):
    """
    Random Forest Classifier를 사용하여 
    [시간대, 요일, 환경 수치] 기반의 기기 작동 확률을 학습합니다.
    """
    if not os.path.exists(data_file):
        return {"error": "Data file not found."}
        
    try:
        df = pd.read_csv(data_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 특징 추출 (Feature Engineering)
        df['hour'] = df['timestamp'].dt.hour
        # df['day_of_week'] = df['timestamp'].dt.dayofweek
        # df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        # 공기청정기 예시로 모델링
        features = ['hour', 'temperature', 'humidity', 'fine_dust']
        # features = ['hour', 'is_weekend', 'temperature', 'humidity', 'pm25']
        target = 'air_purifier_on'
        
        X = df[features]
        y = df[target]
        
        # 데이터가 불균형할 수 있으므로 간단한 학습만 수행
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        model.fit(X_train, y_train)
        
        # 특성 중요도 추출
        importances = dict(zip(features, model.feature_importances_))
        sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "model_type": "RandomForestClassifier",
            "accuracy": round(model.score(X_test, y_test), 2),
            "feature_importances": [
                {"feature": f, "importance": round(i, 3)} for f, i in sorted_importances
            ],
            "message": "머신러닝 모델 학습이 완료되었습니다. 이제 특정 상황에서의 기기 작동 확률을 예측할 수 있습니다."
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    result = detect_anomalies_and_recommend()
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
