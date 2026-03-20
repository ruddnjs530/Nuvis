import os
import shutil
import torch
import numpy as np
import librosa
from fastapi import FastAPI, UploadFile, File, HTTPException
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from stt_parser import DEFAULT_ROOM_MAP, get_room_map, parse_voice_command, set_room_map
import json
from pathlib import Path
import requests

# GPU 설정
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "5"
device = "cuda" if torch.cuda.is_available() else "cpu"

# ─────────────────────────────────────────
# 모델 경로 설정
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent
SHARED_ENV_PATH = PROJECT_DIR / "docs" / "shared" / ".env"
MODEL_V2 = BASE_DIR / "model" / "v2_full"
MODEL_V1 = BASE_DIR / "model" / "whisper-smarthome"
BASE_MODEL = "openai/whisper-small"
ROOM_NAME_ENDPOINT = "/api/room/name"

# 우선순위: v2_full -> whisper-smarthome -> base
if MODEL_V2.exists():
    MODEL_PATH = str(MODEL_V2)
    print(f"🔥 Loading Fine-tuned Model V2: {MODEL_PATH}")
elif MODEL_V1.exists():
    MODEL_PATH = str(MODEL_V1)
    print(f"🔥 Loading Fine-tuned Model V1: {MODEL_PATH}")
else:
    MODEL_PATH = BASE_MODEL
    print(f"📡 Loading Base Model: {MODEL_PATH}")

# 모델 및 프로세서 로드
try:
    processor = WhisperProcessor.from_pretrained(MODEL_PATH)
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_PATH).to(device)
    model.config.forced_decoder_ids = None
    print("✅ Model & Processor loaded successfully!")
except Exception as e:
    print(f"❌ Model load failed: {e}")
    exit(1)


def load_shared_env_file() -> None:
    if not SHARED_ENV_PATH.exists():
        return

    with SHARED_ENV_PATH.open("r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def get_backend_base_url() -> str | None:
    load_shared_env_file()

    for env_key in ("BACKEND_BASE_URL", "BACKEND_API_BASE_URL"):
        value = os.getenv(env_key)
        if value:
            return value.rstrip("/")

    return None


def normalize_room_name_payload(payload) -> list[dict]:
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("data", "rooms", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return value

    raise ValueError("room name API response format is invalid")


def fetch_room_map_from_backend() -> dict:
    backend_base_url = get_backend_base_url()
    if not backend_base_url:
        raise ValueError("BACKEND_BASE_URL is not configured")

    url = f"{backend_base_url}{ROOM_NAME_ENDPOINT}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()

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
    try:
        room_map = fetch_room_map_from_backend()
        set_room_map(room_map)
        print(f"✅ Room map loaded from backend: {get_room_map()}")
    except Exception as e:
        set_room_map(DEFAULT_ROOM_MAP)
        print(f"⚠️ Failed to load room map from backend: {e}")
        print(f"⚠️ Falling back to default room map: {get_room_map()}")


app = FastAPI(title="Smart Home AI STT API (Fine-tuned)")


@app.on_event("startup")
async def on_startup() -> None:
    initialize_room_map()

@app.post("/api/stt/transcribe")
async def transcribe_audio_api(audio: UploadFile = File(...)):
    temp_file_path = None

    try:
        # 1. 파일 임시 저장
        temp_file_path = f"temp_{audio.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
        # 2. 오디오 로드 및 전처리 (16kHz 변환 포함)
        audio_input, _ = librosa.load(temp_file_path, sr=16000)
        
        # 3. Whisper 추론
        input_features = processor(audio_input, sampling_rate=16000, return_tensors="pt").input_features.to(device)
        
        # 모델 생성 (힌트 주입 대신 파인튜닝 자체의 성능 활용)
        predicted_ids = model.generate(input_features, language="korean", task="transcribe")
        recognized_text = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0].strip()
        
        print(f"📡 [STT API] 인식 결과: '{recognized_text}'")
        
        # 4. 명령어 파싱
        parsed_json_str = parse_voice_command(recognized_text)
        
        # 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        return {
            "status": "success",
            "recognized_text": recognized_text,
            "robot_command": json.loads(parsed_json_str) 
        }

    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
