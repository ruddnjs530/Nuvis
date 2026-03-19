import os
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "5"

from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import whisper
import json
from stt_parser import parse_voice_command

app = FastAPI(title="Smart Home AI STT API")

# Whisper 모델 로드 (앱 시작 시 한 번만 메모리(GPU)에 올림)
print("Loading Whisper model 'base' on GPU (Visible device 5)...")
model = whisper.load_model("base", device="cuda")
print("✅ Whisper Model loaded successfully!")

@app.post("/api/stt/transcribe")
async def transcribe_audio_api(audio: UploadFile = File(...)):
    """
    클라이언트에서 보낸 오디오 파일을 받아 STT 변환 및 파싱된 JSON 제어 명령을 반환합니다.
    """
    try:
        # 1. 클라이언트가 보낸 음성 파일을 임시 저장
        temp_file_path = f"temp_{audio.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
        print(f"📡 [STT API] 오디오 수신 변환 시작: {temp_file_path}")
            
        # 2. Whisper 모델로 텍스트 변환 (한국어 강제 지정 및 힌트 주입)
        prompt_words = "거실, 안방, 침실, 주방, 공기청정기, 가습기, 제습기, 작동, 꺼줄래, 켜지마, 말고, 아니"
        result = model.transcribe(temp_file_path, language="ko", initial_prompt=prompt_words)
        recognized_text = result["text"].strip()
        
        # 3. 로봇 파싱 로직 태우기!
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
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 추천 API(8000)와 겹치지 않게 STT 서버는 8001 포트 사용
    uvicorn.run(app, host="0.0.0.0", port=8001)
