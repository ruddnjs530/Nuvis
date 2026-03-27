import argparse
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

# ==============================================================================
# [교육용 주석] 다중 방(Mock) 센서 데이터 생성기
# ==============================================================================
# 목적:
#   실제 IoT 수집 전 단계에서 AI 추천 서버가 여러 room_id를 동시에 받아도
#   방별 생활 패턴을 학습/테스트할 수 있도록 가짜 시계열 데이터를 생성합니다.
# ==============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "server_ai" / "recommendation" / "data" / "mock_payload.json"

ROOM_PROFILES = [
    {
        "room_id": 1,
        "name": "스테이션 (HQ)",
        "temp_bias": -0.5,
        "hum_bias": -4.0,
        "dust_bias": 4.0,
        "pattern": "hq_air",
    },
    {
        "room_id": 2,
        "name": "거실",
        "temp_bias": 0.2,
        "hum_bias": -1.5,
        "dust_bias": 6.0,
        "pattern": "living_air",
    },
    {
        "room_id": 3,
        "name": "주방",
        "temp_bias": 1.2,
        "hum_bias": 5.5,
        "dust_bias": 18.0,
        "pattern": "kitchen_air",
    },
    {
        "room_id": 4,
        "name": "현관",
        "temp_bias": -1.0,
        "hum_bias": 3.0,
        "dust_bias": 16.0,
        "pattern": "entrance_air",
    },
    {
        "room_id": 5,
        "name": "현관 옆방",
        "temp_bias": 0.3,
        "hum_bias": 8.0,
        "dust_bias": 3.0,
        "pattern": "humid_dehum_room",
    },
    {
        "room_id": 6,
        "name": "PC방",
        "temp_bias": 1.6,
        "hum_bias": -3.0,
        "dust_bias": 9.0,
        "pattern": "pc_air",
    },
    {
        "room_id": 7,
        "name": "화장실 옆방",
        "temp_bias": 0.8,
        "hum_bias": 13.0,
        "dust_bias": 2.0,
        "pattern": "toilet_dehum",
    },
    {
        "room_id": 8,
        "name": "침실1 (좌측 상단)",
        "temp_bias": -0.4,
        "hum_bias": -11.0,
        "dust_bias": 1.0,
        "pattern": "bedroom_humidifier_a",
    },
    {
        "room_id": 9,
        "name": "침실2 (좌측 하단)",
        "temp_bias": -0.2,
        "hum_bias": -9.5,
        "dust_bias": 2.5,
        "pattern": "bedroom_humidifier_b",
    },
]


def resolve_output_paths(filename: str | None = None) -> list[Path]:
    if filename:
        return [Path(filename)]
    return [DEFAULT_OUTPUT_PATH]


def simulate_environment(ts: datetime, profile: dict, rng: random.Random) -> tuple[float, float, float]:
    hour = ts.hour
    day_angle = hour / 24.0 * 2 * math.pi

    temp = (
        22.0
        + profile["temp_bias"]
        + math.sin(day_angle - math.pi / 2) * 4.2
        + rng.gauss(0, 0.45)
    )
    hum = (
        48.0
        + profile["hum_bias"]
        + math.cos(day_angle) * 8.0
        + rng.gauss(0, 1.8)
    )
    fine_dust = max(0.0, rng.gauss(22.0 + profile["dust_bias"], 7.0))

    # 공간 특성에 따라 센서값을 조금 더 극적으로 만들어 방별 패턴을 분리합니다.
    if profile["pattern"] == "kitchen_air" and hour in {8, 10, 18, 20}:
        fine_dust += rng.uniform(18, 42)
        hum += rng.uniform(2, 5)
    elif profile["pattern"] == "entrance_air" and hour in {6, 8, 18, 20, 22}:
        fine_dust += rng.uniform(14, 36)
    elif profile["pattern"] == "toilet_dehum" and hour in {6, 8, 22}:
        hum += rng.uniform(8, 15)
    elif profile["pattern"] in {"bedroom_humidifier_a", "bedroom_humidifier_b"} and hour in {0, 2, 4, 6}:
        hum -= rng.uniform(5, 9)
    elif profile["pattern"] == "pc_air" and hour in {20, 22, 0}:
        temp += rng.uniform(0.8, 1.6)
        fine_dust += rng.uniform(6, 14)

    if rng.random() < 0.03:
        fine_dust += rng.uniform(35, 70)

    return round(temp, 1), round(hum, 1), round(fine_dust, 1)


