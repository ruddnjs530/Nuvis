from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, ConfigDict # ConfigDict, Field 추가
from typing import List, Optional
import asyncio
import logging
import pandas as pd
from sklearn.ensemble import IsolationForest
import os
import time

# ==============================================================================
# [교육용 주석] 추천 서버(Recommendation AI) 메인 API 엔드포인트
# ==============================================================================
# 역할: Java(Spring) 또는 Node.js와 같은 메인 백엔드 서버에서 대규모 센서 이력 데이터가
# 들어오면(HTTP POST), pandas 데이터프레임 기반의 통계/전통적 머신러닝 연산을 통해
# 생활 패턴을 분석하고 유저에게 제안할 수 있는 '최적의 자동화 규칙'을 역설정해주는 서버입니다.
# 프레임워크: FastAPI (Python에서 비동기 처리가 빠르고 가장 모던한 웹 프레임워크)
# ==============================================================================

# 기본 파이썬 로깅 패키지 설정. 웹서버가 구동되면서 찍히는 로그들의 형식과 레벨을 INFO(기본 안내)로 맞춤
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 웹 애플리케이션 초기화 (Swagger UI 등 문서에서 보일 이름 설정)
app = FastAPI(title="Smart Home AI Recommendation API")

# ─────────────────────────────────────────
# 전역 보안 미들웨어 (Security Middleware)
# ─────────────────────────────────────────
class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = {}
        self.MAX_REQ_PER_MIN = 300  
        self.MAX_PAYLOAD_MB = 10    
        self.MAX_PAYLOAD_BYTES = self.MAX_PAYLOAD_MB * 1024 * 1024

    def get_allowed_ips(self) -> set:
        ips = os.getenv("ALLOWED_BACKEND_IPS", "127.0.0.1")
        return {ip.strip() for ip in ips.split(",") if ip.strip()}

    async def dispatch(self, request: Request, call_next):
        # 환경변수 파일이 로드되지 않았다면 .env 파일에서 직접 로드
        if not os.getenv("ALLOWED_BACKEND_IPS"):
            from pathlib import Path
            env_path = Path(__file__).parent.parent.parent / "docs" / "shared" / ".env"
            if env_path.exists():
                with env_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line and not line.strip().startswith("#"):
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip())

        client_ip = request.client.host if request.client else "unknown"
        
        # 1. IP 화이트리스트 검증 
        allowed_ips = self.get_allowed_ips()
        if client_ip not in allowed_ips and "0.0.0.0" not in allowed_ips:
            logger.warning(f"🚨 [보안] 허가되지 않은 IP 접근 시도 차단: {client_ip}")
            return JSONResponse(status_code=403, content={"detail": f"Forbidden: Your IP ({client_ip}) is not allowed."})

        # 2. 파일 용량 상한선 검증 
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_PAYLOAD_BYTES:
            logger.warning(f"🚨 [보안] 허용 용량 초과 요청 차단: {client_ip} ({int(content_length)//1024//1024}MB)")
            return JSONResponse(status_code=413, content={"detail": f"Payload Too Large: Maximum allowed size is {self.MAX_PAYLOAD_MB}MB."})

        # 3. Rate Limiting 
        now = time.time()
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip] = [t for t in self.request_counts[client_ip] if now - t < 60]
        
        if len(self.request_counts[client_ip]) >= self.MAX_REQ_PER_MIN:
            logger.warning(f"🚨 [보안] Rate Limit 초과 차단 (DDoS 방어): {client_ip}")
            return JSONResponse(status_code=429, content={"detail": "Too Many Requests: Please slow down."})
            
        self.request_counts[client_ip].append(now)

        return await call_next(request)

app.add_middleware(SecurityMiddleware)

# ─────────────────────────────────────────
# 안전장치 설정 (Safety Config)
# 백엔드가 한 번에 수만 건의 기록을 던질 수 있으므로 서버의 메모리(RAM)나 과부하 방지차원의 규약
# MAX_RECORDS : 페이로드가 너무 클 경우 최신 N건만 잘라서 분석에 사용 
# ANALYSIS_TIMEOUT : 기기 1개당 분석 소요시간이 N초를 초과하면 해당 기기는 포기(Timeout)하고 반환 (장애 전파 방지용)
# ─────────────────────────────────────────
MAX_RECORDS: int = 500
ANALYSIS_TIMEOUT: float = 5.0


