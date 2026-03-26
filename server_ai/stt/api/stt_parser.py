import json
import re

# ==============================================================================
# [교육용 주석] STT 음성 명령 자연어 도출 파서 (Rule-based Natural Language NLP Parser)
# ==============================================================================
# 역할: 거대한 Whisper AI가 뱉어낸 길고 불규칙한 한글 일반 텍스트 문장 
#       (예: "흠... 거실 말고 우리 안방에 있는 가습기를 편하게 켜줄래?") 속에서,
#       우리가 정형화 해둔 규칙(Rule)대로 핵심 의도만 발라내고,
#       최종적으로 백엔드 서버나 자율주행 모듈이 쉽게 알아먹을 수 있는 
#       프로토콜 포맷(JSON)으로 분해 조립해주는 똑똑한 중간 번역(Parser) 레이어 모듈입니다.
# ==============================================================================

# 백엔드 Prisma seed 기준 기본 방 맵.
# 나중에 STT 시스템이 가동되면 메인 서버 API(DB)와 연동돼 최신 정보로 덮어쓰기(Set) 당합니다.
DEFAULT_ROOM_MAP = {
    "스테이션 (HQ)": 1,
    "거실": 2,
    "침실": 3,
    "주방": 4,
}

# 유저들이 일상에서 섞어 쓰는 흔한 동의어(Alias) 그룹 묶음
# 백엔드 대표 이름은 유지하고, 사용자 발화만 별칭으로 흡수합니다.
ROOM_ALIAS_GROUPS = (
    ("스테이션 (HQ)", "스테이션", "hq", "HQ", "에이치큐", "충전소"),
    ("침실", "안방", "내방"),
    ("주방", "부엌"),
)

def _expand_room_aliases(base_room_map: dict) -> dict:
    """
    주어진 방 데이터베이스(예: 거실=2, 침실=3)를 바탕으로,
    방금 위에서 선언한 그룹("안방", "내방") 동의어들에 대해서도 똑같은 roomId 지식을 확장 및 파생 이식해 두는 함수입니다.
    이래야 유저가 사투리나 동의어를 써도 똑같은 AI 모델로 찰떡같이 백엔드와 연결시켜줍니다.
    """
    expanded_map = dict(base_room_map)

    for alias_group in ROOM_ALIAS_GROUPS:
        # 그룹(안방,침실,내방) 안의 단어 중 하나(안방) 라도 db에 등록되어 있다면 그 ID(예: 3)를 일단 확보해옵니다. (파이썬 next 발전형 문법 사용)
        matched_room_id = next(
            (expanded_map[name] for name in alias_group if name in expanded_map),
            None,
        )
        # 매칭되는게 하나도 없으면 다음 그룹으로 넘어감
        if matched_room_id is None:
            continue

        # 기 확보된 아이디를 기반으로, 해당 그룹의 '모든' 동의어 텍스트들을 딕셔너리의 새 키(Key)로 등재합니다.
        for alias in alias_group:
            expanded_map.setdefault(alias, matched_room_id)

    return expanded_map

# 이 파이썬 패키지가 임포트되어 돌아갈 때 상시 메모리에 상주시켜 검색 효율을 극대화하는 글로벌 기반 확장 맵 변수
ROOM_MAP = _expand_room_aliases(DEFAULT_ROOM_MAP)

# 유저가 부르는 한국어 기기 명칭 -> 백엔드/클라이언트 DB가 알아먹는 기기 영문 코드 (양방향 연결 고리)
MODULE_MAP = {
    "공기청정기": "air_purifier",
    "가습기": "humidifier",
    "제습기": "dehumidifier"
}

# 기기 동의어/오타 허용 관용구 맵 (딥러닝 Whisper AI가 가끔 이상한 오타를 뱉을 때를 대비한 사후 문맥 보정기)
# 예: STT가 "가스불 켜줘" 라고 실수로 오인식 했더라도 사용 환경에 가스불은 지시할 리 없으므로, 우리는 정황상 기계적으로 "가습기"임을 유추해 보정해 줍니다.
MODULE_ALIAS_MAP = {
    "공기청소기": "공기청정기",
    "공기천장기": "공기청정기",
    "공기천천히": "공기청정기", # 한국어 발음 뭉개짐 이슈 방어
    "가스기": "가습기",
    "가스불": "가습기",
}

