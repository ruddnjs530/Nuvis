import heapq
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import yaml


class GraphConfigError(ValueError):
    pass


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    kind: str
    x: float
    y: float
    yaw: float
    room_zone: str = ""


@dataclass(frozen=True)
class RoomSpec:
    entry_node: str
    work_node: str
    exit_node: str


class TopologyGraph:
    def __init__(
        self,
        nodes: Dict[str, GraphNode],
        adjacency: Dict[str, List[Tuple[str, float]]],
    ) -> None:
        self.nodes = nodes
        self.adjacency = adjacency

    def nearest_node(
        self,
        x: float,
        y: float,
        *,
        last_node_id: str = "",
        snap_radius: float,
        stick_radius: float,
    ) -> Optional[str]:
        if last_node_id and last_node_id in self.nodes:
            node = self.nodes[last_node_id]
            if _distance_xy(x, y, node.x, node.y) <= max(0.0, stick_radius):
                return last_node_id

        nearest_id = ""
        nearest_dist = float("inf")
        for node_id, node in self.nodes.items():
            dist = _distance_xy(x, y, node.x, node.y)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_id = node_id

        if not nearest_id:
            return None
        if nearest_dist > max(0.0, snap_radius):
            return None
        return nearest_id

    def shortest_path(self, start_node: str, goal_node: str) -> Optional[List[str]]:
        if start_node not in self.nodes or goal_node not in self.nodes:
            return None
        if start_node == goal_node:
            return [start_node]

        distances = {start_node: 0.0}
        previous: Dict[str, str] = {}
        heap: List[Tuple[float, str]] = [(0.0, start_node)]

        while heap:
            current_cost, current_node = heapq.heappop(heap)
            if current_node == goal_node:
                break
            if current_cost > distances.get(current_node, float("inf")):
                continue

            for next_node, edge_cost in self.adjacency.get(current_node, []):
                new_cost = current_cost + edge_cost
                if new_cost < distances.get(next_node, float("inf")):
                    distances[next_node] = new_cost
                    previous[next_node] = current_node
                    heapq.heappush(heap, (new_cost, next_node))

        if goal_node not in distances:
            return None

        path = [goal_node]
        cur = goal_node
        while cur != start_node:
            cur = previous[cur]
            path.append(cur)
        path.reverse()
        return path


def load_topology_graph(file_path: str) -> TopologyGraph:
    path = Path(file_path)
    if not file_path or not path.exists():
        raise GraphConfigError(f"graph file not found: {file_path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    nodes_raw = raw.get("nodes", [])
    edges_raw = raw.get("edges", [])
    if not isinstance(nodes_raw, list):
        raise GraphConfigError("graph.yaml 'nodes' must be a list")
    if not isinstance(edges_raw, list):
        raise GraphConfigError("graph.yaml 'edges' must be a list")

    nodes: Dict[str, GraphNode] = {}
    adjacency: Dict[str, List[Tuple[str, float]]] = {}

    for node_raw in nodes_raw:
        if not isinstance(node_raw, dict):
            raise GraphConfigError("graph.yaml node entry must be a mapping")
        node_id = str(node_raw.get("id", "")).strip()
        if not node_id:
            raise GraphConfigError("graph.yaml node is missing non-empty 'id'")
        if node_id in nodes:
            raise GraphConfigError(f"duplicate node id in graph.yaml: {node_id}")

        kind = str(node_raw.get("kind", "")).strip()
        if kind not in {"junction", "room_entry", "room_work", "dock"}:
            raise GraphConfigError(
                f"graph.yaml node '{node_id}' has invalid kind='{kind}'"
            )
        try:
            x = float(node_raw["x"])
            y = float(node_raw["y"])
            yaw = float(node_raw.get("yaw", 0.0))
        except Exception as exc:  # noqa: BLE001
            raise GraphConfigError(f"node '{node_id}' has invalid numeric fields: {exc}")
        room_zone = str(node_raw.get("room_zone", "")).strip()

        node = GraphNode(
            node_id=node_id,
            kind=kind,
            x=x,
            y=y,
            yaw=yaw,
            room_zone=room_zone,
        )
        nodes[node_id] = node
        adjacency[node_id] = []

    for edge_raw in edges_raw:
        if not isinstance(edge_raw, dict):
            raise GraphConfigError("graph.yaml edge entry must be a mapping")
        source = str(edge_raw.get("from", "")).strip()
        target = str(edge_raw.get("to", "")).strip()
        if not source or not target:
            raise GraphConfigError("graph.yaml edge must have non-empty 'from' and 'to'")
        if source not in nodes or target not in nodes:
            raise GraphConfigError(
                f"graph.yaml edge references unknown node: {source} -> {target}"
            )
        if "cost" in edge_raw and edge_raw["cost"] is not None:
            try:
                edge_cost = float(edge_raw["cost"])
            except Exception as exc:  # noqa: BLE001
                raise GraphConfigError(
                    f"graph.yaml edge '{source}->{target}' has invalid cost: {exc}"
                )
        else:
            edge_cost = _distance_xy(nodes[source].x, nodes[source].y, nodes[target].x, nodes[target].y)

        if edge_cost <= 0.0:
            raise GraphConfigError(
                f"graph.yaml edge '{source}->{target}' must have positive cost"
            )
        bidirectional = bool(edge_raw.get("bidirectional", True))
        adjacency[source].append((target, edge_cost))
        if bidirectional:
            adjacency[target].append((source, edge_cost))

    return TopologyGraph(nodes=nodes, adjacency=adjacency)


def load_room_specs(file_path: str, graph_node_ids: Iterable[str]) -> Dict[str, RoomSpec]:
    path = Path(file_path)
    if not file_path or not path.exists():
        raise GraphConfigError(f"rooms file not found: {file_path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rooms_raw = raw.get("rooms", {})
    if not isinstance(rooms_raw, dict):
        raise GraphConfigError("rooms.yaml 'rooms' must be a mapping")

    valid_ids = set(graph_node_ids)
    room_specs: Dict[str, RoomSpec] = {}
    for room_zone, spec_raw in rooms_raw.items():
        zone = str(room_zone).strip()
        if not zone:
            raise GraphConfigError("rooms.yaml has an empty room key")
        if not isinstance(spec_raw, dict):
            raise GraphConfigError(f"rooms.yaml '{zone}' must be a mapping")

        entry_node = str(spec_raw.get("entry_node", "")).strip()
        work_node = str(spec_raw.get("work_node", "")).strip()
        exit_node = str(spec_raw.get("exit_node", "")).strip() or entry_node

        if not entry_node or not work_node:
            raise GraphConfigError(
                f"rooms.yaml '{zone}' requires 'entry_node' and 'work_node'"
            )
        for node_id in (entry_node, work_node, exit_node):
            if node_id not in valid_ids:
                raise GraphConfigError(
                    f"rooms.yaml '{zone}' references unknown graph node '{node_id}'"
                )

        room_specs[zone] = RoomSpec(
            entry_node=entry_node,
            work_node=work_node,
            exit_node=exit_node,
        )

    return room_specs


def _distance_xy(ax: float, ay: float, bx: float, by: float) -> float:
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
