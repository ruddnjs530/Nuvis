from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Set

import yaml


@dataclass(frozen=True)
class ZoneRouteConfig:
    blocked_zones: Set[str] = field(default_factory=set)
    zone_routes: Dict[str, List[str]] = field(default_factory=dict)

    def is_blocked(self, zone: str) -> bool:
        return zone in self.blocked_zones

    def expand(self, zone: str) -> List[str]:
        route = self.zone_routes.get(zone)
        if route:
            return list(route)
        return [zone]


def load_waypoint_names(file_path: str) -> Set[str]:
    if not file_path:
        return set()

    path = Path(file_path)
    if not path.exists():
        return set()

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    waypoints = data.get("waypoints", {})
    if not isinstance(waypoints, dict):
        raise ValueError("waypoints.yaml must contain a top-level 'waypoints' mapping")
    return {str(name).strip() for name in waypoints.keys() if str(name).strip()}


def load_route_config(file_path: str, waypoint_names: Iterable[str]) -> ZoneRouteConfig:
    if not file_path:
        return ZoneRouteConfig()

    path = Path(file_path)
    if not path.exists():
        return ZoneRouteConfig()

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    blocked_raw = data.get("blocked_zones", [])
    routes_raw = data.get("zone_routes", {})

    if blocked_raw is None:
        blocked_raw = []
    if routes_raw is None:
        routes_raw = {}
    if not isinstance(blocked_raw, list):
        raise ValueError("routes.yaml 'blocked_zones' must be a list")
    if not isinstance(routes_raw, dict):
        raise ValueError("routes.yaml 'zone_routes' must be a mapping")

    blocked_zones = _normalize_zone_list(blocked_raw, "blocked_zones")
    zone_routes: Dict[str, List[str]] = {}
    for destination, route in routes_raw.items():
        destination_name = str(destination).strip()
        if not destination_name:
            raise ValueError("routes.yaml contains an empty destination key in 'zone_routes'")
        if isinstance(route, str):
            parsed_route = [route]
        else:
            parsed_route = route
        zone_routes[destination_name] = _normalize_zone_list(
            parsed_route, f"zone_routes.{destination_name}"
        )
        if not zone_routes[destination_name]:
            raise ValueError(f"routes.yaml route for '{destination_name}' must not be empty")

    waypoint_name_set = {name for name in waypoint_names if name}
    if waypoint_name_set:
        unknown = set(blocked_zones)
        unknown.update(zone_routes.keys())
        for route in zone_routes.values():
            unknown.update(route)
        unknown -= waypoint_name_set
        if unknown:
            unknown_list = ", ".join(sorted(unknown))
            raise ValueError(
                "routes.yaml references zones missing from waypoints.yaml: "
                f"{unknown_list}"
            )

    return ZoneRouteConfig(blocked_zones=set(blocked_zones), zone_routes=zone_routes)


def _normalize_zone_list(values, field_name: str) -> List[str]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list")

    normalized: List[str] = []
    seen = set()
    for value in values:
        zone = str(value).strip()
        if not zone:
            raise ValueError(f"{field_name} contains an empty zone name")
        if zone in seen:
            continue
        normalized.append(zone)
        seen.add(zone)
    return normalized
