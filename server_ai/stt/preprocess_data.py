"""
AI Hub 카투홈(Car2Home) 데이터셋 전처리 스크립트
- WAV 파일: 48kHz → 16kHz 변환
- JSON 라벨: LabelText 추출
- 최종 출력: processed/ 폴더 + metadata.csv
"""

import os
import json
import csv
import shutil
from pathlib import Path

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"          # stt/data/ 경로
OUTPUT_DIR = Path(__file__).parent / "data" / "processed"  # 출력 경로
OUTPUT_WAV_DIR = OUTPUT_DIR / "audio"              # 변환된 WAV 저장
METADATA_PATH = OUTPUT_DIR / "metadata.csv"        # 최종 학습 메타데이터
TARGET_SR = 16000                                  # Whisper 요구 샘플링레이트

# ─────────────────────────────────────────
# 라이브러리 임포트
# ─────────────────────────────────────────
try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("[경고] librosa/soundfile 미설치. 설치 명령어: pip install librosa soundfile")

def convert_wav(src_path: Path, dst_path: Path, target_sr: int = 16000) -> bool:
    """WAV 파일을 target_sr(16kHz)로 변환하여 저장"""
    try:
        audio, sr = librosa.load(src_path, sr=target_sr, mono=True)
        sf.write(dst_path, audio, target_sr)
        return True
    except Exception as e:
        print(f"  [오류] {src_path.name}: {e}")
        return False

def extract_label(json_path: Path) -> str | None:
    """JSON 파일에서 전사텍스트(LabelText) 추출"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("전사정보", {}).get("LabelText", "").strip()
        quality = data.get("기타정보", {}).get("QualityStatus", "")
        # 품질이 Good인 것만 사용
        if quality != "Good":
            return None
        return text if text else None
    except Exception as e:
        print(f"  [오류] JSON 파싱 실패 {json_path.name}: {e}")
        return None

def run():
    if not LIBROSA_AVAILABLE:
        print("librosa와 soundfile을 먼저 설치해주세요:")
        print("  pip install librosa soundfile")
        return

    # 출력 폴더 생성
    OUTPUT_WAV_DIR.mkdir(parents=True, exist_ok=True)

    # 전체 JSON 파일 수집
    json_files = sorted(DATA_DIR.rglob("*.json"))
    print(f"[정보] 발견된 JSON 파일 수: {len(json_files)}")

    success, skipped = 0, 0
    rows = []  # (audio_path, text) 리스트

    for json_path in json_files:
        # 라벨 추출
        text = extract_label(json_path)
        if not text:
            skipped += 1
            continue

        # 대응하는 WAV 파일 경로
        wav_path = json_path.with_suffix(".wav")
        if not wav_path.exists():
            print(f"  [경고] WAV 없음: {wav_path.name}")
            skipped += 1
            continue

        # 변환된 WAV 저장 경로
        out_wav_path = OUTPUT_WAV_DIR / wav_path.name

        # 이미 변환된 파일 스킵
        if out_wav_path.exists():
            rows.append((str(out_wav_path), text))
            success += 1
            continue

        # 48kHz → 16kHz 변환
        if convert_wav(wav_path, out_wav_path, TARGET_SR):
            rows.append((str(out_wav_path), text))
            success += 1
            if success % 100 == 0:
                print(f"  진행중: {success}개 완료...")
        else:
            skipped += 1

    # metadata.csv 저장
    with open(METADATA_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["audio_path", "text"])
        writer.writerows(rows)

    print(f"\n[완료] 성공: {success}개 / 스킵: {skipped}개")
    print(f"[완료] 메타데이터 저장: {METADATA_PATH}")
    print(f"[완료] 변환된 WAV 저장: {OUTPUT_WAV_DIR}")

if __name__ == "__main__":
    run()
