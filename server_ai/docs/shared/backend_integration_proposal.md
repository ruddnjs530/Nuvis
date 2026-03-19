# 스마트홈 AI 추천 시스템 연동 제안서

> **작성자:** AI 파트 | **작성일:** 2026-03-13
> 본 문서는 백엔드(메인 서버)와 AI 분석 서버 간의 원활하고 효율적인 데이터 연동을 위한 아키텍처 제안서입니다.
> AI 서버는 유지보수와 성능 최적화를 위해 DB에 직접 접근하지 않고, 메인 서버가 필요한 데이터를 전송하여 분석 결과를 반환받는 **Stateless API 방식(Data Passing)** 을 채택합니다.

> **문서 범위 메모 (2026-03-16):** 본 문서의 AI 서버 범위는 `server_ai`로 분리되는 **추천 AI + STT 계열 서비스**를 기준으로 합니다. YOLO 비전 노드는 ROS2 런타임 성격이 강하므로 본 문서의 백엔드 연동 범위에서는 제외하고, 추후 `ros2_ws` 측 통합 문맥에서 별도로 다룹니다.

---

## 1. 기본 연동 방식 (MVP: Human-in-the-loop)

현재 MVP 단계에서 권장하는 기본적인 **"추천 후 사용자 수락"** 기반의 파이프라인입니다.

### 1.1. 데이터 흐름 (Data Flow)

1. **데이터 추출:** 메인 서버(Spring Boot)에서 정기적으로(예: 앱 기동 시 또는 사용자가 추천 버튼 클릭 시) 특정 유저의 최근 N일치 센서 로그 데이터를 DB에서 추출합니다.
2. **API 요청:** 메인 서버가 AI 서버의 엔드포인트로 추출한 데이터를 JSON 형태로 `POST` 요청합니다.
3. **분석 및 응답:** AI 서버는 수신된 데이터를 메모리상(Pandas DataFrame)에서 즉시 분석하고, "최적의 기기 제어 임계값(Threshold)" 수치를 메인 서버로 응답합니다.
4. **사용자 제안:** 메인 서버는 응답받은 결과값을 기반으로 사용자에게 "이 조건으로 자동화를 설정할까요?"라고 묻습니다.
5. **룰 반영:** 사용자가 앱에서 '수락'을 누르면 해당 조건이 메인 DB의 자동화 룰 테이블에 최종 저장됩니다.

### 1.2. API 명세 (제안)

#### 이벤트 추천

- **Endpoint:** `POST /api/event/ai-suggestions` (AI 서버)
- **Request Body (메인 서버 → AI 서버):** 최근 이력 데이터를 배열로 전송 (최대 500건)

```json
{
  "user_id": "user_12345",
  "sensor_data": [
    {
      "timestamp": "2026-03-13T12:00:00",
      "temperature": 22.5,
      "humidity": 45,
      "pm25": 40.2,
      "air_purifier_on": 1,
      "humidifier_on": 0,
      "dehumidifier_on": 0
    },
    {
      "timestamp": "2026-03-13T12:05:00",
      "temperature": 22.5,
      "humidity": 44,
      "pm25": 45.1,
      "air_purifier_on": 1,
      "humidifier_on": 0,
      "dehumidifier_on": 0
    }
  ]
}
```

- **Response Body (AI 서버 → 메인 서버):** 기기별 분석 결과 반환

```json
{
  "status": "success",
  "user_id": "user_12345",
  "data": {
    "air_purifier": {
      "device": "공기청정기",
      "threshold_value": 42.7,
      "condition_operator": ">",
      "analysis_details": {
        "avg_pm25_when_turned_on": 45.0,
        "data_points_analyzed": 38,
        "pattern_confidence": "High"
      },
      "reason": "유저 행동 분석 결과, 미세먼지 수치가 약 45.0㎍/m³ 일 때 공기청정기를 켰습니다. ..."
    },
    "humidifier": { "..." : "..." },
    "dehumidifier": { "..." : "..." },
    "anomaly_warnings": {
      "status": "warning",
      "device": "air_purifier",
      "ml_pm25_alert_threshold": 43.1,
      "anomaly_data_points_analyzed": 4,
      "reason": "최근 데이터의 이상치 분석 결과, 비정상적일 때의 평균 미세먼지가 약 45.4㎍/m³ 입니다. 급격한 미세먼지 증가로 인한 위기 상황을 사전에 알릴 수 있도록, 43.1㎍/m³ 도달 시 스마트 알림 전송을 추천합니다."
    }
  }
}
```

