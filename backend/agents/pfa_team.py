"""Alur Produksi — cross-contamination flow, area karantina, jalur material bersih/kotor."""
from __future__ import annotations

from backend.agents.team_utils import make_finding, flow_from_model, rooms_from_model


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    rooms = rooms_from_model(world_model)
    room_map = {r["room_id"]: r for r in rooms}
    flow = flow_from_model(world_model)

    corridors = [r for r in rooms if r.get("type") == "corridor_hallway"]
    clean = set(flow.get("clean_corridors", []))
    dirty = set(flow.get("dirty_corridors", []))

    overlap = clean & dirty
    for room_id in overlap:
        room = room_map.get(room_id)
        if room:
            findings.append(make_finding(
                scan_id=scan_id,
                domain="PFA",
                sub_agent="FlowPath-Analyzer",
                room=room,
                severity="HIGH",
                confidence=0.85,
                label_text=f"Jalur bersih dan kotor bersilangan di {room_id} — risiko kontaminasi silang",
                recommendation=(
                    "Pisahkan jalur material bersih dan kotor dengan tanda lantai per "
                    "CPOB Bab 3 prinsip alur satu arah BPOM RI"
                ),
            ))

    for corridor in corridors:
        adj = set(corridor.get("adjacency", []))
        adj_types = {room_map[r].get("type") for r in adj if r in room_map}
        if "production_floor" in adj_types and "warehouse_storage" in adj_types:
            findings.append(make_finding(
                scan_id=scan_id,
                domain="PFA",
                sub_agent="Quarantine-Auditor",
                room=corridor,
                severity="ADVISORY",
                confidence=0.72,
                label_text=f"Koridor {corridor['room_id']} menghubungkan produksi dan gudang tanpa area karantina",
                recommendation=(
                    "Tambahkan area karantina atau anteroom antara gudang dan area produksi "
                    "per CPOB Bab 3 persyaratan bangunan dan fasilitas"
                ),
            ))

    return findings