def set_room_map(room_map: dict) -> dict:
    """외부(main.py 통신부 등)에서 백엔드 최신 방 정보를 긁어왔을 때 이 파서의 뇌 테이블 구조를 강제로 업데이트 시켜주는 Setter 유틸"""
    global ROOM_MAP
    # 외부에서 새 구조가 들어오면 거기에 또 동의어 확장팩을 달아서 재장전 해줌
    ROOM_MAP = _expand_room_aliases(room_map or DEFAULT_ROOM_MAP)
    return ROOM_MAP

def get_room_map() -> dict:
    """현재 메모리에 탑재된 파서의 지식 맵을 깊은 복사(dict 껍데기)로 안전히 전달해주는 Getter"""
    return dict(ROOM_MAP)

def normalize_text(text: str) -> str:
    """문자열에서 한글, 알파벳, 숫자만 모조리 남기고, 복잡한 띄어쓰기 탭 기호 쉼표 등 '모든' 특수 기호를 완전 정규식 변환으로 밀어버리는 클렌징 함수"""
    return re.sub(r"[^가-힣a-zA-Z0-9]", "", text).lower()

def detect_module(filtered_text: str, normalized_text: str) -> str | None:
    """
    텍스트 내부에 '공기청정기', '가습기' 등의 단어가 포함돼있는지 엑스레이 처럼 검사하여 매칭되는 영문 제원 코드(모듈 ID)를 내뱉습니다.
    인자: 원본 문장(filtered), 띄어쓰기를 싹 다 갈아버린 버전의 문장(normalized)
    """
    # 1. 1차 관문 (정식 명칭 확인) -> "안방 공기청정기 켜줘" 에 콕 박혀있는 "공기청정기" 단어 식별
    for kor_module, eng_module in MODULE_MAP.items():
        if kor_module in filtered_text or normalize_text(kor_module) in normalized_text:
            return eng_module

    # 2. 2차 관문 (혹시 AI의 오타나 사용자의 발음 실수 등에 따른 별명(Alias)으로 확인되는 경우 유도결제)
    for alias_text, canonical_module in MODULE_ALIAS_MAP.items():
        if alias_text in normalized_text:
            return MODULE_MAP[canonical_module] # 가스불 -> 가습기 영문코드 도출

    # 못 찾았으면 빈손
    return None


