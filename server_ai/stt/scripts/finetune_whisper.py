"""
==============================================================================
[교육용 주석] Whisper 모델 파인튜닝 (Fine-Tuning) 스크립트
==============================================================================
목적: 이미 세상의 언어를 수만 시간 학습해둔 OpenAI의 거대 AI 음성인식기인 "Whisper" 뇌스펙을 베이스로,
      방금 전처리한 우리 앱의 특화된 도메인(Smart Home 공간의 억양과 고유명사)들을 
      조금 더 똑똑하고 정교하게 알아듣도록 맞춤교육(파인튜닝)을 시키는 메인 스크립트입니다.

학습 방식(설계 전략):
- 전이 학습(Transfer Learning): 바닥부터 가르치지 않고, 기존 천재 뇌(openai/whisper-small)를 그대로 가져와 부족한 부분만 채웁니다.
- HuggingFace Transformers: 가장 대중적이고 쉬운 최신 자연어처리/음성 딥러닝 프레임워크 도구입니다.
- 운영체제 안전 철학: 이 코드는 GPU/멀티프로세싱 간 충돌(Deadlock, 무한 대기 현상)을 원천 차단하기 위해
                     HuggingFace 자체의 복잡한 map 도구를 무시하고, 직관적인 파이토치(PyTorch) 기본 Dataset 구조를 직접 설계해 씁니다.
==============================================================================
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
    WhisperProcessor,               # 1. 오디오 파형 전처리 규칙 + 텍스트를 숫자로 바꾸는 녀석
    WhisperForConditionalGeneration,# 2. Whisper 모델 본체 (가중치가 들어있는 AI 뇌)
    Seq2SeqTrainer,                 # 3. 입력과 출력이 다를 때(오디오->텍스트), 정답을 맞추는 채점/훈련 루프를 알아서 다 돌려주는 매니저 객체
    Seq2SeqTrainingArguments,       # 4. 몇 번 공부할지, 학습 환경(하이퍼파라미터) 세팅 지시서
)

# 토크나이저 병렬처리가 다른 PyTorch 스레드와 겹쳐서 컨테이너가 멈추는 버그를 방지하는 강제 안전 스위치
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ─────────────────────────────────────────
# 설정값 (하이퍼파라미터 - Hyper parameters)
# 자동차 튜닝의 부품값처럼, 머신러닝의 성능과 자원 점유도를 결정짓는 핵심 계기판들입니다.
# ─────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
METADATA_PATH = BASE_DIR / "data" / "processed" / "metadata.csv" # 정답지가 들어간 요약본 지표
MODEL_OUTPUT  = BASE_DIR / "model" / "v2_full"                   # 학습이 끝난 나만의 똑똑해진 파일들이 구워질 저장 폴더

MODEL_NAME    = "openai/whisper-small" # 기초 뼈대로 삼을 모델 크기. tiny, base, small, medium, large 중에서 GPU 성능 대비 정확도 효율이 좋은 small 채택
LANGUAGE      = "Korean"
TASK          = "transcribe" # translate(한국어 -> 영어 번역 출력) 모드가 아니라, 들은 그대로 받아적기만 하는(transcribe) 모드
SAMPLING_RATE = 16000

TRAIN_RATIO   = 0.9      # 전체 데이터가 100개면, 90개는 공부하는 데 쓰고, 10개는 모의고사 치는 데(검증) 쓰겠다는 비율
MAX_STEPS     = 10000    # 모델 뇌신경 구조망(가중치)을 수정 반영(Step)하는 행위를 최대 1만 번을 수행하겠음
BATCH_SIZE    = 8        # 한 번에 GPU 메모리에 올려서 동시 채점/공부시킬 오디오 파일 묶음 갯수 (메모리가 OOM으로 터지면 이 값을 4나 2로 줄여야 함)
LEARNING_RATE = 1e-5     # 학습률(보폭 넓이). 파인튜닝은 이미 기초가 잡힌 뇌를 고치는 것이므로 매우 조심스럽고 미세한 보폭(0.00001)으로 걷습니다.
WARMUP_STEPS  = 100      # 학습 극초반 100번은 처음부터 확 달리지 않고 보폭을 천천히 늘려가며 수식이 무너지는 것(발산)을 막는 웜업 운동 단계.
SAVE_STEPS    = 200      # 가다가 터질 수 있으니 200번 문제 풀때마다 중간 세이브 지점(Checkpoint)을 생성함
EVAL_STEPS    = 200      # 200번 마다 남겨둔 10%의 검증 데이터로 채점을 치룸

# ─────────────────────────────────────────
# 1. PyTorch Custom Dataset (딥러닝 공장 컨베이어 벨트 역할)
# ─────────────────────────────────────────
# 딥러닝 훈련 루프 내에서, 원본 오디오 파일 덩어리를 어떻게 까서(Read), 
# 인공지능이 계산하기 편한 숫자로 변환하고(Feature Extractor), 정답 텍스트를 정답 번호로 치환할지(Tokenizer) 정의한 거푸집입니다.
class SmartHomeAudioDataset(Dataset):
    def __init__(self, rows: list, processor: WhisperProcessor):
        self.rows = rows
        self.processor = processor

    def __len__(self):
        # AI가 "데이터 총 몇개 남았어?" 물어볼 때 답하는 용도
        return len(self.rows)

    def __getitem__(self, idx):
        # AI가 훈련루프에서 "다음 데이터 하나 꺼내줘!" 라고 할 때 그 순간순간(Just In time) 동작하게 되는 코드
        audio_path, text = self.rows[idx]

        # 물리적 WAV 파일을 파이썬 숫자 배열로 엶
        audio_array, sr = sf.read(audio_path)
        if audio_array.ndim > 1: # 혹시 2채널(스테레오)이면 1채널(모노)로 강제 합침 계산
            audio_array = audio_array.mean(axis=1)
        audio_array = audio_array.astype(np.float32)

        # <핵심 부분 A: 음성 전처리>
        # 복잡한 오디오 파형 곡선을, AI가 눈으로 보기 펀한 그림판 형태인 "멜 스펙트로그램(Mel spectrogram, 주파수 분포도)" 패턴 숫자로 바꿈
        input_features = self.processor.feature_extractor(
            audio_array, sampling_rate=SAMPLING_RATE
        ).input_features[0]

        # <핵심 부분 B: 텍스트 정답 토크나이징>
        # "불 켜줘" 라는 사람 글씨를 잘라 사전에 등록된 각 단어 고유의 ID(숫자) 목차로 변형함
        labels = self.processor.tokenizer(text).input_ids

        # 최종적으로 컨베이어 벨트 위로 올려주는 데이터 패키지 (텐서 폼)
        return {
            "input_features": torch.tensor(input_features, dtype=torch.float32),
            "labels": torch.tensor(labels, dtype=torch.long),
        }

def load_rows(csv_path: Path) -> list:
    """전처리 단계에서 예쁘게 만들어둔 CSV를 통째로 파이썬 배열로 변환합니다."""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f) # 엑셀 머릿글을 키값으로 쓰는 편리한 DictReader
        for row in reader:
            if os.path.exists(row["audio_path"]):
                rows.append((row["audio_path"], row["text"]))
    print(f"[정보] 로드된 데이터 수: {len(rows)}개")
    return rows

# ─────────────────────────────────────────
# 2. 데이터 콜레이터 (Data Collator - 행렬 패딩 처리 보좌관)
# ─────────────────────────────────────────
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """
    이런 문제가 있습니다. 딥러닝 GPU 연산은 무조건 모든 데이터의 길이가 동일한 '네모 반듯한 직사각형 행렬' 모양이어야만 동시 처리가 가능합니다.
    하지만 어떤 음성은 2초, 어떤 음성은 5초 등 말하는 길이가 들쭉날쭉합니다.
    Collator는 이번 Batch 단위에 잡힌 데이터들 중 '가장 길이가 긴 데이터'에 맞춰 모자란 친구들 빈 공간에 'Padding(의미없는 더미 0값)'을 채워넣어
    억지로 네모 반듯하게 줄을 쫙 맞춰주는 필수 도우미입니다.
    """
    processor: Any

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]):
        # 음성 입력 데이터에 빈칸(0 패딩) 끼워넣기 작업
        input_features = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(
            input_features, return_tensors="pt"
        )

        # 텍스트 결과 답안지에도 글자수 맞추기 0 패딩을 넣는데, 
        # 음성과 다르게 인공지능이 "아 여기는 정답이 아니라 빈칸 채운곳이니 오답노트에서 아예 무시해"(-100 마킹) 라고 알아들을 수 있게 처리합니다.
        label_features = [{"input_ids": f["labels"].tolist()} for f in features]
        labels_batch = self.processor.tokenizer.pad(
            label_features, return_tensors="pt"
        )
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )
        
        # 모델 구조에 따라 시작 태그(BOS: Begin Of Sentence)가 겹치는 걸 걷어내는 내부 보강 처리
        if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
            labels = labels[:, 1:]
        batch["labels"] = labels
        return batch

# ─────────────────────────────────────────
# 3. 평가 지표 (CER - 글자 단위 오류율 채점 로직)
# ─────────────────────────────────────────
def make_compute_metrics(processor):
    """
    AI가 모의고사 1건을 치를 때마다, 찐 정답지와 AI의 대답을 수치적으로 비교하는 자동 채점기.
    CER(Character Error Rate): [전체 정답 글자수 대비 글자 1자가 틀렸거나/빠졌거나/더들어갔을 때]를 종합해 감점합니다.
    (따라서 점수가 0%에 가까울수록 오타 없이 완벽한 정답에 가까움을 증명하는 지표입니다.)
    """
    cer_metric = evaluate.load("cer")

    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        # 아까 무시하라고 표기한 마커(-100)를 원상복구 시켜줌 (그래야 텍스트로 치환할 때 에러가 안남)
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        
        # 숫자(Token Ids 배열)로 되어있는 정답지와 제출답안을 사람이 읽을 수 있는 유니코드 텍스트 문자열로 역번역
        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)
        
        # 텍스트끼리 매치 스토리를 돌려서 점수(CER) 도출
        cer = cer_metric.compute(predictions=pred_str, references=label_str)
        return {"cer": round(cer, 4)}

    return compute_metrics

# ─────────────────────────────────────────
# 4. 메인 실행 (전체 조율 및 수행 절차)
# ─────────────────────────────────────────
def main():
    print("=" * 50)
    print("Whisper 파인튜닝 시작 (스마트홈 도메인)")
    print("=" * 50)

    # 1. 서버 하드웨어 스펙 및 장비 감지
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[정보] 사용 디바이스: {device}")
    if device == "cuda":
        print(f"[정보] GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("[경고] GPU 미감지! CPU로는 학습이 수십일이 걸릴 수 있습니다.")

    # 2. 베이스 모델 및 프로세서(수리기/번역기) 인터넷 뚝배기에서 다운로드 (또는 서버의 캐시에서 가져옴)
    print(f"[정보] 모델 로드 중: {MODEL_NAME}")
    processor = WhisperProcessor.from_pretrained(MODEL_NAME, language=LANGUAGE, task=TASK)
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
    
    # 억지로 다른 언어로 예측이 빠지지(환각 증세) 않도록 강제로 한국어로만 내뱉게 환경 고정 세팅 
    model.generation_config.language = LANGUAGE.lower()
    model.generation_config.task = TASK
    model.generation_config.forced_decoder_ids = None

    # 3. 데이터 로딩 파트
    print("[정보] 데이터 로드 중...")
    rows = load_rows(METADATA_PATH)

    # 전체를 학습용 90%, 검증용(모의고사용) 10% 비율로 나눕니다.
    n_train = int(len(rows) * TRAIN_RATIO)
    n_val = len(rows) - n_train
    train_rows = rows[:n_train]
    val_rows = rows[n_train:]
    print(f"[정보] 학습: {len(train_rows)}개 / 검증: {len(val_rows)}개")

    train_dataset = SmartHomeAudioDataset(train_rows, processor)
    val_dataset = SmartHomeAudioDataset(val_rows, processor)

    # 실제 학습이 돌기 전, 혹시 데이터 코드가 깨지는 지 확인을 위해 안전하게 첫 데이터 1개만 돌려봄 (디버그 성)
    print("[정보] 첫 번째 샘플 로드 테스트...")
    sample = train_dataset[0]
    print(f"[정보] input_features shape: {sample['input_features'].shape}")
    print(f"[정보] labels length: {len(sample['labels'])}")
    print("[정보] 테스트 통과! 학습 시작을 준비합니다.")

    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)
    compute_metrics = make_compute_metrics(processor)

    # 4. 훈련 종합 설정 포장 단계 (TrainingArguments)
    MODEL_OUTPUT.mkdir(parents=True, exist_ok=True)
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(MODEL_OUTPUT),
        max_steps=MAX_STEPS,                 # 전체 몇 걸음 훈련 달릴 돌지
        per_device_train_batch_size=BATCH_SIZE, # 한번에 넣을 오디오 개수
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=1,       # 메모리 부족 시 BATCH_SIZE는 2로 내리고 이걸 4로 올려서 곱하기=8 로 대체 구성가능한 스킬 속성
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        fp16=torch.cuda.is_available(),      # 메모리와 연산속도 뻥튀기를 위해 부동소수점 단위를 32bit-> 16bit로 압축시킬지(Half Precision) 여부
        eval_strategy="steps",
        eval_steps=EVAL_STEPS,
        save_steps=SAVE_STEPS,
        logging_steps=50,
        save_total_limit=2,                  # 서버 용량 디스크 꽉참을 방지하기 위해 과거 체크포인트는 최근 2개까지만 보관하고 알아서 날림
        load_best_model_at_end=True,         # 학습을 다 마쳤을 때 무조건 마지막 게 아니라, CER 점수가 제일 찬란하게 좋았던 시점의 뇌 상태를 복원시킴
        metric_for_best_model="cer",
        greater_is_better=False,             # 윗줄의 CER점수는 오답률이므로 낮을수록(False) 좋은 것임을 인지시킴
        predict_with_generate=True,
        generation_max_length=225,           # 아무리 말이 길어도 출력 텍스트 길이를 최대 225자로 제한시킴. 
        report_to="none",                    # WandB 등의 외부 분석 대시보드로 로그 데이터를 안보냄
        dataloader_num_workers=0,            # 윈도우/컨테이너 데드락 방지용으로 파이썬 멀티코어 처리를 완전 봉쇄 (속도는 조금 참아야함)
    )

    # 5. Trainer 인스턴스: 위에 선언한 모든 꼬리표 조건(모델+데이터+채점기+옵션)들을 이 트레이너 매니저한테 다 때려넣으면 알아서 복잡한 미분과 병렬처리를 돌림
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
    # 약 몇 시간 ~ 며칠이 소요되는 거대한 메인 머신러닝 연산 구문 
    trainer.train()

    # 학습 완전 완료 후, 가장 똑똑해진 최종 결과물 덩어리들을 물리적인 하드 디스크 파일(.safetensors 등)로 구워냄
    print(f"[완료] 모델 저장 중: {MODEL_OUTPUT}")
    trainer.save_model(str(MODEL_OUTPUT))
    processor.save_pretrained(str(MODEL_OUTPUT))
    print("[완료] 파인튜닝 완료!")

if __name__ == "__main__":
    main()
