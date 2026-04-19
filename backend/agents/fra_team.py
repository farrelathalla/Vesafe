"""Keselamatan Alat Berat — clearance forklift, garis kuning, clearance mesin."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model

_FORKLIFT_AREAS = {"warehouse_storage", "production_floor", "corridor_hallway"}
_MACHINE_AREAS  = {"production_floor", "utility_room"}


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    for room in rooms_from_model(world_model):
        room_type = room.get("type")

        if room_type in _FORKLIFT_AREAS:
            area = room.get("area_sqft_estimate", 0)
            if area and area < 200:
                findings.append(make_finding(
                    scan_id=scan_id, domain="FRA", sub_agent="Forklift-Clearance-Auditor", room=room,
                    severity="CRITICAL", confidence=0.88,
                    label_text=f"Lorong {room['room_id']} terlalu sempit untuk manuver forklift aman",
                    recommendation="Perlebar jalur forklift minimum lebar forklift + 2×900mm per SMK3 PP No. 50/2012",
                ))

            if not room.get("sightline_to_nursing_station", True):
                findings.append(make_finding(
                    scan_id=scan_id, domain="FRA", sub_agent="SafetyLine-Inspector", room=room,
                    severity="HIGH", confidence=0.82,
                    label_text=f"Garis kuning jalur evakuasi di {room['room_id']} tidak terlihat atau terhalang",
                    recommendation="Cat ulang dan bersihkan garis kuning jalur evakuasi per SMK3 dan SNI 03-1735-2000",
                ))

        if room_type in _MACHINE_AREAS:
            if has_equipment(room, "ventilator") and not accessible_equipment(room, "ventilator"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="FRA", sub_agent="WorkZone-Geometer", room=room,
                    severity="HIGH", confidence=0.79,
                    label_text=f"Mesin di {room['room_id']} tidak memiliki clearance memadai — risiko kecelakaan",
                    recommendation="Pastikan clearance minimal 1m di sekeliling mesin berat per SMK3 PP No. 50/2012",
                    eq_type="ventilator",
                ))

    return findings
