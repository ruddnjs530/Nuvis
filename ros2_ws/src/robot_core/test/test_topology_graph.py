from pathlib import Path

from robot_core.topology_graph import load_room_specs, load_topology_graph


def test_topology_graph_load_and_path():
    config_dir = Path(__file__).resolve().parents[2] / "robot_nav" / "config"
    graph = load_topology_graph(str(config_dir / "graph.yaml"))
    rooms = load_room_specs(str(config_dir / "rooms.yaml"), graph.nodes.keys())

    assert "center_entry" in graph.nodes
    assert "kitchen" in rooms

    path = graph.shortest_path("center_entry", rooms["kitchen"].work_node)
    assert path is not None
    assert path[0] == "center_entry"
    assert path[-1] == "kitchen_work"


def test_topology_graph_nearest_node_prefers_sticky_node():
    config_dir = Path(__file__).resolve().parents[2] / "robot_nav" / "config"
    graph = load_topology_graph(str(config_dir / "graph.yaml"))

    sticky = graph.nearest_node(
        x=1.00,
        y=-4.00,
        last_node_id="hq_dock",
        snap_radius=2.5,
        stick_radius=0.8,
    )
    assert sticky == "hq_dock"
