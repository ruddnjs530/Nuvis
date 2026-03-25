import pandas as pd
from sklearn.ensemble import IsolationForest
import os

# ==============================================================================
# [교육용 주석] 추천 API 서브 머신러닝 모듈 (Anomaly Detection & Random Forest)
# ==============================================================================
# 이 파일은 딥러닝(LSTM) 메인 모델 외에, Scikit-learn(전통적 머신러닝 라이브러리)을
# 활용하여 '위기 감지'나 '기본 확률 예측' 등 빠르고 가벼운 부가 통계 기능을 제공합니다.
# ==============================================================================

def detect_anomalies_and_recommend(data_file=None):
    if data_file is None:
        data_file = os.path.join(os.path.dirname(__file__), "mock_sensor_data.csv")
    
    """
    [위기 감지형 탐지 알고리즘 - Isolation Forest]
    Isolation Forest는 정상 데이터 무리(군집)에서 멀리 동떨어진 '이상치(Anomaly)'를
    매우 빠르고 적은 컴퓨팅 파워로 찾아내는 '비지도 학습(정답 없는 학습)' 알고리즘입니다.
    특정 스레시홀드를 벗어난 비정상적인 환경(화재, 미세먼지 폭증 수준)이 언제 있었는지 감지하고,
    그 시점의 평균 데이터를 바탕으로 스마트홈 기기 작동 임계값을 역으로 추천합니다.
    """
    if not os.path.exists(data_file):
        return {"error": f"Data file '{data_file}' not found."}
        
    try:
        # 데이터 로드
        df = pd.read_csv(data_file)
        
        # 순수한 외부 환경 수치(온/습도, 미세먼지)만 평가 테이블로 올립니다. 
        # (기기를 켰다/껐다 하는 유저의 행동은 이상 기후 데이터 자체와 무관하므로 배제합니다)
        features = ['temperature', 'humidity', 'fine_dust']
        X = df[features]
        
        # Isolation Forest 모델 생성
        # n_estimators=100: 나무(Tree 모델) 100개를 만들어서 각자 판별하게 한 뒤 다수결로 판정합니다.
        # contamination=0.05: 우리가 임의로 "보유한 전체 데이터 중 약 5% 정도는 비정상(Anomaly)일 것이다"라고 
        #                     사전 비율을 가정하여 모델에게 가이드라인을 줍니다.
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        
        # fit_predict: 데이터를 보고 정상 패턴을 학습(fit)함과 동시에 각 줄(행)이 정상인지 이상치인지 예측(predict)
        df['anomaly_score'] = model.fit_predict(X)
        
        # 머신러닝 평가 결과: 데이터프레임 안에서 1 은 정상(Normal), -1 이 비정상(Anomaly)을 의미합니다.
        anomalies = df[df['anomaly_score'] == -1]
        
        if len(anomalies) == 0:
            return {"message": "No environmental anomalies detected."}
            
        # 머신러닝 모델이 극단적 환경(Anomaly)으로 판단한 시점들끼리 모아서, 그때의 미세먼지 평균치를 구합니다.
        ml_recommended_fine_dust = anomalies['fine_dust'].mean()
        
        # 선제적 위기 대응 목적의 로직: 
        # 환경이 100% 최악이 된 상황에 기기를 켜는 건 늦습니다.
        # 따라서 최악의 수치에서 -5% (0.95곱하기) 낮춘 수치를 '미리 예방할 수 있는 임계값'으로 추천합니다.
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
    [기초 확률 예측 알고리즘 - Random Forest]
    Random Forest Classifier를 사용하여 [시간대, 온도, 습도, 미세먼지] 피처(Feature)를 보았을 때
    사용자가 기기를 켤 '확률'을 학습하는 또 다른 클래식 머신러닝 보조 도구입니다.
    현재 API에서 메인 예측에는 딥러닝(LSTM)이 쓰이지만, 어떤 변수(온도냐, 미세먼지냐)가 
    판단에 가장 결정적이었는지(Feature Importance)를 분석해볼 때 유용합니다.
    """
    if not os.path.exists(data_file):
        return {"error": "Data file not found."}
        
    try:
        df = pd.read_csv(data_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 특징 추출 (Feature Engineering): 문자열 날짜에서 '시간(hour)' 속성만 추출해 의미있는 변수로 사용
        df['hour'] = df['timestamp'].dt.hour
        
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        # 학습에 쓸 입력값 배열 구성 (이번 예시는 공기청정기를 언제 켜는지 분석)
        features = ['hour', 'temperature', 'humidity', 'fine_dust']
        target = 'air_purifier_on' # 모델이 맞춰야할 최종 목적 정답(Label/Target)
        
        X = df[features]
        y = df[target]
        
        # 데이터 분리(train_test_split): 
        # 전체 100건의 데이터가 있다면 무작위 80건(80%)은 훈련용 문제지로 쓰고, 20건(20%)은 시험용으로 남겨둡니다.
        # 이렇게 해야 모델이 문제 자체를 외운 것(과적합, Overfitting)인지 아니면 진짜 원리를 깨달은건지 객관적으로 검증할 수 있습니다.
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Random Forest 알고리즘 세팅 및 훈련
        # max_depth=5: 스무고개처럼 데이터에게 질문하는 깊이를 5번까지만 허용하여 수식이 비정상적으로 복잡해지는 걸 방지합니다.
        model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        model.fit(X_train, y_train) # <- 여기서 본격적인 학습 연산이 진행됩니다.
        
        # 특성 중요도(Feature Importances) 산출:
        # 훈련된 이 모델이 '공기청정기' 작동 여부를 판단할 때 어느 변수(시간, 미세먼지 등)를 सबसे 비중있게 계산했는지 
        # 0.0 ~ 1.0 비율로 알려주는 기능입니다.
        importances = dict(zip(features, model.feature_importances_))
        sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True) # 내림차순 정렬
        
        return {
            "model_type": "RandomForestClassifier",
            "accuracy": round(model.score(X_test, y_test), 2), # 아까 남겨둔 시험지(Test Set)로 본 100점 만점 중 백분율(정확도)
            "feature_importances": [
                {"feature": f, "importance": round(i, 3)} for f, i in sorted_importances
            ],
            "message": "머신러닝 모델 학습이 완료되었습니다. 이제 특정 상황에서의 기기 작동 확률을 예측할 수 있습니다."
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # 파이썬 스크립트를 직접 실행($ python ml_model.py)했을 때 이상 탐지 결과를 터미널에 프린트해주는 테스트용 영역
    result = detect_anomalies_and_recommend()
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
