from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import logging
import pandas as pd
from sklearn.ensemble import IsolationForest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Home AI Recommendation API")

# ─────────────────────────────────────────
# 안전장치 설정 (Safety Config)
# MAX_RECORDS : 페이로드가 너무 클 경우 최신 N건만 분석에 사용 (메모리/속도 보호)
# ANALYSIS_TIMEOUT : 기기 1개당 분석이 N초를 초과하면 포기하고 fallback 반환 (장애 전파 방지)
# ─────────────────────────────────────────
MAX_RECORDS: int = 500
ANALYSIS_TIMEOUT: float = 5.0


# ─────────────────────────────────────────
# 기기-센서 매핑 설정 (Device Config)
# 새로운 기기를 추가할 때는 이 딕셔너리에 한 줄만 추가하면 됩니다.
# ─────────────────────────────────────────
DEVICE_CONFIG = {
    "air_purifier": {
        "label": "공기청정기",
        "device_col": "air_purifier_on",      # SensorRecord의 ON/OFF 컬럼명
        "sensor_col": "pm25",                 # 관련 환경 센서 컬럼명
        "trigger_when": "high",               # 센서값이 높을 때 켬
        "unit": "㎍/m³",
    },
    "humidifier": {
        "label": "가습기",
        "device_col": "humidifier_on",
        "sensor_col": "humidity",
        "trigger_when": "low",                # 센서값이 낮을 때 켬 (습도 낮으면 가습기 ON)
        "unit": "%",
    },
    "dehumidifier": {
        "label": "제습기",
        "device_col": "dehumidifier_on",
        "sensor_col": "humidity",
        "trigger_when": "high",               # 센서값이 높을 때 켬 (습도 높으면 제습기 ON)
        "unit": "%",
    },
}


# ─────────────────────────────────────────
# Request Body 스키마 정의 (Pydantic)
# ─────────────────────────────────────────

class SensorRecord(BaseModel):
    """메인 서버에서 전달하는 센서 + 조작 이력 1건"""
    timestamp: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pm25: Optional[float] = None
    air_purifier_on: Optional[int] = 0
    humidifier_on: Optional[int] = 0      # 가습기 ON/OFF 이력
    dehumidifier_on: Optional[int] = 0   # 제습기 ON/OFF 이력

class AnalysisRequest(BaseModel):
    """AI 서버에 분석을 요청할 때의 Body 전체"""
    user_id: str
    sensor_data: List[SensorRecord]


# ─────────────────────────────────────────
# 범용 AI 분석 함수
# ─────────────────────────────────────────

def analyze_event_for_device(df: pd.DataFrame, config: dict) -> dict:
    """
    [이벤트 추천 - 범용]
    특정 기기를 켰을 당시의 평균 센서 수치를 기반으로
    최적의 자동화 임계값(Threshold)을 추천합니다.
    """
    device_col = config["device_col"]
    sensor_col = config["sensor_col"]
    label = config["label"]
    trigger_when = config["trigger_when"]
    unit = config["unit"]

    # 해당 기기/센서 컬럼이 데이터에 없으면 스킵
    if device_col not in df.columns or sensor_col not in df.columns:
        return {"message": f"No data columns found for {label}. Skipping."}

    on_events = df[df[device_col] == 1]

    if len(on_events) < 5:
        return {"message": f"Not enough data for {label} recommendation."}

    avg_sensor_val = float(on_events[sensor_col].mean())
    std_sensor_val = float(on_events[sensor_col].std())

    # trigger_when에 따라 임계값 방향이 달라짐
    # high(공청기/제습기): 평균보다 살짝 낮게 설정 (선제적 대응)
    # low(가습기):         평균보다 살짝 높게 설정 (선제적 대응)
    if trigger_when == "high":
        threshold = round(avg_sensor_val * 0.95, 1)
        condition = f"{threshold} {unit} 이상"
    else:
        threshold = round(avg_sensor_val * 1.05, 1)
        condition = f"{threshold} {unit} 이하"

    confidence = "High" if std_sensor_val < 15.0 else "Medium"

    return {
        "device": label,
        "sensor": sensor_col,
        "threshold_value": threshold,
        "condition_operator": ">" if trigger_when == "high" else "<",
        "analysis_details": {
            f"avg_{sensor_col}_when_turned_on": round(avg_sensor_val, 1),
            "data_points_analyzed": len(on_events),
            "pattern_confidence": confidence
        },
        "reason": (
            f"유저 행동 분석 결과, {sensor_col} 수치가 약 {avg_sensor_val:.1f}{unit} 일 때 "
            f"{label}을(를) 켰습니다. 선제적 대응을 위해 {condition}일 때 자동 실행을 추천합니다."
        )
    }