# ─────────────────────────────────────────
# 기기-센서 매핑 하드코딩 설정 (Device Config)
# ─────────────────────────────────────────
# 이 딕셔너리 구조가 이 파일의 '뇌' 역할 중 하나입니다.
# 나중에 에어컨, 난방기 등 새로운 기기가 출시되어 추가할 때는 로직을 안 고치고 이 목록에 한 묶음만 선언하면 됩니다.
DEVICE_CONFIG = {
    "air_purifier": {
        "label": "공기청정기",
        "device_col": "air_purifier_on",      # JSON/DB에 매핑되는 실제 기기 ON/OFF 컬럼명
        "sensor_col": "fine_dust",            # 이 기기와 가장 연관(인과성)있는 환경 센서 이름
        "trigger_when": "high",               # 센서 수치가 '높을 때' 켜야하는지 낮을 때 켜야하는지
        "unit": "㎍/m³",                      # 유저 안내 메시지용 텍스트 단위
    },
    "humidifier": {
        "label": "가습기",
        "device_col": "humidifier_on",
        "sensor_col": "humidity",
        "trigger_when": "low",                # 습도(humidity)가 '낮을 때(low)' 가습기 ON 구동
        "unit": "%",
    },
    "dehumidifier": {
        "label": "제습기",
        "device_col": "dehumidifier_on",
        "sensor_col": "humidity",
        "trigger_when": "high",               # 습도(humidity)가 '높을 때(high)' 제습기 ON 구동
        "unit": "%",
    },
}

# ─────────────────────────────────────────
# Request Body 스키마 정의 (Pydantic 유효성 검사기)
# ─────────────────────────────────────────
# Pydantic은 클라이언트가 API로 JSON 데이터를 보낼 때, 
# 데이터의 "자료형(타입)"과 "필수 포함 여부"가 맞는지 사전에 엄격하게 검증(Validation)해주는 Python 라이브러리입니다.
# 틀린 형식으로 들어오면 알아서 422 Unprocessable Entity 에러를 반환해줍니다.

class SensorRecord(BaseModel):
    """메인 서버에서 배열 형태로 담아 전달하는 개별 센서 측정 + 기기 조작 1행 데이터 스펙"""
    timestamp: str
    # 백엔드 DB/API 규격 'roomId'와 호환을 위한 alias
    room_id: int = Field(alias="roomId", validation_alias="room_id") 
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    fine_dust: Optional[float] = None     
    air_purifier_on: Optional[int] = 0
    humidifier_on: Optional[int] = 0
    dehumidifier_on: Optional[int] = 0

    model_config = ConfigDict(populate_by_name=True)

class AnalysisRequest(BaseModel):
    """AI API 서버에 POST 요청을 보낼 때 제일 최상단의 통합 Body 구조체"""
    # 백엔드(Nest.js/Spring)의 CamelCase 필드명(userId)과 AI 내부 snake_case를 호환시키기 위해 alias 적용
    user_id: int = Field(alias="userId", validation_alias="user_id") 
    
    # 백엔드 전달명 'data'를 AI 내부명 'sensor_data'로 유연하게 수용
    sensor_data: List[SensorRecord] = Field(alias="data", validation_alias="sensor_data")

    # 별칭(Alias)과 실제 변수명 둘 다 인식할 수 있도록 설정
    model_config = ConfigDict(populate_by_name=True)


# ─────────────────────────────────────────
# 범용 AI 분석 함수군 (비즈니스 로직)
# ─────────────────────────────────────────

