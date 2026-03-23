import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import os
import json
from datetime import datetime
from pathlib import Path

# 1. 시계열 데이터셋 클래스 고도화
class SensorDataset(torch.utils.data.Dataset):
    def __init__(self, data_file, sequence_length=10):
        # JSON 또는 CSV 로드 지원
        if data_file.endswith('.json'):
            with open(data_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            df = pd.DataFrame(raw_data['sensor_data'])
        else:
            df = pd.read_csv(data_file)
            
        # ─────────────────────────────────────────
        # 특징 공학 (Feature Engineering)
        # ─────────────────────────────────────────
        # 1. 시계열 특징 추출
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        # df['is_weekend'] = df['timestamp'].dt.weekday >= 5  # 요일 구분 제거
        
        # 2. 주기적 인코딩 (Sin/Cos) - 23시와 0시의 인접성 보존
        df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # 3. 입력 피처 및 타겟 설정
        self.feature_cols = ['temperature', 'humidity', 'fine_dust', 'sin_hour', 'cos_hour']
        self.target_cols = ['air_purifier_on', 'humidifier_on', 'dehumidifier_on']
        
        # 스케일링
        self.scaler = StandardScaler()
        self.data = self.scaler.fit_transform(df[self.feature_cols].astype(float))
        self.targets = df[self.target_cols].values
        self.seq_len = sequence_length
        
    def __len__(self):
        return len(self.data) - self.seq_len
        
    def __getitem__(self, idx):
        x = self.data[idx : idx + self.seq_len]
        y = self.targets[idx + self.seq_len]
        return torch.FloatTensor(x), torch.FloatTensor(y)

# 2. LSTM 모델 구조 (Multi-label Output 지원)
class DevicePredictorLSTM(nn.Module):
    def __init__(self, input_size=5, hidden_size=64, num_layers=2, output_size=3):
        super(DevicePredictorLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        # 초기 Hidden State & Cell State
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        # 마지막 시점의 출력 사용
        out = self.fc(out[:, -1, :])
        return self.sigmoid(out)

def train_lstm_on_gpu(data_file=None):
    if data_file is None:
        data_file = str(Path(__file__).parent / "mock_payload.json")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Using Device: {device}")
    
    if not os.path.exists(data_file):
        print(f"[경고] {data_file}가 없습니다. 머크 데이터를 먼저 생성합니다.")
        from generate_mock_data import generate_mock_json_payload
        generate_mock_json_payload(data_file)

    # 데이터 로드 (시퀀스 길이 12 = 30분 단위 데이터 기준 6시간 관측)
    dataset = SensorDataset(data_file, sequence_length=12)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)
    
    model = DevicePredictorLSTM(input_size=len(dataset.feature_cols), output_size=len(dataset.target_cols)).to(device)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    print(f"[정보] 학습 시작... (Features: {dataset.feature_cols})")
    model.train()
    for epoch in range(10): # 학습 에포크 상향
        total_loss = 0
        for x_batch, y_batch in dataloader:
            x_batch, y_batch = x_batch.to(device), y_batch.to(device)
            
            optimizer.zero_grad()
            outputs = model(x_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        print(f"Epoch [{epoch+1}/10], Avg Loss: {total_loss/len(dataloader):.4f}")
        
    # 모델 저장 (추후 API에서 로드 가능하도록)
    save_path = os.path.join(os.path.dirname(__file__), "model", "lstm_device_model.pth")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'feature_cols': dataset.feature_cols,
        'target_cols': dataset.target_cols,
        'scaler': dataset.scaler
    }, save_path)
    print(f"✅ 모델 저장 완료: {save_path}")

if __name__ == "__main__":
    train_lstm_on_gpu()
