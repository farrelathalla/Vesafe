from __future__ import annotations

import json


_CATEGORY_TO_ZONE: dict[str, str] = {
    "production":           "production_zone",
    "sterile_production":   "production_zone",
    "chemical_storage":     "hazmat_storage",
    "b3_storage":           "hazmat_storage",
    "hazmat":               "hazmat_storage",
    "loading_dock":         "loading_dock",
    "forklift_zone":        "forklift_zone",
    "utility":              "utility_corridor",
    "electrical":           "utility_corridor",
    "gowning":              "gowning_room",
    "corridor_hallway":     "circulation_corridor",
    "other":                "general_area",
}

_ZONE_EQUIPMENT: dict[str, list[dict]] = {
    "production_zone": [
        {"type": "fire_extinguisher",  "position": "wall mount left",  "accessible": True,  "confidence": 0.85},
        {"type": "ppe_station",        "position": "entry wall",       "accessible": True,  "confidence": 0.80},
        {"type": "emergency_shower",   "position": "far wall",         "accessible": True,  "confidence": 0.75},
        {"type": "spill_kit",          "position": "wall mount right", "accessible": True,  "confidence": 0.78},
    ],
    "hazmat_storage": [
        {"type": "fire_extinguisher",  "position": "entry wall",       "accessible": True,  "confidence": 0.88},
        {"type": "spill_kit",          "position": "side wall",        "accessible": True,  "confidence": 0.82},
        {"type": "chemical_rack",      "position": "left wall",        "accessible": True,  "confidence": 0.90},
        {"type": "secondary_containment", "position": "floor under racks", "accessible": True, "confidence": 0.80},
        {"type": "emergency_shower",   "position": "entry zone",       "accessible": True,  "confidence": 0.72},
    ],
    "loading_dock": [
        {"type": "fire_extinguisher",  "position": "dock wall",        "accessible": True,  "confidence": 0.85},
        {"type": "dock_safety_light",  "position": "above bay door",   "accessible": True,  "confidence": 0.70},
        {"type": "wheel_chock",        "position": "dock floor",       "accessible": True,  "confidence": 0.75},
    ],
    "forklift_zone": [
        {"type": "safety_mirror",      "position": "corner wall",      "accessible": True,  "confidence": 0.80},
        {"type": "fire_extinguisher",  "position": "side wall",        "accessible": True,  "confidence": 0.83},
        {"type": "charging_station",   "position": "back wall",        "accessible": True,  "confidence": 0.78},
    ],
    "utility_corridor": [
        {"type": "fire_extinguisher",  "position": "wall mount",       "accessible": True,  "confidence": 0.85},
        {"type": "electrical_panel",   "position": "wall mount",       "accessible": True,  "confidence": 0.88},
        {"type": "emergency_exit",     "position": "end of corridor",  "accessible": True,  "confidence": 0.90},
    ],
    "gowning_room": [
        {"type": "ppe_station",        "position": "entry wall",       "accessible": True,  "confidence": 0.85},
        {"type": "air_shower",         "position": "exit door",        "accessible": True,  "confidence": 0.80},
    ],
    "circulation_corridor": [
        {"type": "emergency_exit",     "position": "end wall",         "accessible": True,  "confidence": 0.88},
        {"type": "fire_extinguisher",  "position": "wall mount",       "accessible": True,  "confidence": 0.83},
        {"type": "evacuation_sign",    "position": "ceiling",          "accessible": True,  "confidence": 0.90},
    ],
    "general_area": [
        {"type": "fire_extinguisher",  "position": "wall mount",       "accessible": True,  "confidence": 0.80},
        {"type": "emergency_exit",     "position": "side wall",        "accessible": True,  "confidence": 0.85},
    ],
}

_ZONE_ADJACENCY: dict[str, list[str]] = {
    "production_zone":      ["gowning_room", "hazmat_storage", "circulation_corridor"],
    "hazmat_storage":       ["loading_dock", "circulation_corridor", "production_zone"],
    "loading_dock":         ["hazmat_storage", "forklift_zone", "circulation_corridor"],
    "forklift_zone":        ["loading_dock", "circulation_corridor", "general_area"],
    "utility_corridor":     ["production_zone", "general_area"],
    "gowning_room":         ["production_zone", "circulation_corridor"],
    "circulation_corridor": ["production_zone", "hazmat_storage", "loading_dock", "forklift_zone"],
    "general_area":         ["circulation_corridor", "forklift_zone"],
}


