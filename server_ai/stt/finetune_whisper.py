"""
Whisper 파인튜닝 스크립트 (Korean Smart Home Domain Adaptation)
- 데이터: AI Hub 카투홈 데이터셋 (metadata.csv)
- 모델: openai/whisper-small (한국어 지원)
- 방식: HuggingFace datasets.map() 없이 PyTorch Dataset 직접 사용 (데드락 방지)
- 출력: stt/model/whisper-smarthome 폴더에 파인튜닝 모델 저장

[필수 설치]
pip install transformers accelerate evaluate jiwer soundfile
"""

import csv
import os
import torch
import numpy as np
import soundfile as sf
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import evaluate
from torch.utils.data import Dataset, DataLoader, random_split
from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ─────────────────────────────────────────
# 설정값 (필요 시 수정)
# ─────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
METADATA_PATH = BASE_DIR / "data" / "processed" / "metadata.csv"
MODEL_OUTPUT  = BASE_DIR / "model" / "whisper-smarthome"

MODEL_NAME    = "openai/whisper-small"
LANGUAGE      = "Korean"
TASK          = "transcribe"
SAMPLING_RATE = 16000

TRAIN_RATIO   = 0.9
MAX_STEPS     = 1000
BATCH_SIZE    = 8
LEARNING_RATE = 1e-5
WARMUP_STEPS  = 100
SAVE_STEPS    = 200
EVAL_STEPS    = 200


# ─────────────────────────────────────────
# 1. PyTorch Dataset (map() 없이 직접 로드)
# ─────────────────────────────────────────
class SmartHomeAudioDataset(Dataset):
    """metadata.csv를 읽어 (input_features, labels) 쌍을 반환하는 Dataset"""

    def __init__(self, rows: list, processor: WhisperProcessor):
        self.rows = rows
        self.processor = processor

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        audio_path, text = self.rows[idx]

        # WAV 로드 (soundfile 직접 사용)
        audio_array, sr = sf.read(audio_path)
        if audio_array.ndim > 1:
            audio_array = audio_array.mean(axis=1)
        audio_array = audio_array.astype(np.float32)

        # Whisper Feature 추출
        input_features = self.processor.feature_extractor(
            audio_array, sampling_rate=SAMPLING_RATE
        ).input_features[0]

        # 텍스트 → Token IDs
        labels = self.processor.tokenizer(text).input_ids

        return {
            "input_features": torch.tensor(input_features, dtype=torch.float32),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def load_rows(csv_path: Path) -> list:
    """metadata.csv에서 (audio_path, text) 행 목록 반환"""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if os.path.exists(row["audio_path"]):
                rows.append((row["audio_path"], row["text"]))
    print(f"[정보] 로드된 데이터 수: {len(rows)}개")
    return rows


# ─────────────────────────────────────────
# 2. 데이터 콜레이터 (패딩 처리)
# ─────────────────────────────────────────
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: Any

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]):
        input_features = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(
            input_features, return_tensors="pt"
        )

        label_features = [{"input_ids": f["labels"].tolist()} for f in features]
        labels_batch = self.processor.tokenizer.pad(
            label_features, return_tensors="pt"
        )
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )
        if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
            labels = labels[:, 1:]
        batch["labels"] = labels
        return batch


# ─────────────────────────────────────────
# 3. 평가 지표 (CER)
# ─────────────────────────────────────────
def make_compute_metrics(processor):
    cer_metric = evaluate.load("cer")

    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)
        cer = cer_metric.compute(predictions=pred_str, references=label_str)
        return {"cer": round(cer, 4)}

    return compute_metrics


# ─────────────────────────────────────────
# 4. 메인 실행
# ─────────────────────────────────────────
def main():
    print("=" * 50)
    print("Whisper 파인튜닝 시작 (스마트홈 도메인)")
    print("=" * 50)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[정보] 사용 디바이스: {device}")
    if device == "cuda":
        print(f"[정보] GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("[경고] GPU 미감지! 학습이 매우 느릴 수 있습니다.")

    # 모델 & 프로세서 로드
    print(f"[정보] 모델 로드 중: {MODEL_NAME}")
    processor = WhisperProcessor.from_pretrained(MODEL_NAME, language=LANGUAGE, task=TASK)
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
    model.generation_config.language = LANGUAGE.lower()
    model.generation_config.task = TASK
    model.generation_config.forced_decoder_ids = None

    # 데이터 로드
    print("[정보] 데이터 로드 중...")
    rows = load_rows(METADATA_PATH)

    # 학습/검증 분할
    n_train = int(len(rows) * TRAIN_RATIO)
    n_val = len(rows) - n_train
    train_rows = rows[:n_train]
    val_rows = rows[n_train:]
    print(f"[정보] 학습: {len(train_rows)}개 / 검증: {len(val_rows)}개")

    train_dataset = SmartHomeAudioDataset(train_rows, processor)
    val_dataset = SmartHomeAudioDataset(val_rows, processor)

    # 테스트: 첫 아이템 직접 로드 확인
    print("[정보] 첫 번째 샘플 로드 테스트...")
    sample = train_dataset[0]
    print(f"[정보] input_features shape: {sample['input_features'].shape}")
    print(f"[정보] labels length: {len(sample['labels'])}")
    print("[정보] 테스트 통과! 학습 시작합니다.")

    # 콜레이터 & 평가 지표
    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)
    compute_metrics = make_compute_metrics(processor)

    # 학습 설정
    MODEL_OUTPUT.mkdir(parents=True, exist_ok=True)
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(MODEL_OUTPUT),
        max_steps=MAX_STEPS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=1,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        fp16=torch.cuda.is_available(),
        eval_strategy="steps",
        eval_steps=EVAL_STEPS,
        save_steps=SAVE_STEPS,
        logging_steps=50,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="cer",
        greater_is_better=False,
        predict_with_generate=True,
        generation_max_length=225,
        report_to="none",
        dataloader_num_workers=0,   # 멀티프로세싱 완전 비활성화
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        processing_class=processor.feature_extractor,
    )

    print("[시작] 파인튜닝 학습 시작!")
    trainer.train()

    print(f"[완료] 모델 저장 중: {MODEL_OUTPUT}")
    trainer.save_model(str(MODEL_OUTPUT))
    processor.save_pretrained(str(MODEL_OUTPUT))
    print("[완료] 파인튜닝 완료!")


if __name__ == "__main__":
    main()