def get_lifestyle_period(hour: int) -> str:
    """시간대별 생활 패턴 분리"""
    if 6 <= hour < 9: return "아침 기상/출근 (06~09시)"
    elif 9 <= hour < 18: return "일과 (09~18시)"
    elif 18 <= hour < 23: return "저녁 귀가/휴식 (18~23시)"
    else: return "수면 (23~06시)"

def analyze_schedule_for_device(df: pd.DataFrame, config: dict) -> dict:
    """
    [라이프스타일 기반 스케줄 추천]
    기기를 가장 자주 켜는 생활 패턴(평일/주말, 특정 시간대)을 분석하여 반복 스케줄을 추천합니다.
    """
    device_col = config["device_col"]
    label = config["label"]

    if device_col not in df.columns:
        return {"message": f"No data column found for {label}. Skipping."}

    df_copy = df.copy()
    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
    
    # 1. 켜진 이벤트만 추출
    on_events = df_copy[df_copy[device_col] == 1].copy()

    if len(on_events) < 5:
        return {"message": f"Not enough data for {label} schedule recommendation."}

    # 2. 특징 추출 (시간대, 주말 여부, 라이프스타일 기간)
    on_events.loc[:, 'hour'] = on_events['timestamp'].dt.hour
    on_events.loc[:, 'is_weekend'] = on_events['timestamp'].dt.weekday >= 5
    on_events.loc[:, 'period'] = on_events['hour'].apply(get_lifestyle_period)
    
    # 주말/평일 + 시간대 조합 패턴 찾기
    on_events.loc[:, 'pattern'] = on_events.apply(
        lambda row: ("주말 " if row['is_weekend'] else "평일 ") + row['period'], axis=1
    )
    
    # 가장 빈번한 패턴 찾기
    pattern_counts = on_events['pattern'].value_counts()
    most_frequent_pattern = str(pattern_counts.index[0])
    frequency_count = int(pattern_counts.iloc[0])
    total_on = int(len(on_events))
    pattern_ratio = float(frequency_count / total_on)

    # 신뢰도 검증 (전체 켜진 횟수의 30% 이상이 해당 패턴에 집중될 경우 유의미하다고 판단)
    if pattern_ratio < 0.3:
        return {"message": f"No strong lifestyle patterns found for {label} yet."}
        
    # 추천 시간 도출 (해당 패턴 그룹 중 가장 잦은 시간)
    pattern_data = on_events[on_events['pattern'] == most_frequent_pattern]
    most_frequent_hour = int(pattern_data['hour'].mode()[0])
    is_weekend = "주말" in most_frequent_pattern
    
    repeat_days = ["Sat", "Sun"] if is_weekend else ["Mon", "Tue", "Wed", "Thu", "Fri"]

    return {
        "recommended_schedule": {
            "time": f"{most_frequent_hour:02d}:00",
            "device": config["device_col"].replace("_on", ""),
            "action": "ON",
            "repeat_days": repeat_days
        },
        "analysis_details": {
            "total_on_events_analyzed": total_on,
            "top_lifestyle_pattern": most_frequent_pattern,
            "pattern_hits": frequency_count,
            "pattern_ratio": f"{pattern_ratio:.1%}"
        },
        "reason": (
            f"유저님의 생활 패턴을 분석한 결과, 주로 {most_frequent_pattern}에 {label}을(를) 가장 많이 사용하셨습니다. "
            f"이 패턴이 전체 작동 횟수의 {pattern_ratio:.1%}를 차지합니다. "
            f"해당 패턴의 핵심 시간인 {most_frequent_hour}시에 자동 실행되도록 스케줄을 추가할까요?"
        )
    }


