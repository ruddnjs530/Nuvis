from pathlib import Path

import yaml


def test_waypoints_yaml_has_required_zones():
    path = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "waypoints.yaml"
    )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    waypoints = data.get("waypoints", {})

    assert "hq" in waypoints
    for zone_name in ("living_room", "bedroom", "kitchen"):
        assert zone_name in waypoints
        for key in ("x", "y", "yaw"):
            assert key in waypoints[zone_name]