def analyze_event_for_device(df: pd.DataFrame, config: dict) -> dict:
    """
    [이벤트성 룰 추천 알고리즘]
    "유저님은 보통 미세먼지가 X일 때 공기청정기를 켭니다. 자동화 할까요?" 라고 제안하는 AI 로직
    단순 전체 평균만 보지 않고, 가장 기기를 많이 켜는 '시간대(Lifestyle context)'를 고려해
    가장 유의미한 평균을 찾습니다.
    """
    device_col = config["device_col"]
    sensor_col = config["sensor_col"]
    label = config["label"]
    trigger_when = config["trigger_when"]
    unit = config["unit"]

    # 데이터 프레임에 필수 컬럼이 없으면 에러 내지 않고 즉시 스킵 안내문을 반환합니다.
    if device_col not in df.columns or sensor_col not in df.columns:
        return {"message": f"No data columns found for {label}. Skipping."}

    # 외부 데이터를 원본 훼손 없이 분석하기 위해 .copy()로 복제본을 떠서 조작합니다.
    df_copy = df.copy()
    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    
    # 시간(숫자)를 보고 -> 그 시간이 '출근길'인지 '수면' 시간대인지 범주형 라벨로 바꾸는 사용자 정의 함수를 일괄 적용(apply)합니다.
    df_copy['period'] = df_copy['hour'].apply(get_lifestyle_period)

    # 전체 데이터 중에서 오직 "해당 기기를 유저가 직접 켰던(==1)" 시점들만 필터링해서 뽑아냅니다.
    on_events = df_copy[df_copy[device_col] == 1]

    # 기기를 켠 경험이 5번 미만이면 통계/기계학습적 의미가 부족하므로 포기합니다.
    if len(on_events) < 5:
        return {"message": f"Not enough data for {label} recommendation."}

    # 1. 기기를 켰을 때 센서 수치의 전체 평균 (단순 통계 기준선)
    avg_sensor_val = float(on_events[sensor_col].mean())
    
    # 2. 기기를 유독 가장 많이 켜는 특정 '라이프스타일 시간대(예: 수면시간)' 찾기
    # .mode()는 최빈값(가장 자주 등장한 값)을 찾아줍니다.
    most_freq_period = on_events['period'].mode()[0]
    
    # 3. 그 가장 자주 켜는 시간대(context) 환경에 있었던 기기 ON 시점만 다시 재필터링해서 평균을 구함 (보다 맥락적이고 정교함)
    period_events = on_events[on_events['period'] == most_freq_period]
    period_avg = float(period_events[sensor_col].mean())

    # trigger_when 로직 기획:
    # "미세먼지(high)"의 경우, 유저가 켰을 때 평균 50이면, 유저가 불쾌감을 느끼기 아주 살짝 전인 47(50*0.95)쯤 
    # 선제적으로 켜지게 트리거를 셋팅해줍니다. 
    # 반대로 가습기(low)는 건조할때 켜므로, 평균 30일때 켠다면, 30%보다 높은 31%(30*1.05)일때 선제 방어하도록 제안.
    if trigger_when == "high":
        threshold = round(period_avg * 0.95, 1)
        condition = f"{threshold} {unit} 이상"
    else:
        threshold = round(period_avg * 1.05, 1)
        condition = f"{threshold} {unit} 이하"

    return {
        "actionModuleType": label,        # 메인 서버와의 DB 연동 규격을 맞추기 위해 key 통일
        "sensor": sensor_col,
        "context": most_freq_period,
        "threshold_value": threshold,
        "condition_operator": ">" if trigger_when == "high" else "<",
        "analysis_details": {
            "overall_avg": round(avg_sensor_val, 1),
            "context_avg": round(period_avg, 1),
            "data_points_in_context": len(period_events)
        },
        "reason": (
            f"유저님은 주로 '{most_freq_period}'에 {label}을(를) 사용하셨습니다. "
            f"이 시간대 평균 {sensor_col} 수치는 {period_avg:.1f}{unit}입니다. "
            f"해당 상황에 맞춰 {condition}일 때 자동 가동을 추천합니다."
        )
    }


def get_lifestyle_period(hour: int) -> str:
    """시간을 받아 4가지 거시적 라이프스타일 묶음 문자로 매핑"""
    if 6 <= hour < 9: return "아침 기상/출근 (06~09시)"
    elif 9 <= hour < 18: return "일과 (09~18시)"
    elif 18 <= hour < 23: return "저녁 귀가/휴식 (18~23시)"
    else: return "수면 (23~06시)"


