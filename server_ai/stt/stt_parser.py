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
    (예: "거실로 가서 공기청정기 켜줘" -> JSON)
    """
    command = {
        "action": "none",
        "target_room": None,
        "module": None,
        "state": None
    }
    
    # 1. 대상 위치 파악
    for kor_room, eng_room in ROOM_MAP.items():
        if kor_room in stt_text:
            command["target_room"] = eng_room
            command["action"] = "move" # 방 이름이 있으면 일단 이동 명령 부여
            break

    # 2. 제어할 모듈 파악
    for kor_module, eng_module in MODULE_MAP.items():
        if kor_module in stt_text:
            command["module"] = eng_module
            # 방 이름이 있으면 이동 후 제어, 없으면 현재 위치에서 모듈만 제어
            command["action"] = "move_and_operate" if command["target_room"] else "operate_module"
            break

    # 3. ON/OFF 상태 제어 파악
    if re.search(r"켜|작동|틀어", stt_text):
        command["state"] = "on"
    elif re.search(r"꺼|중지|멈춰", stt_text):
        command["state"] = "off"

    # 파싱 실패 처리
    if command["action"] == "none":
        return json.dumps({"error": "명령을 이해하지 못했습니다."})

    return json.dumps(command, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # 테스트 플레이그라운드
    test_sentences = [
        "로봇아 거실로 가서 공기청정기 켜줘",
        "안방 가습기 좀 꺼줄래",
        "그냥 주방으로 이동해"
    ]
    
    print("=== 자연어 명령 파싱 테스트 (Mock) ===\n")
    for sentence in test_sentences:
        print(f"음성 인식 텍스트: '{sentence}'")
        parsed_json = parse_voice_command(sentence)
        print(f"변환된 로봇 명령:\n{parsed_json}\n")
