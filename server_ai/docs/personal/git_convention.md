# git 컨벤션

생성일: 2026년 3월 18일 오전 10:45

# Git 컨벤션

## 1) 기본 원칙

- 기본 브랜치: `master`
- `master` 직접 push 금지 → **PR로만 머지**
- `master`는 항상 **동작 가능한 상태** 유지
- 작업은 **이슈 기반**으로만 진행 (브랜치 생성 전 이슈 생성)

---

## 2) 브랜치 전략 (GitHub Flow)

1. `master`에서 브랜치 생성
2. 작업 후 커밋
3. PR 생성
4. **AI 1차 코드리뷰 → 사람 리뷰 → 머지**
5. 머지 후 브랜치 삭제

---

## 3) 브랜치 네이밍 규칙 (필수)

### type (3개만)

- `feat` : 기능 개발
- `bug` : 버그 수정
- `task` : 그 외 작업(리팩토링/문서/테스트/설정/CI 등)

### 형식

`<scope>/<type>/<short-desc> `

- `<short-desc>`: `kebab-case`, 짧게 작성

예:

- `be/feat/some-message`

규칙:

---

## 4) 커밋 메시지 규칙

### 형식

`<message>`

### 작성 규칙

- 동사로 시작(예: add/fix/update/remove/refactor/implement…)
- 한 줄로 “무엇이 바뀌었는지” 명확히
- 불필요한 접두사/이모지/WIP 지양
- 한글 사용 가능
- 너무 공들일 필요 없음 (Squash merge로 `master`에는 상세 커밋이 남지 않음)

예:

- `implement auth login`
- `fix rooms list null handling`
- `add junit report workflow`
- `refactor user service methods`
- `add user service unit tests`

---

## 5) PR 규칙

### PR 제목

`[#<issueNo>] <type>: <summary>`

예:

- `[#126] feat: auth login 구현`

### PR 본문(최소)

- 변경 요약(1~3줄)
- 테스트 방법
- 이슈 연결
    - 자동 종료: `Closes #126`
    - 참조: `Refs #126`

---

## 6) 코드 리뷰 프로세스 (AI 1차 리뷰 필수)

1. PR 생성
2. **AI에게 1차 코드리뷰 요청(필수)**
3. AI 피드백 반영
4. 사람 리뷰(최소 1명) 승인
5. CI 통과 후 머지

---

## 7) 머지 방식

- 기본: **Squash merge 권장**
- 머지 후 브랜치 삭제

# 기능 개발 이슈 컨벤션

### 제목

`[Feature][Domain] 한 줄 요약`

---

## 본문 (메인 이슈 기준)

### 1) What to build (무엇을 개발하나) — 필수

- **개발 대상:** 만들 기능/플로우/엔드포인트
- **기대 동작(플로우):** 사용자/시스템이 어떻게 동작해야 하는지
- **제약/가정:** 인증/권한/성능/운영/호환/의존성
- **MVP:** 이번 이슈에서 반드시 되는 최소 기능(2~5 bullets)

### 2) (선택) API

- 엔드포인트 목록만 간단히

### 3) Acceptance Criteria ✅ (완료조건 표) — 필수

| # | 완료조건(측정 가능) | 검증 방법 |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

### 4) Sub-issues — 선택

- 서브이슈는 **제목만** 생성해도 된다.
- **서브이슈 본문은 빈칸이어도 OK** (필요할 때만 나중에 채운다).
- 서브이슈 제목도 동일 규칙 사용: `[Feature][Domain] ...`

---

## 복붙용 템플릿 (메인 이슈)

```markdown
## What to build (무엇을 개발하나)
- 개발 대상:
- 기대 동작(플로우):
- 제약/가정:
- MVP:
  -
  -

## (선택) API
-
-

## Acceptance Criteria ✅
| # | 완료조건(측정 가능) | 검증 방법 |
|---|---|---|
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

## Sub-issues (선택)
> 서브이슈는 제목만 만들어도 됨 (본문 비워도 OK)
- [ ] [Feature][...] ...
- [ ] [Feature][...] ...
```

---