> **💡 신규 추가 (위기 감지 알림):** 
> 응답 결과 중 `anomaly_warnings` 객체는 AI의 **Isolation Forest(이상 탐지 머신러닝)** 알고리즘이 찾아낸 급격한 환경 변화(예: 미세먼지 폭증 등) 결과입니다. 만약 해당 필드의 `status`가 `"warning"`으로 반환될 경우, 메인 서버에서는 유저에게 **즉각적인 스마트 푸시 알림**을 보내는 용도로 활용해 주시기 바랍니다.

#### 스케줄 추천

- **Endpoint:** `POST /api/schedule/ai-suggestions` (AI 서버)
- **Request/Response 구조:** 이벤트 추천과 동일한 Request Body, 시간대 기반 스케줄 결과 반환

> **⚠️ 안전장치 (AI 서버 자체 적용 완료):**
> - 전달 데이터가 500건을 초과하면 **최신 500건만** 분석에 사용합니다.
> - 기기 1개당 분석 시간이 **5초를 초과**하면 해당 기기만 timeout 처리하고 나머지 기기는 정상 반환합니다.
> - 따라서 메인 서버의 **HTTP Read Timeout은 30초 이상**으로 설정해 주세요.

---

## 2. ERD 검토 결과 및 DB 수정 요청

현재 ERD(`ERD.jpg`)를 검토한 결과입니다.

### ✅ 이미 잘 설계된 부분 (변경 불필요)

- **기기 범용성:** `MODULES.type`, `EVENTS.action_module_type`, `SCHEDULES.action_module_type` 컬럼이 `VARCHAR` 타입으로 설계되어, 공기청정기/가습기/제습기 등 **어떤 기기 타입이든 동일한 AI 추천 로직에 연결 가능**합니다.
- **AI 추천 결과 저장:** `AI_SUGGESTIONS` 테이블이 이미 존재하며 `suggested_threshold`, `reason`, `status(수락/거절)` 컬럼을 갖춰 Human-in-the-loop 흐름을 완벽하게 지원합니다.

### ❌ AI 분석을 위해 추가가 필요한 부분 (★ 필수 요청)

#### 요청 A: `ROOM_CONDITIONS_HISTORY` 테이블 추가

**이유:** 현재 `ROOM_CONDITIONS` 테이블은 `room_id`에 Unique Key 제약이 걸려 방 당 현재 값 **1건만** 저장됩니다. AI가 "지난 N일 사용자 패턴"을 분석하려면 시계열 이력이 누적(INSERT)되는 별도 히스토리 테이블이 필요합니다.

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| `id` | BIGINT (PK, AUTO_INCREMENT) | 이력 레코드 고유 ID |
| `room_id` | BIGINT (FK) | 어느 방의 센서 데이터인지 |
| `temperature` | FLOAT | 온도 (°C) |
| `humidity` | FLOAT | 습도 (%) |
| `fine_dust` | FLOAT | 미세먼지 pm2.5 (㎍/m³) |
| `recorded_at` | DATETIME | 센서값이 기록된 시각 |

> **구현 방법:** 기존 `ROOM_CONDITIONS`를 UPDATE 하던 로직 외에, 동일한 데이터를 이 테이블에 **INSERT도 추가**해주시면 됩니다.

---

#### 요청 B: `MODULE_CONTROL_LOGS` 테이블 추가

