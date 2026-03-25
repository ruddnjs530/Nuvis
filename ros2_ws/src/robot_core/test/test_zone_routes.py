from pathlib import Path

import pytest
import yaml

from robot_core.zone_routes import load_route_config, load_waypoint_names


def test_load_route_config_expands_known_multi_segment_routes():
    config_dir = Path(__file__).resolve().parents[2] / "robot_nav" / "config"
    waypoint_names = load_waypoint_names(str(config_dir / "waypoints.yaml"))
    route_config = load_route_config(str(config_dir / "routes.yaml"), waypoint_names)

    assert route_config.is_blocked("entrance_next_room")
    assert route_config.expand("kitchen") == ["picture", "kitchen"]
    assert route_config.expand("hq") == ["hq"]


def test_load_route_config_rejects_unknown_waypoint_reference(tmp_path):
    waypoints_path = tmp_path / "waypoints.yaml"
    routes_path = tmp_path / "routes.yaml"

    waypoints_path.write_text(
        yaml.safe_dump({"waypoints": {"hq": {"x": 0.0, "y": 0.0, "yaw": 0.0}}}),
        encoding="utf-8",
    )
    routes_path.write_text(
        yaml.safe_dump({"zone_routes": {"hq": ["unknown_zone"]}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown_zone"):
        load_route_config(str(routes_path), load_waypoint_names(str(waypoints_path)))