def analyze_schedule_for_device(df: pd.DataFrame, config: dict) -> dict:
    """
    [시간 스케줄 기반 추천 알고리즘]
    센서의 환경 오염 문제가 아니라, 유저가 단순히 매일 특정 시간에 씻고 나와서 
    반복적으로 습관처럼 특정 장비를 켜는 경우(Time Schedule)를 찾아냅니다.
    """
    device_col = config["device_col"]
    label = config["label"]

    if device_col not in df.columns:
        return {"message": f"No data column found for {label}. Skipping."}

    df_copy = df.copy()
    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
    
    # 해당 기기를 '켰다(==1)' 고 마킹된 모든 과거 내역만 모음
    on_events = df_copy[df_copy[device_col] == 1].copy()

    if len(on_events) < 5:
        return {"message": f"Not enough data for {label} schedule recommendation."}

    # 특징 추출
    on_events.loc[:, 'hour'] = on_events['timestamp'].dt.hour
    on_events.loc[:, 'period'] = on_events['hour'].apply(get_lifestyle_period)
    on_events.loc[:, 'pattern'] = on_events['period']
    
    # 어떤 시간대 패턴(period)에서 이 이력이 가장 많았는지 집계표(value_counts)를 만듦
    pattern_counts = on_events['pattern'].value_counts()
    
    most_frequent_pattern = str(pattern_counts.index[0]) # 1등 패턴 이름
    frequency_count = int(pattern_counts.iloc[0])        # 1등 패턴의 건수
    total_on = int(len(on_events))                       # 기기 켠 전체 건수
    
    # 1등 패턴 점유율 = 패턴건수 / 켰던 총건수
    pattern_ratio = float(frequency_count / total_on)

    # 신뢰도 검증: 
    # 특정 시간대에 켜진 횟수가 총 횟수의 30%를 못 넘으면, 이 사람의 습관이라기보단 
    # 켜는 시간이 무작위(Random)에 가깝다고 판단하고 추천을 기각시킴 (신뢰도 미달)
    if pattern_ratio < 0.3:
        return {"message": f"No strong lifestyle patterns found for {label} yet."}
        
    # 그 지배적인 패턴 내에서 '정확히 몇 시' 인지 최빈값을 찾아냄
    pattern_data = on_events[on_events['pattern'] == most_frequent_pattern]
    most_frequent_hour = int(pattern_data['hour'].mode()[0])

    return {
        "recommended_schedule": {
            "time": f"{most_frequent_hour:02d}:00",      # 숫자 9 -> 문자 "09:00" 포맷팅
            "actionModuleType": config["device_col"].replace("_on", ""), # "air_purifier_on" -> "_on" 삭제 후 응답
            "action": "ON",
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
            f"해당 패턴의 핵심 시간인 {most_frequent_hour:02d}시에 자동 실행되도록 스케줄을 추가할까요?"
        )
    }

# 이 Isolation Forest 함수는 외부 머신러닝 모듈(ml_model.py)와 논리가 거의 같습니다. 다만 메인 앱 통합용입니다.
def analyze_environmental_anomalies(df: pd.DataFrame) -> dict:
    features = ['temperature', 'humidity', 'fine_dust'] 
    
    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        return {"status": "skipped", "message": "필수 환경 센서 데이터가 부족하여 위기 감지를 건너뜁니다."}
        
    df_clean = df[features].dropna().copy()
    if len(df_clean) < 20: 
        return {"status": "skipped", "message": "위기 감지 모델을 분석하기에 유효한 데이터가 부족합니다."}
        
    try:
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        df_clean['anomaly_score'] = model.fit_predict(df_clean[features])
        anomalies = df_clean[df_clean['anomaly_score'] == -1]
        
        if len(anomalies) == 0:
            return {"status": "normal", "message": "최근 환경 상태에서 특이사항이 감지되지 않았습니다."}
            
        ml_recommended_fine_dust = anomalies['fine_dust'].mean()
        safe_margin_fine_dust = round(ml_recommended_fine_dust * 0.95, 1)
        
        return {
            "status": "warning",
            "actionModuleType": "air_purifier", 
            "fine_dust": safe_margin_fine_dust,      
            "anomaly_data_points_analyzed": int(len(anomalies)),
            "reason": (
                f"최근 데이터의 이상치 분석 결과, 비정상적일 때의 평균 미세먼지가 약 {round(ml_recommended_fine_dust, 1)}㎍/m³ 입니다. "
                f"급격한 미세먼지 증가로 인한 위기 상황을 사전에 알릴 수 있도록, {safe_margin_fine_dust}㎍/m³ 도달 시 스마트 알림 전송을 추천합니다."
            )
        }
    except Exception as e:
        logger.error(f"[anomaly] 이상 탐지 오류: {e}")
        return {"status": "error", "message": "위기 감지 분석 중 오류가 발생했습니다."}