**이유:** `EVENTS`, `SCHEDULES` 테이블은 "규칙(Rule)"을 저장하는 테이블로, **실제로 언제 기기가 가동/정지됐는지의 이력**을 남기지 못합니다. 스케줄 추천의 핵심인 "사용자가 몇 시에 기기를 켜는 패턴이 있는가?"를 분석하려면 실제 조작 이력 로그가 필요합니다.

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| `log_id` | BIGINT (PK, AUTO_INCREMENT) | 로그 레코드 고유 ID |
| `user_id` | BIGINT (FK) | 어느 유저의 조작인지 |
| `module_id` | BIGINT (FK) | 어느 모듈이 동작했는지 |
| `action_module_type` | VARCHAR(50) | 기기 종류 (`air_purifier`, `humidifier`, `dehumidifier`) |
| `action` | VARCHAR(10) | 조작 내용 (`ON` / `OFF`) |
| `triggered_by` | VARCHAR(20) | 조작 주체 (`manual` / `event` / `schedule`) |
| `created_at` | DATETIME | 실제 기기가 켜진/꺼진 시각 |

> **구현 방법:** 유저가 대시보드에서 기기를 수동 조작하거나, 이벤트/스케줄 자동화로 기기가 실행될 때마다 이 테이블에 **INSERT**해주시면 됩니다.

---

#### 요청 C: AI 연동용 기간 조회 로직 추가

위 두 테이블이 추가된 후, 메인 서버는 AI 분석 요청 시 특정 유저의 **"최근 14일치 센서 기록 + 조작 이력"** 을 조인하여 아래 JSON 형태로 AI 서버에 전달하는 내부 쿼리 및 로직을 구현해주세요.

```json
// sensor_data 배열 1건 = ROOM_CONDITIONS_HISTORY 1행 + 해당 시각 MODULE_CONTROL_LOGS 기기 상태 조인
{
  "user_id": "user_001",
  "sensor_data": [
    {
      "timestamp": "2026-03-13 09:00:00",
      "temperature": 24.3,
      "humidity": 55.2,
      "pm25": 32.1,
      "air_purifier_on": 0,
      "humidifier_on": 1,
      "dehumidifier_on": 0
    }
  ]
}
```

---

## 3. AI 서버 장애 시 Fallback 처리 요청

AI 추천은 **편의 기능**이므로, AI 서버가 응답 불가한 경우에도 나머지 서비스는 정상 동작해야 합니다.

AI 서버 호출 실패 / 타임아웃 발생 시:
- 메인 서비스는 **정상 동작 유지**
- 사용자에게는 아래 메시지만 노출

```
"AI 추천 기능을 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요."
```

구현 예시:

```java
try {
    AiSuggestionResponse result = aiClient.getSuggestions(payload);
    return result;
} catch (Exception e) {
    log.warn("[AI Fallback] AI 서버 응답 실패: {}", e.getMessage());
    return AiSuggestionResponse.unavailable("AI 추천 기능을 일시적으로 사용할 수 없습니다.");
}
```

---

## 4. 추가 제안: 완전 자동화(Full-Automation) 시연 시나리오

MVP 안정화 후 2차 고도화로 도입할 수 있는 **"완전 자동화(100% Autonomous)"** 시스템입니다.
시뮬레이터 시연 중 "미세먼지 폭증" 같은 갑작스러운 환경 변화 시, **유저 클릭 없이 AI가 자동 감지 → 로봇 즉각 출동**하는 시나리오입니다.

### 4.1. 변경된 흐름 (Seamless Update)

서버 간 API 연동 규격은 그대로 유지하면서 **메인 서버의 DB 반영 방식**만 변경합니다.

1. 메인 서버가 주기적으로 AI 서버에 분석을 요청하여 새로운 "최적 임계값 업데이트치"를 응답받습니다.
2. 메인 서버는 **사용자에게 확인을 묻지 않고**, 백그라운드에서 즉시 유저의 자동화 규칙 테이블(Rule DB)을 갱신합니다.
3. 서버/IoT 기기 룰 엔진이 즉각 갱신되어, 사용자는 아무 설정도 하지 않았지만 환경에 맞춰 자동으로 기기가 제어됩니다.

