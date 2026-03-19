import json
import re

# 가상의 방 위치 및 모듈 사전 (현장 상황에 맞게 매핑 추가)
ROOM_MAP = {
    "거실": "living_room",
    "주방": "kitchen",
    "침실": "bedroom",
    "안방": "bedroom",
    "내방": "my_room"
}

MODULE_MAP = {
    "공기청정기": "air_purifier",
    "가습기": "humidifier",
    "제습기": "dehumidifier"
}

def parse_voice_command(stt_text: str) -> str:
    """
    STT로 변환된 자연어 텍스트를 분석하여 로봇이 이해할 수 있는 JSON 명령어로 변환합니다.
    (예: "거실 말고 안방 가습기 켜줘" -> JSON)
    부정어(말고, 가지마 등)를 인지하고 정확한 타겟을 추출하도록 고도화되었습니다.
    """
    command = {
        "action": "none",
        "target_room": None,
        "module": None,
        "state": None
    }
    
    # "말고", "아니고" 등의 부정어가 붙은 단어를 걸러내기 위한 전처리
    filtered_text = re.sub(r'([가-힣]+)\s*(말고|아니고|가지마)', '', stt_text)
    
    # 띄어쓰기 문제("내 방" vs "내방")를 해결하기 위해 공백을 모두 제거한 문자열도 검색용으로 준비
    no_space_text = filtered_text.replace(" ", "")

    # 1. 대상 위치 파악 (공백 제거된 텍스트와 원본 필터링 텍스트 모두 고려)
    for kor_room, eng_room in ROOM_MAP.items():
        if kor_room in filtered_text or kor_room in no_space_text:
            command["target_room"] = eng_room
            command["action"] = "move" # 방 이름이 있으면 일단 이동 명령 부여
            break

    # 2. 제어할 모듈 파악
    for kor_module, eng_module in MODULE_MAP.items():
        if kor_module in filtered_text:
            command["module"] = eng_module
            # 방 이름이 있으면 이동 후 제어, 없으면 현재 위치에서 모듈만 제어
            command["action"] = "move_and_operate" if command["target_room"] else "operate_module"
            break

    # 3. ON/OFF 상태 제어 파악
    # 부정어 결합 형태 인지 (예: 안 켜도 돼, 켜지마, 끄지마)
    on_pattern = r"(켜|작동|틀어|시작)(?!.*(지마|안|말고|취소))"
    off_pattern = r"(꺼|중지|멈춰|종료|그만)(?!.*(지마|안|말고|취소))"
    
    # 예: "켜지마" -> 끄는 것과 같음. 혹은 동작 안함.
    # 단순화하여 긍정적인 '켜/꺼' 추출
    if re.search(on_pattern, filtered_text):
        command["state"] = "on"
    elif re.search(off_pattern, filtered_text):
        command["state"] = "off"
    elif re.search(r"(꺼지지마|멈추지마)", filtered_text):
        command["state"] = "on"
    elif re.search(r"(켜지마|작동하지마|안\s*켜|안\s*틀)", filtered_text):
        command["state"] = "off"

    # 파싱 실패 처리
    if command["action"] == "none":
        return json.dumps({"error": "명령을 이해하지 못했습니다."}, ensure_ascii=False)

    return json.dumps(command, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # 테스트 플레이그라운드
    test_sentences = [
        "거실로 가서 공기청정기 켜줘",
        "거실 말고 안방 가습기 꺼줄래",
        "안방 공기청정기 켜지마",
        "그냥 주방으로 이동해"
    ]
    
    print("=== 자연어 명령 파싱 테스트 (Mock) ===\n")
    for sentence in test_sentences:
        print(f"음성 인식 텍스트: '{sentence}'")
        parsed_json = parse_voice_command(sentence)
        print(f"변환된 로봇 명령:\n{parsed_json}\n")
