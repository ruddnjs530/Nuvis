import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import os
import json
from datetime import datetime
from pathlib import Path

# ==============================================================================
# [교육용 주석] 1. 시계열 데이터셋 클래스 (PyTorch Dataset)
# ==============================================================================
# 이 클래스의 역할: 원본 데이터(JSON, CSV)를 읽어와서 PyTorch 인공지능 모델이 학습할 수 있는 
# 숫자 배열(Tensor) 형태로 전처리(Preprocessing)하고 잘라서 반환해줍니다.
class SensorDataset(torch.utils.data.Dataset):
    def __init__(self, data_file, sequence_length=10):
        # JSON 또는 CSV 포맷에 맞춰 데이터를 Pandas DataFrame으로 로드합니다.
        if data_file.endswith('.json'):
            with open(data_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            df = pd.DataFrame(raw_data['sensor_data'])
        else:
            df = pd.read_csv(data_file)
            
        # ─────────────────────────────────────────
        # 특징 공학 (Feature Engineering)
        # ─────────────────────────────────────────
        # 인공지능 모델이 학습을 더 잘하게 만들기 위해 기본 데이터에서 파생 변수를 만들어내는 과정입니다.
        
        # 1. 시계열 특징 추출: 문자열로 된 날짜를 분석에 용이한 파이썬 날짜 객체로 변환한 뒤 '시간(hour)'만 뽑아냅니다.
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        
        # 2. 주기적 인코딩 (Sin/Cos Encoding)
        # 시간은 23시 다음이 다시 0시로 이어집니다. 하지만 단순 숫자 23과 0은 컴퓨터 입장에서 매우 멀리 떨어져 있습니다.
        # 이를 원형(Circle) 데이터로 만들어 23시와 0시가 수학적으로 인접하게 인식하도록 Sin/Cos로 삼각함수 변환합니다.
        df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # 3. 입력 피처(독립변수, X) 및 타겟(종속변수, y) 설정
        self.feature_cols = ['temperature', 'humidity', 'fine_dust', 'sin_hour', 'cos_hour']
        self.target_cols = ['air_purifier_on', 'humidifier_on', 'dehumidifier_on'] # 우리가 예측해야 할 3가지 기기 동작 여부
        
        # 스케일링 (정규화)
        # 데이터의 단위가 다르면(예: 온도는 20도, 미세먼지는 100 이상) 수치가 큰 데이터에만 모델이 과하게 영향을 받을 수 있습니다.
        # 이 크기 차이가 학습을 방해하지 않도록 값의 분포를 동일한 스케일(평균 0, 표준편차 1)로 
        # 맞추는 작업이 바로 스케일링(StandardScaler)입니다.
        self.scaler = StandardScaler()
        self.data = self.scaler.fit_transform(df[self.feature_cols].astype(float))
        self.targets = df[self.target_cols].values # 기기가 켜졌는지(1) 꺼졌는지(0)
        self.seq_len = sequence_length # 몇 개의 과거 데이터를 보고 미래를 예측할지 (예: 과거 12칸=6시간)
        
    def __len__(self):
        # 학습에 쓰일 수 있는 데이터 묶음의 총 개수를 반환합니다.
        # 시퀀스 길이만큼은 과거 데이터를 모아야 하므로 그 길이만큼을 전체 데이터 수에서 빼줍니다.
        return len(self.data) - self.seq_len
        
    def __getitem__(self, idx):
        # 실제로 DataLoader(PyTorch 유틸)가 훈련 데이터 조각을 요구할 때 즉시(Just in time) 호출되는 함수입니다.
        # idx 위치부터 시퀀스 길이(seq_len) 만큼을 범위로 잘라서 X를 만들고, 바로 그 다음 시점의 정답을 찾아 y로 꺼냅니다.
        x = self.data[idx : idx + self.seq_len]
        y = self.targets[idx + self.seq_len]
        # PyTorch에서 사용하는 자료형인 텐서(FloatTensor)로 변환하여 리턴합니다.
        return torch.FloatTensor(x), torch.FloatTensor(y)

# ==============================================================================
# [교육용 주석] 2. LSTM 모델 구조 (다중 라벨 분류)
# ==============================================================================
# LSTM(Long Short-Term Memory)은 RNN(순환신경망)의 한 종류로, 과거 시점의 데이터를 장/단기적으로 기억하여 
# 시계열 예측(주식, 온도 변화, 사용자 패턴 등)을 하기에 가장 보편적이고 좋은 인공지능 모델입니다.
class DevicePredictorLSTM(nn.Module):
    def __init__(self, input_size=5, hidden_size=64, num_layers=2, output_size=3):
        super(DevicePredictorLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM 계층:
        # batch_first=True: 데이터 형태를 [배치 크기, 시퀀스 길이, 피처 개수] 로 맞추기 위함입니다.
        # dropout=0.2: 과적합(Overfitting, 훈련셋만 정답을 외우고 실제 테스트에선 대응을 못하는 현상)을 방지하기 위해 
        #              신경망 뇌세포(노드)의 20%를 무작위로 끄면서 학습합니다.
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        
        # Fully Connected Layer (분류기): 
        # LSTM에서 학습된 특징 벡터(hidden_size, 여기선 64개)를 우리가 원하는 결과 개수(output_size, 즉 3개 기기)로 변환해주는 역할을 합니다.
        self.fc = nn.Linear(hidden_size, output_size)
        
        # Sigmoid 함수: 
        # 신경망의 출력이 어떤 숫자가 나오든 0.0 ~ 1.0 사이의 '확률 값'이 되도록 찌그러뜨립(S자 곡선)니다. 0.5 이상이면 기기를 켠다고 판단할 것입니다.
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        # 학습/추론 할 때 데이터가 어떻게 흘러가는지(순전파) 정의하는 부분입니다.
        
        # 초기 Hidden State(단기기억 공간)와 Cell State(장기기억 공간) 배열을 전부 0으로 만들어서 모델에 세팅합니다.
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        # out[:, -1, :]의 의미: 과거 시퀀스들 중 맨 마지막 시점(-1)의 결과만 꺼내서 최종 예측에 사용한다는 의미입니다 (모든 과거 요약 정보).
        out = self.fc(out[:, -1, :])
        return self.sigmoid(out)

# ==============================================================================
# [교육용 주석] 3. 학습용 메인 함수 (훈련 파이프라인)
# ==============================================================================
def train_lstm_on_gpu(data_file=None):
    if data_file is None:
        # recommendation/data/mock_payload.json 을 기본 학습 데이터 경로로 사용합니다.
        data_file = str(Path(__file__).resolve().parent.parent / "data" / "mock_payload.json")
    
    # GPU(CUDA)가 사용 가능하면 GPU 속도를 누리고, 없으면 일반 코어 CPU를 사용하도록 자동 세팅합니다.
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Using Device: {device}")
    
    # 학습할 데이터 파일이 없으면 기존 작성했던 데이터 생성 스크립트를 즉석으로 호출해서 만들어냅니다.
    if not os.path.exists(data_file):
        print(f"[경고] {data_file}가 없습니다. 머크 데이터를 먼저 생성합니다.")
        from generate_mock_data import generate_mock_json_payload
        generate_mock_json_payload(data_file)

    # 데이터 로드 (시퀀스 길이 12 = 30분 단위 데이터 기준으로 6시간 동안 쭉 일어난 날씨/가전 변화의 흐름을 하나의 입력 샘플로 봅니다.)
    dataset = SensorDataset(data_file, sequence_length=12)
    
    # DataLoader: 대용량 배열에서 데이터를 batch_size(32개)씩 묶고, 
    # 데이터 순서를 무작위로 섞은 후(Shuffle=True), 조금씩 모델에 꾸준히 넘겨주는 유틸리티입니다.
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)
    
    # 모델을 생성하고 방금 찾은 장비(GPU/CPU) 메모리에 통째로 올려줍니다 (.to(device))
    model = DevicePredictorLSTM(input_size=len(dataset.feature_cols), output_size=len(dataset.target_cols)).to(device)
    
    # criterion(손실 함수) = 모델이 틀린 정도를 수학적 공식으로 점수화하는 역할을 합니다. 낮을수록 좋은 것입니다.
    # BCELoss(Binary Cross Entropy Loss): 기기가 커질지(1), 안켜질지(0)를 맞추는 이진 분류 확률 문제에서 가장 널리 쓰이는 채점 방식.
    criterion = nn.BCELoss()
    
    # optimizer(최적화 알고리즘) = Adam. 
    # 모델의 정답(파라미터 가중치)을 어떤 방향으로 얼마나 고칠지 판단하는 아주 똑똑한 내비게이터입니다. (lr은 보폭을 뜻하는 학습률)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    print(f"[정보] 학습 시작... (Features: {dataset.feature_cols})")
    
    model.train() # 모델을 "훈련 모드"로 바꿉니다. (훈련 상황이어야 Dropout 등의 보조 기능들이 켜져서 동작함)
    for epoch in range(10): # 전체 훈련 데이터를 처음부터 끝까지 총 10번 반복해서 암기(Epoch) 시킵니다.
        total_loss = 0
        for x_batch, y_batch in dataloader:
            # 훈련할 조각들을 장비(GPU/CPU)에 올림
            x_batch, y_batch = x_batch.to(device), y_batch.to(device)
            
            # 아래 5줄이 딥러닝에서 '학습을 1스텝 수행' 하는데 있어 가장 핵심 프로세스, 일명 Training Loop 입니다.
            optimizer.zero_grad()       # 0. 기존 루프에서 계산했던 그라디언트(순간 변화율, 미분값) 찌꺼기 초기화(리셋)
            outputs = model(x_batch)    # 1. 인공지능이 예측을 시도해봄 (Forward 단계)
            loss = criterion(outputs, y_batch) # 2. 예측결과와 실제 정답을 채점해서 오차(Loss)가 얼마나 났는지 체크함
            loss.backward()             # 3. 그 오차의 책임을 소급해서 추적해 모델 내 어느 부분의 수식을 손봐야할지 미분을 역으로 계산함 (Backward 과정)
            optimizer.step()            # 4. 위에서 찾은 책임을 토대로 모델의 가중치(뇌 세포들의 결합세력)를 실제로 수정 업데이트 반영함
            
            total_loss += loss.item()
            
        print(f"Epoch [{epoch+1}/10], Avg Loss: {total_loss/len(dataloader):.4f}")
        
    # 모델 저장 (추후 FAST API 등 웹 어플리케이션에서 방금 학습된 이 똑똑한 뇌를 다시 로드해서 써먹을 수 있도록 .pth 파일로 물리디스크화 시킵니다)
    save_path = os.path.join(os.path.dirname(__file__), "model", "lstm_device_model.pth")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 모델의 '뼈대 구조에 배치된 숫자 가중치(state_dict)' 뿐만 아니라, 
    # 피처의 순서, 스케일러(Scale 룰) 등 API 측에서 데이터 추론 시 맞춰야 하는 온갖 재료들을 파이썬 dict 형태로 묶어서 한 번에 덤프 뜹니다.
    torch.save({
        'model_state_dict': model.state_dict(),
        'feature_cols': dataset.feature_cols,
        'target_cols': dataset.target_cols,
        'scaler': dataset.scaler
    }, save_path)
    print(f"✅ 모델 저장 완료: {save_path}")

if __name__ == "__main__":
    train_lstm_on_gpu()