# ─────────────────────────────────────────
# 위기 감지형(Isolation Forest) AI 이상 탐지 함수
# ─────────────────────────────────────────
def analyze_environmental_anomalies(df: pd.DataFrame) -> dict:
    """
    [위기 감지형 알림]
    Isolation Forest 모델을 사용하여 최근 센서(온도, 습도, 미세먼지) 데이터의 
    유의미한 이상치(Anomaly)를 감지하고, 해당 시점의 평균 데이터를 바탕으로 
    선제적 위기 대응 알림을 위한 임계값을 추천합니다.
    """
    features = ['temperature', 'humidity', 'pm25']
    
    # 필요한 컬럼이 없으면 조기 반환
    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        return {"status": "skipped", "message": "필수 환경 센서 데이터가 부족하여 위기 감지를 건너뜁니다."}
        
    # 센서 측정값이 있는 깔끔한 데이터만 확보
    df_clean = df[features].dropna().copy()
    if len(df_clean) < 20: 
        return {"status": "skipped", "message": "위기 감지 모델을 분석하기에 유효한 데이터가 부족합니다."}
        
    try:
        # 상위 5%의 극단적/비정상적인 환경 데이터를 찾도록 모델 학습
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        df_clean['anomaly_score'] = model.fit_predict(df_clean[features])
        
        # -1 로 분류된 데이터가 시스템이 판단한 이상치(Anomaly)
        anomalies = df_clean[df_clean['anomaly_score'] == -1]
        
        if len(anomalies) == 0:
            return {"status": "normal", "message": "최근 환경 상태에서 특이사항이 감지되지 않았습니다."}
            
        # 주로 미세먼지 기준으로 비정상 상황 임계값을 추천
        ml_recommended_pm25 = anomalies['pm25'].mean()
        safe_margin_pm25 = round(ml_recommended_pm25 * 0.95, 1)
        
        return {
            "status": "warning",
            "device": "air_purifier",
            "ml_pm25_alert_threshold": safe_margin_pm25,
            "anomaly_data_points_analyzed": int(len(anomalies)),
            "reason": (
                f"최근 데이터의 이상치 분석 결과, 비정상적일 때의 평균 미세먼지가 약 {round(ml_recommended_pm25, 1)}㎍/m³ 입니다. "
                f"급격한 미세먼지 증가로 인한 위기 상황을 사전에 알릴 수 있도록, {safe_margin_pm25}㎍/m³ 도달 시 스마트 알림 전송을 추천합니다."
            )
        }
    except Exception as e:
        logger.error(f"[anomaly] 이상 탐지 오류: {e}")
        return {"status": "error", "message": "위기 감지 분석 중 오류가 발생했습니다."}


# ─────────────────────────────────────────
# API 엔드포인트
# ─────────────────────────────────────────