## Sub-issues 섹션에 넣을 문구(권장)

> ✅ **서브이슈는 제목만 생성하고, 본문은 빈칸으로 둬도 OK.**
> 
> 
> 논의가 필요하거나 구현 중 발견되는 요구사항만 서브이슈 본문에 추가한다.
> 

---

# 예시

### 제목

`[Feature][MVP] Auth + Rooms 기본 플로우 개발 (FR-01~03,09,11,17,19 + FR-05 최소)`

## What to build (무엇을 개발하나)

- 개발 대상:
    - 로그인/로그아웃 + 방 목록/생성 + 초대코드 생성/참여 + 참여자 목록 조회까지 “최소 사용 가능” 플로우를 개발한다.
- 기대 동작(플로우):
    1. 사용자가 로그인하면 사이드바에 방 리스트가 표시된다(없으면 빈 상태).
    2. 사용자가 방을 생성하면 즉시 방 리스트에 반영된다.
    3. 사용자가 초대 코드를 생성하고, 다른 계정이 해당 코드로 join 할 수 있다.
    4. 사용자가 방 참여자 목록을 조회할 수 있다.
- 제약/가정(인증/권한/성능/운영/의존성):
    - 인증은 세션/쿠키 기반으로 동작한다(로그인 시 세션 생성, 로그아웃 시 만료).
    - 로그인 사용자만 방 목록/생성/초대/참여/참여자 조회 가능(최소 권한).
    - FE 연동을 위해 성공/실패 응답이 일관된 형태로 전달되어야 한다(최소: HTTP Status + message 또는 code).
- MVP(이번 이슈에서 반드시 되는 최소 범위):
    - FR-01~03, FR-09, FR-11, FR-17, FR-19 + FR-05(최소)
    - 아래 API가 동작하고, FE에서 DoD 시나리오가 수행 가능해야 한다.

## API

- GET /api/v1/auth/login
- POST /api/v1/auth/logout
- GET /api/v1/rooms
- POST /api/v1/rooms
- GET /api/v1/rooms/{id}/participants
- POST /api/v1/rooms/{id}/invites
- POST /api/v1/rooms/join/{inviteCode}

## Acceptance Criteria ✅

| # | 완료조건(측정 가능) | 검증 방법 |
| --- | --- | --- |
| 1 | 로그인 성공 후 사이드바에 방 리스트가 표시된다(빈 목록도 정상). | 로그인 후 UI 확인 + GET /rooms 200 |
| 2 | 방 생성 후 즉시 목록에 반영된다(생성 직후 재조회로 확인 가능). | POST /rooms 성공 → GET /rooms에 생성된 방 포함 |
| 3 | 초대 코드/링크 생성이 가능하고 inviteCode(또는 링크 구성 값)를 반환한다. | POST /rooms/{id}/invites 201 + inviteCode 확인 |
| 4 | 다른 계정으로 inviteCode를 사용해 join이 성공하고 방 참여 상태가 된다. | 다른 계정 로그인 → POST /rooms/join/{inviteCode} 성공 → 참여 확인 |
| 5 | 방 참여자 목록 조회가 가능하고 참여자 리스트에 본인이 포함된다. | GET /rooms/{id}/participants 200 + 리스트 확인 |

## Sub-issues

- [ ]  `[Feature][Auth] 로그인 플로우 구현 (GET /api/v1/auth/login)`
- [ ]  `[Feature][Auth] 로그아웃 구현 (POST /api/v1/auth/logout)`
- [ ]  `[Feature][Rooms] 방 목록 조회 + 사이드바 연동 (GET /api/v1/rooms)`
- [ ]  `[Feature][Rooms] 방 생성 + 생성 즉시 목록 반영 (POST /api/v1/rooms)`
- [ ]  `[Feature][Invites] 초대 코드/링크 생성 (POST /api/v1/rooms/{id}/invites)`
- [ ]  `[Feature][Join] 초대 코드로 방 참여 (POST /api/v1/rooms/join/{inviteCode})`
- [ ]  `[Feature][Participants] 방 참여자 목록 조회 (GET /api/v1/rooms/{id}/participants)`

---