# ─────────────────────────────────────────
# FastAPI 라우터 엔드포인트 세팅부
# 클라이언트(메인서버)가 호출할 웹 주소(URL Path)와 처리 메서드를 연결합니다.
# ─────────────────────────────────────────

@app.post("/api/event/ai-suggestions")
async def get_event_suggestions(request: AnalysisRequest):
    """
    [이벤트성 임계값 추천 API]
    요청 들어오면: 1. 데이터 파이 길이 자름 -> 2. 각 기기별로 5초 제한 스레드(병렬) 분석 -> JSON 응답
    """
    try:
        # ① 메모리 보호: 페이로드 상한선(MAX_RECORDS) 적용
        clipped_data = request.sensor_data[-MAX_RECORDS:]
        if len(request.sensor_data) > MAX_RECORDS:
            logger.warning(
                f"[event] user={request.user_id}: 수신 {len(request.sensor_data)}건 → "
                f"최신 {MAX_RECORDS}건만 분석에 사용합니다."
            )

        # 수신된 Pydantic 모델 객체들을 분석 편의성이 100배 좋은 통계 전용 Pandas DataFrame 2차원 표로 변환
        df = pd.DataFrame([record.dict() for record in clipped_data])
        suggestions = {}

        # 모든 등록된 기기(공청기, 가습기, 제습기 등) 리스트를 순회하며 분석 시행
        for device_type, config in DEVICE_CONFIG.items():
            try:
                # ② [핵심 비동기 디자인]: 
                # pandas 연산(CPU 집약적 동작)은 메인 스레드를 정지시킵니다.
                # 웹서버가 멈추지 않게 별도 스레드(to_thread)로 계산을 던져놓고 기다리되,
                # 만약 해당 기기 분석이 ANALYSIS_TIMEOUT초 이내에 안 끝나면 쿨하게 포기하게(TimeoutError) 만듭니다.
                result = await asyncio.wait_for(
                    asyncio.to_thread(analyze_event_for_device, df, config),
                    timeout=ANALYSIS_TIMEOUT,
                )
                suggestions[device_type] = result
            except asyncio.TimeoutError:
                logger.error(f"[event] {device_type} 분석 타임아웃 ({ANALYSIS_TIMEOUT}초 초과)")
                # 5초 넘기면 에러로 앱이 터지지 않고 대신 이 문구를 반환
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

        # ③ 추가로, 위에서 분석된 환경 데이터를 바탕으로 위기 탐지(Isolation Forest) 모델 한 바퀴 가동
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

        # 모든 연산이 끝나고 취합된 최상단 JSON 객체를 반환
        return {"status": "success", "user_id": request.user_id, "data": suggestions}

    except Exception as e:
        logger.error(f"[event] 전체 처리 오류: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/schedule/ai-suggestions")
async def get_schedule_suggestions(request: AnalysisRequest):
    """
    [스케줄(시간) 추천 API]
    메인 서버 통신망을 통해 유저의 이력 데이터를 전달받아,
    유저가 매일 규칙적인 습관으로 기기를 켜는 '스케줄 매크로(Cron)' 시간을 제안합니다.
    """
    try:
        # ① 페이로드 상한선 적용 
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
                # ② 각 종목 기기별 타임아웃 적용 및 스레딩 병렬 분석
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

        # 추천된 스케줄 데이터 트리를 JSON 포맷으로 패키징하여 Return
        return {"status": "success", "user_id": request.user_id, "data": suggestions}

    except Exception as e:
        logger.error(f"[schedule] 전체 처리 오류: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    # 운영체제의 단독 스크립트로 실행되었을 때(예: $ python main.py) 활성화되는 부분입니다.
    # uvicorn은 Python의 비동기 웹서버 엔진구동체입니다. (host 0.0.0.0은 외부접속 전면허용, 포트는 9000번 사용)
    uvicorn.run(app, host="0.0.0.0", port=9000)