@app.post("/api/event/ai-suggestions")
async def get_event_suggestions(request: AnalysisRequest):
    """
    [이벤트 추천]
    메인 서버에서 유저의 센서+조작 이력 데이터를 전달하면,
    등록된 모든 기기(공기청정기/가습기/제습기)에 대한 이벤트 임계값을 한 번에 추천합니다.

    [안전장치]
    - 페이로드 상한: 최신 MAX_RECORDS(=500)건만 분석에 사용합니다.
    - 분석 타임아웃: 기기 1개당 ANALYSIS_TIMEOUT(=5초) 초과 시 fallback 응답을 반환합니다.
    """
    try:
        # ① 페이로드 상한선 적용 — 최신 MAX_RECORDS 건만 사용
        clipped_data = request.sensor_data[-MAX_RECORDS:]
        if len(request.sensor_data) > MAX_RECORDS:
            logger.warning(
                f"[event] user={request.user_id}: 수신 {len(request.sensor_data)}건 → "
                f"최신 {MAX_RECORDS}건만 분석에 사용합니다."
            )

        df = pd.DataFrame([record.dict() for record in clipped_data])
        suggestions = {}

        for device_type, config in DEVICE_CONFIG.items():
            try:
                # ② 분석 타임아웃 적용 — ANALYSIS_TIMEOUT 초 이내에 완료되지 않으면 포기
                result = await asyncio.wait_for(
                    asyncio.to_thread(analyze_event_for_device, df, config),
                    timeout=ANALYSIS_TIMEOUT,
                )
                suggestions[device_type] = result
            except asyncio.TimeoutError:
                logger.error(f"[event] {device_type} 분석 타임아웃 ({ANALYSIS_TIMEOUT}초 초과)")
                suggestions[device_type] = {
                    "status": "timeout",
                    "message": f"{config['label']} 분석이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
                }
            except Exception as device_err:
                logger.error(f"[event] {device_type} 분석 오류: {device_err}")
                suggestions[device_type] = {
                    "status": "error",
                    "message": f"{config['label']} 분석 중 오류가 발생했습니다."
                }

        # ③ 위기 감지 분석 (Isolation Forest) 적용
        try:
            anomaly_result = await asyncio.wait_for(
                asyncio.to_thread(analyze_environmental_anomalies, df),
                timeout=ANALYSIS_TIMEOUT,
            )
            suggestions["anomaly_warnings"] = anomaly_result
        except asyncio.TimeoutError:
            logger.error(f"[event] 이상 탐지 분석 타임아웃 ({ANALYSIS_TIMEOUT}초 초과)")
            suggestions["anomaly_warnings"] = {
                "status": "timeout",
                "message": "위기 감지 분석이 지연되고 있습니다."
            }
        except Exception as e:
            logger.error(f"[event] 이상 탐지 분석 오류: {e}")
            suggestions["anomaly_warnings"] = {
                "status": "error",
                "message": "위기 감지 분석 중 오류가 발생했습니다."
            }

        return {"status": "success", "user_id": request.user_id, "data": suggestions}

    except Exception as e:
        logger.error(f"[event] 전체 처리 오류: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/schedule/ai-suggestions")
async def get_schedule_suggestions(request: AnalysisRequest):
    """
    [스케줄 추천]
    메인 서버에서 유저의 센서+조작 이력 데이터를 전달하면,
    등록된 모든 기기(공기청정기/가습기/제습기)에 대한 반복 스케줄을 한 번에 추천합니다.

    [안전장치]
    - 페이로드 상한: 최신 MAX_RECORDS(=500)건만 분석에 사용합니다.
    - 분석 타임아웃: 기기 1개당 ANALYSIS_TIMEOUT(=5초) 초과 시 fallback 응답을 반환합니다.
    """
    try:
        # ① 페이로드 상한선 적용 — 최신 MAX_RECORDS 건만 사용
        clipped_data = request.sensor_data[-MAX_RECORDS:]
        if len(request.sensor_data) > MAX_RECORDS:
            logger.warning(
                f"[schedule] user={request.user_id}: 수신 {len(request.sensor_data)}건 → "
                f"최신 {MAX_RECORDS}건만 분석에 사용합니다."
            )

        df = pd.DataFrame([record.dict() for record in clipped_data])
        suggestions = {}

        for device_type, config in DEVICE_CONFIG.items():
            try:
                # ② 분석 타임아웃 적용 — ANALYSIS_TIMEOUT 초 이내에 완료되지 않으면 포기
                result = await asyncio.wait_for(
                    asyncio.to_thread(analyze_schedule_for_device, df, config),
                    timeout=ANALYSIS_TIMEOUT,
                )
                suggestions[device_type] = result
            except asyncio.TimeoutError:
                logger.error(f"[schedule] {device_type} 분석 타임아웃 ({ANALYSIS_TIMEOUT}초 초과)")
                suggestions[device_type] = {
                    "status": "timeout",
                    "message": f"{config['label']} 스케줄 분석이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
                }
            except Exception as device_err:
                logger.error(f"[schedule] {device_type} 분석 오류: {device_err}")
                suggestions[device_type] = {
                    "status": "error",
                    "message": f"{config['label']} 스케줄 분석 중 오류가 발생했습니다."
                }

        return {"status": "success", "user_id": request.user_id, "data": suggestions}

    except Exception as e:
        logger.error(f"[schedule] 전체 처리 오류: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
