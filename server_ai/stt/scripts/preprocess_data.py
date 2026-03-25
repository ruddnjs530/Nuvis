"""
==============================================================================
[교육용 주석] 음성 데이터 전처리(Preprocessing) 스크립트
==============================================================================
AI Hub에서 다운로드 받은 원본 데이터(카투홈: Car2Home 데이터셋)를
우리가 사용할 OpenAI Whisper 인공지능 모델이 무리없이 이해할 수 있도록 규격을 통일하고 
정리하는 공장식 가공 과정입니다.

주요 작업:
1. 오디오 포맷 변환: 스마트폰이나 차에서 녹음된 고해상도(48kHz) WAV 파일을
   Whisper 모델의 기본 표준 규격인 16kHz(16000Hz)로 일괄 다운스케일링(변환)합니다.
2. 정답 라벨(텍스트) 추출: 덩치 큰 JSON 속성 트리에서 실제 사람이 말한 전사 텍스트("에어컨 켜줘")만 뽑아냅니다.
3. 메인 표(metadata.csv) 생성: ['음성파일.wav 경로', '정답텍스트'] 형식의 깔끔한 데이터 엑셀표를 생성하여
   나중에 파이토치 학습기가 읽기 쉽게 만들어 줍니다.
==============================================================================
"""

import os
import json
import csv
import shutil
from pathlib import Path

# ─────────────────────────────────────────
# 1. 환경 설정 (경로 및 규격 변수)
# ─────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"                  # 원본 데이터(음성, json)가 들어있는 최상위 폴더
OUTPUT_DIR = Path(__file__).parent / "data" / "processed"  # 가공 완료된 데이터 덩어리들이 저장될 메인 폴더
OUTPUT_WAV_DIR = OUTPUT_DIR / "audio"                      # 16kHz로 변환된 새 오디오 파일들이 모일 곳
METADATA_PATH = OUTPUT_DIR / "metadata.csv"                # 변환된 WAV 파일 위치와 정답 텍스트를 함께 연결해둔 최종 인덱스 파일
TARGET_SR = 16000                                          # Whisper 모델의 필수 해상도 규격 (초당 16,000번 주파수를 쪼갬)

# 오디오 신호처리를 위한 파이썬 기초 라이브러리 체크 
# (librosa: 오디오 분석/푸리에변환의 지존, soundfile: 오디오 파일을 입출력하는 고속 드라이버)
try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("[경고] librosa/soundfile 미설치. 설치 명령어: pip install librosa soundfile")

def convert_wav(src_path: Path, dst_path: Path, target_sr: int = 16000) -> bool:
    """WAV 파일을 Whisper 표준인 16kHz로 리샘플링하여 새로 저장하는 핵심 동작 유틸"""
    try:
        # librosa.load는 원본 해상도와 관계없이 강제로 우리가 지정한 sr=16000으로 리샘플링해서 읽어옵니다. 
        # mono=True: 2채널 소리(스테레오)를 1채널 흑백음(모노)으로 강제 병합합니다. (AI는 방향성이 중요하지 않음)
        audio, sr = librosa.load(src_path, sr=target_sr, mono=True)
        # 변환이 끝난 숫자 배열(audio)을 다시 물리적인 '.wav' 파일 형태로 구워냅니다.
        sf.write(dst_path, audio, target_sr)
        return True
    except Exception as e:
        print(f"  [오류] {src_path.name}: {e}")
        return False