def simulate_device_usage(
    ts: datetime,
    profile: dict,
    temperature: float,
    humidity: float,
    fine_dust: float,
    rng: random.Random,
) -> tuple[int, int, int]:
    hour = ts.hour
    is_weekend = ts.weekday() >= 5
    pattern = profile["pattern"]

    air_on = 0
    hum_on = 0
    dehum_on = 0

    if pattern == "hq_air":
        if not is_weekend and hour in {8, 10, 12} and rng.random() < 0.72:
            air_on = 1
    elif pattern == "living_air":
        if not is_weekend and hour in {18, 20, 22} and rng.random() < 0.85:
            air_on = 1
        if is_weekend and hour in {14, 16, 20} and rng.random() < 0.55:
            air_on = 1
    elif pattern == "kitchen_air":
        if hour in {8, 10, 18, 20} and rng.random() < 0.88:
            air_on = 1
    elif pattern == "entrance_air":
        if hour in {6, 8, 18, 20, 22} and rng.random() < 0.78:
            air_on = 1
    elif pattern == "humid_dehum_room":
        if hour in {12, 14, 16} and humidity > 54 and rng.random() < 0.82:
            dehum_on = 1
    elif pattern == "pc_air":
        if hour in {20, 22, 0} and rng.random() < 0.84:
            air_on = 1
    elif pattern == "toilet_dehum":
        if hour in {6, 8, 22} and rng.random() < 0.9:
            dehum_on = 1
    elif pattern == "bedroom_humidifier_a":
        if hour in {0, 2, 4, 6} and humidity < 46 and rng.random() < 0.92:
            hum_on = 1
    elif pattern == "bedroom_humidifier_b":
        if hour in {22, 0, 2, 4, 6} and humidity < 48 and rng.random() < 0.88:
            hum_on = 1

    # 센서 급변에 따른 긴급 반응 규칙
    if fine_dust > 68:
        air_on = 1
    if humidity < 33 and pattern in {"living_air", "bedroom_humidifier_a", "bedroom_humidifier_b"}:
        hum_on = 1
    if humidity > 67 and pattern in {"kitchen_air", "humid_dehum_room", "toilet_dehum"}:
        dehum_on = 1
    if temperature > 28 and pattern == "pc_air":
        air_on = 1

    return air_on, hum_on, dehum_on


def generate_mock_json_payload(
    filename: str | None = None,
    days: int = 14,
    interval_minutes: int = 120,
    user_id: int = 1,
    seed: int = 42,
    room_profiles: list[dict] | None = None,
) -> dict:
    output_paths = resolve_output_paths(filename)
    profiles = room_profiles or ROOM_PROFILES

    print(
        f"Generating {days} days of multi-room mock sensor payload "
        f"({len(profiles)} rooms, {interval_minutes}min interval)..."
    )

    rng = random.Random(seed)

    start_time = datetime.now() - timedelta(days=days)
    end_time = datetime.now()

    records = []

    ts = start_time
    while ts <= end_time:
        for profile in profiles:
            temperature, humidity, fine_dust = simulate_environment(ts, profile, rng)
            air_on, hum_on, dehum_on = simulate_device_usage(
                ts,
                profile,
                temperature,
                humidity,
                fine_dust,
                rng,
            )

            records.append(
                {
                    "timestamp": ts.isoformat(),
                    "room_id": profile["room_id"],
                    "temperature": temperature,
                    "humidity": humidity,
                    "fine_dust": fine_dust,
                    "air_purifier_on": air_on,
                    "humidifier_on": hum_on,
                    "dehumidifier_on": dehum_on,
                }
            )
        ts += timedelta(minutes=interval_minutes)

    records.sort(key=lambda row: (row["timestamp"], row["room_id"]))

    payload = {
        "user_id": user_id,
        "sensor_data": records,
    }

    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        print(f"  - wrote {len(records)} records to {path}")

    print(f"✅ Generated total {len(records)} records across {len(profiles)} rooms.")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate multi-room mock recommendation payload.")
    parser.add_argument("--filename", type=str, default=None, help="Optional output filename override.")
    parser.add_argument("--days", type=int, default=14, help="How many days of history to generate.")
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=120,
        help="Sampling interval in minutes. Default keeps multi-room payload compact enough for AI tests.",
    )
    parser.add_argument("--user-id", type=int, default=1, help="User ID to embed in the payload.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible mock data.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_mock_json_payload(
        filename=args.filename,
        days=args.days,
        interval_minutes=args.interval_minutes,
        user_id=args.user_id,
        seed=args.seed,
    )
