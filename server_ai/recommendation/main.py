from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import logging
import pandas as pd

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

    avg_sensor_val = on_events[sensor_col].mean()
    std_sensor_val = on_events[sensor_col].std()

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


def analyze_schedule_for_device(df: pd.DataFrame, config: dict) -> dict:
    """
    [스케줄 추천 - 범용]
    특정 기기를 가장 자주 켜는 시간대를 분석하여 반복 스케줄을 추천합니다.
    """
    device_col = config["device_col"]
    label = config["label"]

    if device_col not in df.columns:
        return {"message": f"No data column found for {label}. Skipping."}

    df_copy = df.copy()
    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
    on_events = df_copy[df_copy[device_col] == 1].copy()

    if len(on_events) < 5:
        return {"message": f"Not enough data for {label} schedule recommendation."}

    on_events.loc[:, 'hour'] = on_events['timestamp'].dt.hour
    most_frequent_hour = on_events['hour'].mode()[0]
    frequency_count = len(on_events[on_events['hour'] == most_frequent_hour])
    total_on = len(on_events)
    pattern_ratio = frequency_count / total_on

    if pattern_ratio < 0.15:
        return {"message": f"No strong scheduling patterns found for {label} yet."}

    return {
        "recommended_schedule": {
            "time": f"{most_frequent_hour:02d}:00",
            "device": config["device_col"].replace("_on", ""),
            "action": "ON",
            "repeat": "daily"
        },
        "analysis_details": {
            "total_on_events_analyzed": total_on,
            "frequent_hour_hits": frequency_count,
            "pattern_ratio": f"{pattern_ratio:.1%}"
        },
        "reason": (
            f"사용자님은 분석 기간 동안 매일 {most_frequent_hour}시 경에 가장 자주 "
            f"(총 {frequency_count}회) {label}을(를) 가동하셨습니다. "
            f"매일 {most_frequent_hour}시에 자동 실행되도록 스케줄을 추가할까요?"
        )
    }


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