def extract_label(json_path: Path) -> str | None:
    """원시 JSON 파일의 깊은 뎁스(트리)를 파고 들어가서 번역에 필요한 텍스트만 쏙 빼오는 함수"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 딕셔너리의 .get(키, 기본값) 을 연쇄적으로 사용하여 값이 없더라도 에러로 뻗지 않고 안전하게 구조를 파고 들어갑니다.
        text = data.get("전사정보", {}).get("LabelText", "").strip()
        quality = data.get("기타정보", {}).get("QualityStatus", "")
        
        # 사람(데이터 검수자)이 들었을 때 발음이 뭉개지거나 노이즈가 심한(Bad) 데이터를 버리고 
        # 확실한 양질(Good)의 데이터만 남깁니다. (모델이 쓰레기를 먹고 쓰레기를 뱉는 Garbage in, Garbage out을 막기 위함)
        if quality != "Good":
            return None
            
        return text if text else None
    except Exception as e:
        print(f"  [오류] JSON 파싱 실패 {json_path.name}: {e}")
        return None

def run():
    # 실행 전 필수 라이브러리 검증
    if not LIBROSA_AVAILABLE:
        print("librosa와 soundfile을 먼저 설치해주세요:")
        print("  pip install librosa soundfile")
        return

    # 가공 데이터가 저장될 깡통 목적지 디렉토리를 미리 생성해둡니다. (리눅스의 mkdir -p 와 동일한 기능)
    OUTPUT_WAV_DIR.mkdir(parents=True, exist_ok=True)

    # DATA_DIR(data 폴더) 내에 있는 모든 하위 폴더를 거미줄처럼 재귀적으로 쑤시고 돌면서(rglob) .json 파일들을 모두 긁어 리스트화합니다.
    json_files = sorted(DATA_DIR.rglob("*.json"))
    print(f"[정보] 발견된 JSON 파일 수: {len(json_files)}")

    success, skipped = 0, 0
    rows = []  # CSV에 써넣기 위한 버퍼 메모리 [[경로문자열, "에어컨 틀어줘"], [경로문자열, "창문 닫아"], ...]

    for json_path in json_files:
        # 1. 텍스트 추출 시도 (실패 시 넘어감)
        text = extract_label(json_path)
        if not text:
            skipped += 1
            continue

        # 2. 텍스트 라벨 정보(JSON)에 대응하는 원본 오디오(WAV) 파일 찾기
        # AI Hub 데이터셋의 국룰 폴더 구조에 맞춰, "라벨링데이터" 글자를 "원천데이터" 글자로 단순 치환하여 짝꿍 오디오 파일의 경로를 유추합니다.
        wav_path = Path(str(json_path).replace("/라벨링데이터/", "/원천데이터/")).with_suffix(".wav")
        if not wav_path.exists():
            print(f"  [경고] 대응하는 원본 WAV 없음: {wav_path.name}")
            skipped += 1
            continue

        out_wav_path = OUTPUT_WAV_DIR / wav_path.name

        # 3. 반복 작업 중단 후 재개(Resume)를 위한 방어 로직: 
        # 수만개를 변환하다가 폴더가 터져도, 나중에 다시 돌렸을 때 이미 변환된건 스킵하게 냅둬서 시간 복구.
        if out_wav_path.exists():
            rows.append((str(out_wav_path), text))
            success += 1
            continue

        # 4. 오디오 변환 및 저장 (스크립트 전체에서 가장 시간이 오래 걸리는 무거운 연산 구간)
        if convert_wav(wav_path, out_wav_path, TARGET_SR):
            rows.append((str(out_wav_path), text))
            success += 1
            if success % 100 == 0:
                print(f"  진행중: {success}개 완료...")
        else:
            skipped += 1

    # 5. 최종 훈련용 색인 파일(CSV) 생성
    # 이 metadata.csv 한 장이 있어야 다음 단계인 딥러닝 훈련 단계(finetune)에서 이 거대한 데이터셋을 순차적으로 엮어 읽어들일 수 있습니다.
    with open(METADATA_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["audio_path", "text"]) # 엑셀의 헤더(첫 줄 표기 제목) 생성
        writer.writerows(rows)                  # 바디 데이터(음성-정답 매핑 테이블) 전부 다우어 쓰기

    print(f"\n[완료] 성공: {success}개 / 스킵: {skipped}개")
    print(f"[완료] 메타데이터 저장: {METADATA_PATH}")
    print(f"[완료] 변환된 WAV 저장: {OUTPUT_WAV_DIR}")

if __name__ == "__main__":
    run()