### 4.2. 실시간 자동 감지를 위한 연동 방식 합의 필요

| | 제안 A: Push 방식 ← **AI 파트 추천** | 제안 B: Polling 방식 |
|---|---|---|
| **흐름** | 메인 서버가 5초마다 AI 서버로 센서 데이터 Push | AI 서버 내부 스케줄러가 5초마다 DB를 직접 SELECT |
| **장점** | 실시간성 최고, DB I/O 없음, 서비스 분리 유지 | 메인 서버 추가 작업 최소 |
| **단점** | 메인 서버에 스케줄러 추가 필요 | AI 서버에 DB 접근 계정 공유 필요 (보안 위반) |

```
[제안 A 흐름]
시뮬레이터 → 메인 서버 (N초마다 센서 갱신)
                  ↓ POST /api/ai/analyze-realtime (N초마다)
              AI 서버 (임계값 초과 여부 즉시 판단)
                  ↓ {"action": "trigger", "robot_command": "move_to_kitchen_and_purify"}
              메인 서버 → 로봇 제어 명령 전달
```

> **🗣️ 논의 요청:** "시연 때 미세먼지 폭증 이벤트를 AI가 자동으로 감지해서 로봇을 출동시키려고 하는데, 제안 A처럼 백엔드에서 AI쪽으로 5초마다 데이터를 쏴줄 수 있어? 아니면 제안 B처럼 AI에서 직접 DB를 긁어갈까?"

### 4.3. 완전 자동화 도입 시 Safety Net (백엔드 추가 설계 필요)

사용자 선택권을 없애는 방식이므로 불쾌감 방지를 위한 예외 처리가 필요합니다.

- **Auto-Fallback (무한루프 방지):** 자동화 룰에 의해 공기청정기가 켜졌는데, 유저가 5분 내에 "수동"으로 끈 경우 → 유저의 의도를 존중하여 해당 룰을 임시로 N시간 동안 **비활성화(Mute)** 처리.
- **우선순위 관리 (Conflict Resolution):** "미세먼지 수치 초과(동작)" 룰과 "사용자 외출 상태(정지)" 상태가 겹칠 때를 대비하여 백엔드 룰 엔진에 **우선순위 부여 알고리즘** 필요.

---

## 5. 결론

- AI 서버가 DB에 직접 쿼리를 날리는 것보다, **메인 서버가 필요한 데이터를 추려서 AI 서버에 Data Payload로 전달하는 방식**이 응답 속도, 서버 부하 분산, 추후 시스템 확장성 측면에서 훨씬 유리합니다.
- 백엔드팀에서는 **1.2. API 명세**를 참고하여 해당 데이터를 전달하는 `POST` 통신 로직을 구현해주시면 바로 연동 테스트가 가능합니다.

---

## 📌 요청사항 최종 요약

| 번호 | 구분 | 요청 내용 | 담당 | 완료 여부 |
|---|---|---|---|---|
| 1-A | **[필수]** | `ROOM_CONDITIONS_HISTORY` 테이블 추가 | 백엔드 | ⬜ |
| 1-B | **[필수]** | `MODULE_CONTROL_LOGS` 테이블 추가 | 백엔드 | ⬜ |
| 1-C | **[필수]** | AI 연동용 최근 14일치 데이터 조회 로직 구현 | 백엔드 | ⬜ |
| 2-A | **[필수]** | AI 서버 HTTP Read Timeout 30초 이상 설정 | 백엔드 | ⬜ |
| 2-B | **[필수]** | AI 서버 장애 시 Fallback 처리 구현 | 백엔드 | ⬜ |
| 3 | **[권장]** | `anomaly_warnings` 기반 위기 감지 Push 알림 전송 로직 구현 | 백엔드 | ⬜ |
| 4 | **[논의]** | 완전 자동화 시연용 연동 방식 합의 (Push vs Polling) | AI + 백엔드 | ⬜ |
| 4-a | **[논의 후 구현]** | 완전 자동화 Safety Net (Auto-Fallback, Conflict Resolution) | 백엔드 | ⬜ |

---
