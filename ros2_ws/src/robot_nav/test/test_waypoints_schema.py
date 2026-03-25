from pathlib import Path

import yaml


REQUIRED_ZONES = {
    "hq",
    "entrance",
    "entrance_next_room",
    "pc",
    "tv",
    "kitchen",
    "toilet_next_room",
    "left_up_room",
    "left_down_room",
}


def test_waypoints_yaml_has_required_zones():
    config_dir = Path(__file__).resolve().parents[1] / "config"
    data = yaml.safe_load((config_dir / "waypoints.yaml").read_text(encoding="utf-8"))
    waypoints = data.get("waypoints", {})

    assert REQUIRED_ZONES.issubset(set(waypoints.keys()))
    for zone_name in REQUIRED_ZONES:
        for key in ("x", "y", "yaw"):
            assert key in waypoints[zone_name]


def test_routes_yaml_references_known_waypoints():
    config_dir = Path(__file__).resolve().parents[1] / "config"
    waypoints = yaml.safe_load((config_dir / "waypoints.yaml").read_text(encoding="utf-8")).get(
        "waypoints", {}
    )
    routes = yaml.safe_load((config_dir / "routes.yaml").read_text(encoding="utf-8"))

    blocked_zones = routes.get("blocked_zones", [])
    zone_routes = routes.get("zone_routes", {})

    for zone_name in blocked_zones:
        assert zone_name in waypoints

    assert any(len(route) > 1 for route in zone_routes.values())
    for destination, route in zone_routes.items():
        assert destination in waypoints
        assert route
        for route_zone in route:
            assert route_zone in waypoints


def test_graph_yaml_is_well_formed():
    config_dir = Path(__file__).resolve().parents[1] / "config"
    graph = yaml.safe_load((config_dir / "graph.yaml").read_text(encoding="utf-8"))
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    assert nodes
    assert edges

    node_ids = []
    for node in nodes:
        assert node.get("id")
        assert node.get("kind") in {"junction", "room_entry", "room_work", "dock"}
        for key in ("x", "y", "yaw"):
            assert key in node
        node_ids.append(node["id"])
    assert len(node_ids) == len(set(node_ids))

    node_id_set = set(node_ids)
    for edge in edges:
        assert edge.get("from") in node_id_set
        assert edge.get("to") in node_id_set


def test_rooms_yaml_references_graph_nodes():
    config_dir = Path(__file__).resolve().parents[1] / "config"
    graph = yaml.safe_load((config_dir / "graph.yaml").read_text(encoding="utf-8"))
    rooms = yaml.safe_load((config_dir / "rooms.yaml").read_text(encoding="utf-8")).get(
        "rooms", {}
    )
    node_id_set = {node["id"] for node in graph.get("nodes", [])}

    assert REQUIRED_ZONES.issubset(set(rooms.keys()))
    for zone, spec in rooms.items():
        assert spec["entry_node"] in node_id_set
        assert spec["work_node"] in node_id_set