# Maps a detected vision condition to (equipment_type, make_inaccessible, remove_entirely)
_CONDITION_EFFECTS: dict[str, tuple[str, bool, bool]] = {
    "blocked_fire_extinguisher":   ("fire_extinguisher",   True,  False),
    "blocked_emergency_exit":      ("emergency_exit",       True,  False),
    "blocked_electrical_panel":    ("electrical_panel",     True,  False),
    "blocked_emergency_shower":    ("emergency_shower",     True,  False),
    "blocked_ppe_station":         ("ppe_station",          True,  False),
    "no_evacuation_sign":          ("evacuation_sign",      False, True),
    "no_safety_mirror":            ("safety_mirror",        False, True),
    "no_secondary_containment":    ("secondary_containment",False, True),
    "deformed_rack":               ("chemical_rack",        True,  False),
    "tangled_cords":               ("electrical_panel",     True,  False),
    "scorched_panel":              ("electrical_panel",     True,  False),
    "spill_present":               ("spill_kit",            True,  False),
    "improper_chemical_storage":   ("chemical_rack",        True,  False),
}


def _apply_conditions(equipment: list[dict], conditions: list[str]) -> list[dict]:
    """Mutate equipment list based on vision-detected conditions."""
    if not conditions:
        return equipment

    remove_types: set[str] = set()
    inaccessible_types: set[str] = set()

    for condition in conditions:
        if condition in _CONDITION_EFFECTS:
            eq_type, make_inaccessible, remove = _CONDITION_EFFECTS[condition]
            if remove:
                remove_types.add(eq_type)
            elif make_inaccessible:
                inaccessible_types.add(eq_type)

    result = []
    for eq in equipment:
        if eq["type"] in remove_types:
            continue
        if eq["type"] in inaccessible_types:
            eq = {**eq, "accessible": False}
        result.append(eq)
    return result


async def extract_scene_graph(classified_images: list[dict], osm_topology: dict) -> dict:
    seen_zones: set[str] = set()
    rooms = []
    zone_counter: dict[str, int] = {}

    for image in classified_images[:12]:
        raw_category = (image.get("category") or "other").lower()
        zone_type = _CATEGORY_TO_ZONE.get(raw_category, "general_area")

        zone_counter[zone_type] = zone_counter.get(zone_type, 0) + 1
        room_id = f"{zone_type.upper()[:4]}-{zone_counter[zone_type]:02d}"

        if zone_type in seen_zones:
            continue
        seen_zones.add(zone_type)

        conditions: list[str] = image.get("conditions", [])

        equipment = [
            {**eq, "confidence": round(eq["confidence"] * image.get("confidence", 0.85), 3)}
            for eq in _ZONE_EQUIPMENT.get(zone_type, _ZONE_EQUIPMENT["general_area"])
        ]
        equipment = _apply_conditions(equipment, conditions)

        adjacency = [
            adj for adj in _ZONE_ADJACENCY.get(zone_type, [])
            if adj in seen_zones or adj in [
                _CATEGORY_TO_ZONE.get((img.get("category") or "other").lower(), "general_area")
                for img in classified_images[:12]
            ]
        ]

        # Derive zone flags — vision conditions can override defaults
        has_emergency_exit = zone_type in ("circulation_corridor", "utility_corridor", "loading_dock")
        if "blocked_emergency_exit" in conditions:
            has_emergency_exit = True  # exit exists but is blocked (agents will flag it)

        rooms.append({
            "room_id": room_id,
            "type": zone_type,
            "area_sqm_estimate": 80 + len(rooms) * 30,
            "equipment": equipment,
            "adjacency": adjacency,
            "has_emergency_exit": has_emergency_exit,
            "forklift_access": zone_type in ("loading_dock", "forklift_zone", "hazmat_storage"),
            "hazmat_present": zone_type in ("hazmat_storage", "production_zone") or "spill_present" in conditions,
            "image_source_quality": image.get("source", "supplemental_upload"),
            "detected_conditions": conditions,
        })

    if not rooms:
        rooms.append({
            "room_id": "GENE-01",
            "type": "general_area",
            "area_sqm_estimate": 200,
            "equipment": _ZONE_EQUIPMENT["general_area"],
            "adjacency": [],
            "has_emergency_exit": True,
            "forklift_access": False,
            "hazmat_present": False,
            "image_source_quality": "supplemental_upload",
        })

    return {
        "facility_type": "pharmaceutical_manufacturing_warehouse",
        "units": [
            {
                "unit_id": "warehouse_main",
                "unit_type": "pharmaceutical_warehouse",
                "rooms": rooms,
            }
        ],
        "flow_annotations": {
            "forklift_paths": [["loading_dock", "forklift_zone", "hazmat_storage"]],
            "personnel_paths": [["gowning_room", "production_zone", "circulation_corridor"]],
            "evacuation_routes": [["production_zone", "circulation_corridor", "loading_dock"]],
            "hazmat_zones": [r["room_id"] for r in rooms if r.get("hazmat_present")],
            "osm_context": json.dumps(osm_topology)[:300],
        },
    }
