"""
Canonical Spatial Bundle — Pharmaceutical Warehouse K3
=======================================================
Derives a structured, LLM-readable spatial bundle from a warehouse scene-graph.
This is the sole input contract for all K3 domain swarm agents.

LLMs emit zone_id / equipment_ref references only — no raw coordinates.
"""
from __future__ import annotations

import math

_GRID_SCALE = 4.0
_COL_ORIGIN = 0.5
_ROW_ORIGIN = 0.5
_HALF = _GRID_SCALE * 0.4

_EQ_HEIGHT: dict[str, float] = {
    "fire_extinguisher":    1.2,
    "ppe_station":          1.5,
    "emergency_shower":     2.1,
    "spill_kit":            0.9,
    "chemical_rack":        1.8,
    "secondary_containment":0.1,
    "safety_mirror":        2.0,
    "electrical_panel":     1.4,
    "emergency_exit":       2.2,
    "evacuation_sign":      2.3,
    "dock_safety_light":    2.5,
    "wheel_chock":          0.1,
    "charging_station":     1.0,
    "air_shower":           2.0,
}
_DEFAULT_HEIGHT = 1.0


def _grid_center(room: dict, index: int) -> dict[str, float]:
    col = float(index % 4)
    row = float(index // 4)
    return {
        "x": round((col - _COL_ORIGIN) * _GRID_SCALE, 3),
        "y": _DEFAULT_HEIGHT,
        "z": round((row - _ROW_ORIGIN) * _GRID_SCALE, 3),
    }


def _parse_position_offset(pos: str) -> tuple[float, float, float]:
    p = (pos or "").lower()
    dx, dy, dz = 0.0, 0.0, 0.0
    if "right" in p:
        dx += _HALF
    if "left" in p:
        dx -= _HALF
    if "entry" in p or "door" in p:
        dz -= _HALF
    if "back" in p or "far" in p:
        dz += _HALF
    if "ceiling" in p or "overhead" in p:
        dy = 2.3 - _DEFAULT_HEIGHT
    elif "wall" in p:
        dy = 1.4 - _DEFAULT_HEIGHT
    elif "floor" in p or "ground" in p:
        dy = 0.1 - _DEFAULT_HEIGHT
    return dx, dy, dz


def _eq_anchor(room_center: dict, eq: dict) -> dict[str, float]:
    eq_type = eq.get("type", "")
    height = _EQ_HEIGHT.get(eq_type, _DEFAULT_HEIGHT)
    dx, dy, dz = _parse_position_offset(eq.get("position", ""))
    return {
        "x": round(room_center["x"] + dx, 3),
        "y": round(height + dy, 3),
        "z": round(room_center["z"] + dz, 3),
    }


def _zone_tags(room: dict, flow_annotations: dict) -> list[str]:
    tags: list[str] = []
    room_type = (room.get("type") or "").lower()
    room_id = room.get("room_id", "")

    if room_id in flow_annotations.get("hazmat_zones", []):
        tags.append("hazmat_zone")
    if room.get("hazmat_present"):
        tags.append("hazmat_zone")
    if room.get("forklift_access"):
        tags.append("forklift_zone")
    if room.get("has_emergency_exit"):
        tags.append("has_emergency_exit")
    if "production" in room_type:
        tags.append("production_zone")
    if "hazmat" in room_type or "chemical" in room_type or "b3" in room_type:
        tags.append("chemical_storage")
    if "loading" in room_type or "dock" in room_type:
        tags.append("loading_zone")
    if "forklift" in room_type:
        tags.append("forklift_zone")
    if "utility" in room_type or "electrical" in room_type:
        tags.append("utility_zone")
    if "gowning" in room_type:
        tags.append("ppe_required")
    if "corridor" in room_type or "circulation" in room_type:
        tags.append("circulation")
    return list(set(tags))


def build_spatial_bundle(
    scene_graph: dict,
    floor_plan_ref: str | None = None,
) -> dict:
    units = scene_graph.get("units", [])
    unit_id: str = units[0]["unit_id"] if units else "warehouse_main"

    all_rooms: list[dict] = []
    for unit in units:
        all_rooms.extend(unit.get("rooms", []))

    flow_annotations: dict = scene_graph.get("flow_annotations", {})

    bundle_rooms: list[dict] = []
    room_index: dict[str, dict] = {}

    for i, room in enumerate(all_rooms):
        center = _grid_center(room, i)
        equipment_anchors: list[dict] = []

        for eq in room.get("equipment", []):
            equipment_anchors.append({
                "type": eq.get("type"),
                "accessible": eq.get("accessible", True),
                "confidence": eq.get("confidence", 0.8),
                "anchor": _eq_anchor(center, eq),
                "position_hint": eq.get("position", ""),
            })

        bundle_room = {
            "room_id": room["room_id"],
            "type": room.get("type", "general_area"),
            "zone_tags": _zone_tags(room, flow_annotations),
            "center": center,
            "area_sqm": room.get("area_sqm_estimate", 80),
            "adjacency": room.get("adjacency", []),
            "has_emergency_exit": room.get("has_emergency_exit", False),
            "forklift_access": room.get("forklift_access", False),
            "hazmat_present": room.get("hazmat_present", False),
            "equipment": equipment_anchors,
        }
        bundle_rooms.append(bundle_room)
        room_index[room["room_id"]] = bundle_room

    nav_edges: list[dict] = []
    seen_edges: set[frozenset] = set()

    for room in bundle_rooms:
        for neighbor_id in room["adjacency"]:
            edge_key = frozenset([room["room_id"], neighbor_id])
            if edge_key in seen_edges or neighbor_id not in room_index:
                continue
            seen_edges.add(edge_key)
            neighbor = room_index[neighbor_id]
            c1, c2 = room["center"], neighbor["center"]
            dist_m = round(math.sqrt((c1["x"] - c2["x"]) ** 2 + (c1["z"] - c2["z"]) ** 2), 3)
            nav_edges.append({"from": room["room_id"], "to": neighbor_id, "distance_m": dist_m})

    zone_index: dict[str, list[str]] = {r["room_id"]: r["zone_tags"] for r in bundle_rooms}

    return {
        "unit_id": unit_id,
        "facility_type": scene_graph.get("facility_type", "pharmaceutical_manufacturing_warehouse"),
        "floor_plan_ref": floor_plan_ref,
        "rooms": bundle_rooms,
        "room_index": room_index,
        "nav_edges": nav_edges,
        "zone_index": zone_index,
        "flow_annotations": flow_annotations,
    }
