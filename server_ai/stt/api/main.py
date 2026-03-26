import os
import tempfile
from io import BytesIO
from contextlib import asynccontextmanager
from pathlib import Path

import torch
import numpy as np
import librosa
import soundfile as sf
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from stt_parser import DEFAULT_ROOM_MAP, get_room_map, parse_voice_command, set_room_map
import json
import requests

# ==============================================================================
# [교육용 주석] STT (음성 인식) 최전방 AI 모듈 API 서버
# ==============================================================================
# 역할: 리액트 앱/안드로이드 클라이언트나 백엔드에서 녹음된 오디오 파일(.wav, .mp3)을 
#       FastAPI로 던져주면, GPU 메모리에 올라가 있는 Whisper AI 모델이 이를 글자로 받아적고(STT),
#       stt_parser 모듈을 거쳐 최종 로봇 제어 JSON 명령어 셋으로 파싱/조립해 다시 응답해주는 다차원 지능 서버입니다.
# ==============================================================================

# GPU 디바이스 설정: 머신러닝 모델이 서버의 모든 GPU를 잡식으로 먹지 않고 5번 그래픽카드만 독점하도록 강제 구상
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "5"
# PyTorch에게 엔비디아 그래픽카드(CUDA)가 있는지 물어보고, 없으면 느리지만 CPU라도 쓰도록 유동적 세팅
device = "cuda" if torch.cuda.is_available() else "cpu"

# ─────────────────────────────────────────
# 1. AI 모델 경로 및 동기화 상태(State) 설정
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent.parent
SHARED_ENV_PATH = PROJECT_DIR / "docs" / "shared" / ".env" # 데이터베이스나 백엔드 메인 서버 주소가 적혀있는 환경변수 파일

# 파인튜닝 단계별 모델 절대 경로 (디렉토리 참조)
MODEL_V2 = BASE_DIR / "model" / "v2_full"
MODEL_V1 = BASE_DIR / "model" / "whisper-smarthome"
BASE_MODEL = "openai/whisper-small" # 모델이 아예 없을 때 허깅페이스 인터넷망에서 땡겨올 순정 공기계 모델

ROOM_NAME_ENDPOINT = "/api/room/name" # 백엔드 서버에 실제 방 ID 번호들을 동기화받아올 엔드포인트 주소
ROOM_MAP_SOURCE = "uninitialized"

# 우선순위 분기 (Smart Fallback Router)
# 가장 최신에 학습된 똑똑한 V2 모델이 디스크 폴더에 있으면 그걸 제일 우선적으로 로드하고, 
# 없으면 V1, 그것마저도 삭제됐다면 인터넷에서 다운받은 생짜 BASE 모델을 선택하는 영리한 방어 코드입니다.
if MODEL_V2.exists():
    MODEL_PATH = str(MODEL_V2)
    print(f"🔥 Loading Fine-tuned Model V2: {MODEL_PATH}")
elif MODEL_V1.exists():
    MODEL_PATH = str(MODEL_V1)
    print(f"🔥 Loading Fine-tuned Model V1: {MODEL_PATH}")
else:
    MODEL_PATH = BASE_MODEL
    print(f"📡 Loading Base Model: {MODEL_PATH}")

# ─────────────────────────────────────────
# 2. Whisper 모델 메모리 적재 (Loading)
# ─────────────────────────────────────────
try:
    processor = WhisperProcessor.from_pretrained(MODEL_PATH)
    # 실제 딥러닝 뇌를 그래픽카드 VRAM 위주로 올림 (.to(device))
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_PATH).to(device)
    
    # 한국어 환경(Korean)으로만 생각하고 음성 받아쓰기(transcribe)만 집중하도록 AI 뇌구조 강제 고정 튜닝 
    # (이렇게 하면 첫 마디를 듣고 영어인지 일어인지 고민하는 시간을 생략해 응답 속도가 비약적으로 단축됨)
    model.generation_config.language = "korean"
    model.generation_config.task = "transcribe"
    model.generation_config.forced_decoder_ids = None
    print("✅ Model & Processor loaded successfully!")
except Exception as e:
    print(f"❌ Model load failed: {e}")
    exit(1)