def parse_voice_command(stt_text: str) -> str:
    """
    [핵심 핵심 두뇌] STT로 변환된 긴 한국어 자연어 문장을 3단계의 수술로 분석하여 
    로봇이 바로 움직이거나 API로 스위치를 켤 수 있는 제원 규격 포맷 "명령어 JSON" 형태 배열로 쪼개주는(파싱) 마법사입니다.
    """
    # 밑그림 포맷 생성. 찾지 못할 경우 기본 상태는 None, none.
    command = {
        "action": "none",
        "roomId": None,
        "module": None,
        "state": None
    }
    
    # [Step 1: 지능적 부정어 노이즈 사전 필터링]
    # "거실 말고 안방" 같이 인간 특유의 변덕을 방어하기 위함. 해당 정규식을 돌려서 '거실' 이라는 단계를 텍스트 원본에서 그냥 칼삭(Re.sub 공백) 해버립니다.
    # 그러면 이후 프로세스는 애초에 거실이란 걸 인지 못하므로 에러가 나지 않습니다.
    filtered_text = re.sub(r'([가-힣]+)\s*(말고|아니고|가지마)', '', stt_text)
    
    # 한국어 띄어쓰기 오인식 고질병("내 방" 이라고 쓸수도 "내방"이라 쓸수도)을 일원화시키기 위해,
    # 공백을 한톨도 안 남기고 합쳐버린 빽빽한 문자열 복사본도 뒤의 병행 판독기에 참조용으로 건네줍니다.
    no_space_text = normalize_text(filtered_text)

    # [Step 2: 타겟 위치 방 추출 (어디로 갈까?)]
    for kor_room, room_id in ROOM_MAP.items():
        # "주방" 이라는 글씨가 파형에 존재한다면!
        normalized_room = normalize_text(kor_room)
        if kor_room in filtered_text or normalized_room in no_space_text:
            command["roomId"] = room_id
            command["action"] = "move" # 방 이름이 일단 언급됐다면 로봇은 무조건 현재위치를 버리고 거기로 바퀴를 굴려 '이동명령'을 내려야 하므로 state를 진화시킴
            break # 목적지는 하나이므로 반복 돌 필요없이 탈출

    # [Step 3: 제어할 사물 하드웨어명(모듈) 추출 (무엇을 만질까?)]
    detected_module = detect_module(filtered_text, no_space_text)
    if detected_module:
        command["module"] = detected_module
        
        # Action 조건부 분기(지능화):
        # 만약 목적지 방 이름도 있고 조작할 기기도 외쳤다면? 로봇 입장에선 => "이동 하고 기기도 켜(move_and_operate)" 이고,
        # 방 이름은 안 불렀는데 내 앞의 기기 이름만 불렀다면? => "지금 서 있는 곳에서 움직이지 말고 켜기만 해(operate_module)" 이 됩니다.
        command["action"] = "move_and_operate" if command["roomId"] else "operate_module"

    # [Step 4: ON/OFF 작동 상태(State) 판별 (어떻게 해야할까?)]
    # 정규표현식(Regex)의 난이도 높은 토핑. 긍정과 부정 인텐트(의도) 파악기.
    # 단순히 '켜' 라는 단어만 찾으면 "켜지 마" 도 켠다고 착각함. 
    # 따라서 부정어(지마, 안, 말고, 취소)가 뒤에 절대로 존재하지 않는(Negative Lookahead) '순수한 켤 의도'만 잡아내도록 구성했습니다.
    on_pattern = r"(켜|작동|틀어|시작)(?!.*(지\s*마|안|말고|취소))"
    off_pattern = r"(꺼|중지|멈춰|종료|그만)(?!.*(지\s*마|안|말고|취소))"
    
    if re.search(on_pattern, filtered_text):
        command["state"] = "on"
    elif re.search(off_pattern, filtered_text):
        command["state"] = "off"
        
    # 예외의 예외 처리: "꺼지지마" (끄다의 강한 부정 -> 즉 꺼지지 않게 켜라) 같은 한국어식 이중부정 대응
    elif re.search(r"(꺼지지마|멈추지마)", filtered_text):
        command["state"] = "on"
        
    # 예외의 예외 처리: "안 켜", "켜지 마" 처럼 전치/후치 된 켜다의 강렬한 거부 -> 꺼라 상태로 치환.
    elif re.search(r"(켜\s*지\s*마|작동\s*하\s*지\s*마|안\s*켜|안\s*틀)", filtered_text):
        command["state"] = "off"

    # [Step 5: 최종 안전장치 Fallback] 
    # 아무런 핵심 단어(방 이름도, 기기도) 못 찾은 완전 개소리일 경우 동작 오류를 막기 위해 실패 JSON을 백엔드로 쏴올림
    if command["action"] == "none":
        return json.dumps({"error": "명령을 이해하지 못했습니다."}, ensure_ascii=False)

    # 파싱된 파이썬 객체 트리 구조를 예쁜 구조의 JSON 문자열(indent=2)로 텍스트화 치환하여 반환
    return json.dumps(command, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # 이 파일을 단독 실행(>$ python stt_parser.py)할 때만 돌아가는 Mock 테스트베드 (서버랑 무관)
    test_sentences = [
        "거실로 가서 공기청정기 켜줘",
        "거실 말고 안방 가습기 꺼줄래",
        "안방 공기청정기 켜지마",
        "그냥 주방으로 이동해",
        "HQ로 돌아가",
    ]
    
    print("=== 자연어 명령 파싱 테스트 (Mock) ===\n")
    for sentence in test_sentences:
        print(f"음성 인식 텍스트: '{sentence}'")
        parsed_json = parse_voice_command(sentence)
        print(f"변환된 로봇 명령:\n{parsed_json}\n")