def load_shared_env_file() -> None:
    """백엔드 서버 IP를 동적으로 알아내기 위해 프로젝트 최상단 루트 폴더에 있는 .env 환경파일을 파이썬 내부로 주입시키는 유틸"""
    if not SHARED_ENV_PATH.exists():
        return

    with SHARED_ENV_PATH.open("r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            # 주석(#)이거나 빈 줄은 거름
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            # os 환경 공간에 변수로 등록 
            os.environ.setdefault(key.strip(), value.strip())


def get_backend_base_url() -> str | None:
    """주입된 환경변수에서 메인 Spring/Node API 앱서버의 공통 호스트 주소를 반환합니다."""
    load_shared_env_file()

    for env_key in ("BACKEND_BASE_URL", "BACKEND_API_BASE_URL"):
        value = os.getenv(env_key)
        if value:
            return value.rstrip("/") # 맨 뒤 슬래시 안전하게 제거
    return None


def normalize_room_name_payload(payload) -> list[dict]:
    """
    백엔드 프레임워크가 주는 응답 JSON Data 포맷이 { "data": [...] } 일수도 있고 { "result": [...] } 일수도 있기에,
    껍데기(Wrapper)를 알아서 벗겨내고 핵심 알맹이 배열 데이터만 깔끔히 도출해주는 정규화 함수
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("data", "rooms", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise ValueError("room name API response format is invalid")


def fetch_room_map_from_backend() -> dict:
    """
    STT에서 유저의 목소리를 "거실" 이라고 인식했을 때, 메인 서버 DB 기준 '거실'의 고유 ID가 뭔지 
    사전에 실시간으로 동기화 받아오는 외부 네트워크 HTTP 통신 코어입니다.
    """
    backend_base_url = get_backend_base_url()
    if not backend_base_url:
        raise ValueError("BACKEND_BASE_URL is not configured")

    url = f"{backend_base_url}{ROOM_NAME_ENDPOINT}"
    
    # requests 모듈로 동기화 시행 (최대 5초 기다림 설정으로 우리 AI 서버가 무한대기 락킹되는 꼴 방지)
    response = requests.get(url, timeout=5)
    response.raise_for_status() # 400~500번대 에러가 나면 즉각 예외 투척

    rooms = normalize_room_name_payload(response.json())
    room_map = {}

    for room in rooms:
        if not isinstance(room, dict):
            continue
        room_id = room.get("roomId", room.get("room_id"))
        room_name = room.get("name", room.get("roomName"))
        if room_id is None or room_name is None:
            continue
        room_map[str(room_name).strip()] = int(room_id)

    if not room_map:
        raise ValueError("room name API returned an empty room map")
    return room_map


def initialize_room_map() -> None:
    """
    이 AI 웹서버가 맨 처음 부팅될 때 딱 한번 자동으로 실행되어 
    백엔드의 최신 방 현황 정보 구조체(예: 스테이션(HQ)=1, 거실=2, 침실=3, 주방=4)를 땡겨와 파서에게 미리 외우게 가르쳐두는 초기화 함수
    """
    global ROOM_MAP_SOURCE
    try:
        room_map = fetch_room_map_from_backend()
        set_room_map(room_map)  # stt_parser 파이썬 모듈 전역에 이 맵을 덮어씌워서 이식시킴
        ROOM_MAP_SOURCE = "backend"
        print(f"✅ Room map loaded from backend: {get_room_map()}")
    except Exception as e:
        # 백엔드 서버가 아직 부팅이 안됐거나 죽었더라도, AI 서버 자체 부팅이 막히면 안되므로 
        # 하드코딩된 기본값(Fallback Dummy)으로 대체 후 생존시키는 시스템 장애 격리(Fault Tolerance) 처리.
        set_room_map(DEFAULT_ROOM_MAP)
        ROOM_MAP_SOURCE = "fallback"
        print(f"⚠️ Failed to load room map from backend: {e}")
        print(f"⚠️ Falling back to default room map: {get_room_map()}")


def remove_temp_file(temp_file_path: str | None) -> None:
    """서버 디스크(SSD) 용량 낭비 방지를 위한 일회용 찌꺼기 파일 청소기"""
    if temp_file_path and os.path.exists(temp_file_path):
        os.remove(temp_file_path)


def load_audio_from_temp_file(temp_file_path: str) -> np.ndarray:
    """가무거운 오디오 물리 파일(temp)을 librosa로 냅다 읽고 16000Hz 주파수로 규격화하여 Numpy 수학 행렬로 반환"""
    audio_input, _ = librosa.load(temp_file_path, sr=16000)
    return audio_input


def load_audio_from_upload_bytes(audio_bytes: bytes, filename: str | None = None) -> np.ndarray:
    """
    HTTP POST 네크워크를 타고 날아온 오디오 파일을 디스크에 저장하는 과정 없이,
    넉넉하지만 매우 빠른 휘발성 RAM 메모리(BytesIO)상에서 '인-메모리 방식'으로 곧바로 해독하는 극한의 속도 최적화 로직입니다.
    이게 실패하면 어쩔수 없이 두번째 플랜인 임시 물리 파일(TempFile)로 다운받아서 옛날 방식으로 읽어들입니다.
    """
    try:
        audio_buffer = BytesIO(audio_bytes)
        audio_array, sample_rate = sf.read(audio_buffer, dtype="float32")
        
        # 2채널(좌우 소리가 다른 스테레오)을 AI가 인식하기 쉬운 1채널 흑백음(모노)으로 강제 합침 (수학적 픽셀 축소)
        if getattr(audio_array, "ndim", 1) > 1:
            audio_array = audio_array.mean(axis=1)

        # 모델이 요구하는 필수 주파수 스펙인 16kHz가 아니면 소프트웨어적으로 변형시킴
        if sample_rate != 16000:
            audio_array = librosa.resample(audio_array, orig_sr=sample_rate, target_sr=16000)

        return np.asarray(audio_array, dtype=np.float32)
    except Exception:
        # 위 빠른 메모리 해독에 실패하면 윈도우/리눅스의 임시 폴더에 확장자(.bin 등)를 달아 일시적 물리파일 코어로 격하시킴
        suffix = Path(filename or "").suffix or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(audio_bytes)

        try:
            return load_audio_from_temp_file(temp_file_path)
        finally:
            remove_temp_file(temp_file_path) # 반드시 삭제 스위프 처리


# FastAPI의 최신 문법(컨텍스트 라우터): 웹서버가 구동되기 시작할 때(yield 전) 초기 설정을 마치고, 꺼질 때(yield 후) 뒷정리하는 라이프사이클 훅
@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_room_map()
    yield


# FastAPI 통합 앱 객체 선언 (Swagger UI 등 문서에서 보일 타이틀과 이벤트 훅 장착)
app = FastAPI(
    title="Smart Home AI STT API (Fine-tuned)",
    lifespan=lifespan,
)

# ─────────────────────────────────────────
# 전역 보안 미들웨어 (Security Middleware)
# ─────────────────────────────────────────
class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = {}
        self.MAX_REQ_PER_MIN = 300  # API 서버 통합 분당 최대 300회 제한
        self.MAX_PAYLOAD_MB = 10    # 최대 10MB (OOM 방지)
        self.MAX_PAYLOAD_BYTES = self.MAX_PAYLOAD_MB * 1024 * 1024

    def get_allowed_ips(self) -> set:
        ips = os.getenv("ALLOWED_BACKEND_IPS", "127.0.0.1")
        return {ip.strip() for ip in ips.split(",") if ip.strip()}

    async def dispatch(self, request: Request, call_next):
        # 환경변수가 아직 안불러와졌다면 로드 
        load_shared_env_file()

        client_ip = request.client.host if request.client else "unknown"
        
        # 1. IP 화이트리스트 검증 (인가되지 않은 IP 전면 즉각 차단)
        allowed_ips = self.get_allowed_ips()
        if client_ip not in allowed_ips and "0.0.0.0" not in allowed_ips:
            print(f"🚨 [보안] 허가되지 않은 접속 시도 IP 차단: {client_ip}")
            return JSONResponse(status_code=403, content={"detail": f"Forbidden: Your IP ({client_ip}) is not allowed by the AI Server."})

        # 2. 파일 용량 검증 (10MB 제한)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_PAYLOAD_BYTES:
            print(f"🚨 [보안] 허용 파일 용량 초과 서버 폭발(OOM) 방어 가동: {client_ip}")
            return JSONResponse(status_code=413, content={"detail": f"Payload Too Large: Maximum allowed audio file size is {self.MAX_PAYLOAD_MB}MB."})

        # 3. Rate Limiting (DDoS 방어)
        now = time.time()
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # 60초 넘은 흔적 제거
        self.request_counts[client_ip] = [t for t in self.request_counts[client_ip] if now - t < 60]
        
        if len(self.request_counts[client_ip]) >= self.MAX_REQ_PER_MIN:
            print(f"🚨 [보안] Rate Limit 초과 차단 (DDoS 방어 가동): {client_ip}")
            return JSONResponse(status_code=429, content={"detail": "Too Many Requests: Please slow down."})
            
        self.request_counts[client_ip].append(now)

        return await call_next(request)

app.add_middleware(SecurityMiddleware)


# ─────────────────────────────────────────
# 3. API 라우터 (엔드포인트) 구현부
# ─────────────────────────────────────────

@app.get("/api/stt/health")
async def stt_health():
    """L4 로드밸런서나 컨테이너 오케스트레이션(k8s)이 이 AI 서버가 살았나 죽었나 핑을 10초마다 찔러보는 상태 진단용 주소(Health Check)"""
    room_map = get_room_map()
    return {
        "status": "ok",
        "device": device,
        "model_path": MODEL_PATH,                  # 현재 어떤 수준의 똑똑함을 가진 버전을 물고 켜졌는지 로깅
        "room_map_source": ROOM_MAP_SOURCE,        # 방 이름 동기화는 백엔드에서 정상적으로 받았는지 확인용
        "room_map_count": len(room_map),
        "room_map_preview": room_map,
    }


@app.post("/api/stt/transcribe")
async def transcribe_audio_api(audio: UploadFile = File(...)):
    """
    [핵심 STT 코어 API] 클라이언트가 마이크 버튼을 누르고 녹음한 고음질/잡음 파일을 쏴주면 들어오는 주소입니다.
    데이터 파이프라인 흐름: 
    1. 파일 수신 -> 2. 메모리 해독(RAM) -> 3. Whisper AI 한국어 텍스트 변환 추론(GPU) -> 4. Parser 로봇명령 JSON 치환(Rule) -> 5. 최종 응답
    """
    try:
        # 1. 업로드 오디오 스트림 바이너리로 수신 (비동기 await 로 서버 블로킹 방지)
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="audio file is empty")

        # 2. 오디오 로드 및 전처리 구문 호출 (16kHz 행렬로 변환)
        audio_input = load_audio_from_upload_bytes(audio_bytes, audio.filename)
        
        # 3. Whisper 전처리 로직 (소리 파동 자체를 형태소적 의미가 담긴 '조각 텐서'로 스펙트로그램화 변환)
        inputs = processor(
            audio_input,
            sampling_rate=16000,
            return_tensors="pt",
            return_attention_mask=True,
        )
        # 준비된 특징 재료 배열을 GPU 쪽 창고 램(VRAM)으로 위탁배송
        input_features = inputs.input_features.to(device) 
        attention_mask = getattr(inputs, "attention_mask", None)
        if attention_mask is not None:
            attention_mask = attention_mask.to(device)
        
        # 모델 텍스트 생성 (inference_mode()로 감쌈으로써 훈련용 미분계산 기능과 메모리 할당량을 아예 잠궈버려 추론 속도를 10배 펌핑)
        with torch.inference_mode():
            predicted_ids = model.generate(
                input_features=input_features,
                attention_mask=attention_mask,
            )
            
        # 생성된 기계 토큰 넘버(숫자 뭉치 번호)들을 사람이 읽을 수 있는 유니코드 한글 글자로 일괄 역번역 및 양옆 공백 제거
        recognized_text = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0].strip()
        
        print(f"📡 [STT API] 모델 인식 결과: '{recognized_text}'")
        
        # 4. 문자열(글씨) 명령어 파싱 -> 기계 장치가 인식하는 DB 규격 JSON 오브젝트 맵으로 구문 쪼개기 변환
        parsed_json_str = parse_voice_command(recognized_text)
            
        # 5. 최종 결합 래핑 응답을 프론트/백엔드에 반환
        return {
            "status": "success",
            "recognized_text": recognized_text,          # AI가 받아적은 "인간 친화적 문장" (UI 노출용)
            "robot_command": json.loads(parsed_json_str) # 파서가 쪼갠 "기계 친화적 제어 구조물" (로봇/서버 제어용)
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        # 서버 코드 오류가 발생했을 경우 죽지 않고 500 에러를 친절히 내려보냄
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 만일 운영체제 콘솔에서 직접 이 파이썬 스크립트를 단독으로 실행(python main.py)했을 시 구동되는 Uvicorn 진입점.
    # Uvicorn은 매우 빠르고 가벼운 파이썬 전용 비동기(ASGI) 웹서버 엔진구동체입니다. (host="0.0.0.0" 옵션은 모든 외부망 접속을 허용하겠다는 뜻)
    uvicorn.run(app, host="0.0.0.0", port=9001)
