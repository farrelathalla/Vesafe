"""Tanggap Darurat — APAR coverage, jalur evakuasi, emergency eyewash di area B3."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model

_B3_AREAS = {"chemical_storage_area", "production_floor", "quality_control_lab"}
_ALL_WORK_AREAS = {"production_floor", "warehouse_storage", "chemical_storage_area",
                   "quality_control_lab", "utility_room"}


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    rooms = rooms_from_model(world_model)
    work_rooms = [r for r in rooms if r.get("type") in _ALL_WORK_AREAS]
    has_any_apar = any(has_equipment(r, "fire_extinguisher") for r in rooms)

    for room in work_rooms:
        if not has_any_apar:
            findings.append(make_finding(
                scan_id=scan_id, domain="ERA", sub_agent="APAR-Mapper", room=room,
                severity="CRITICAL", confidence=0.97,
                label_text=f"Tidak ada APAR ditemukan di area {room['room_id']}",
                recommendation="Pasang APAR dengan jarak ≤15m antar titik per Permenaker No. 04/MEN/1980",
                eq_type="fire_extinguisher",
            ))
        elif has_equipment(room, "fire_extinguisher") and not accessible_equipment(room, "fire_extinguisher"):
            findings.append(make_finding(
                scan_id=scan_id, domain="ERA", sub_agent="APAR-Mapper", room=room,
                severity="CRITICAL", confidence=0.92,
                label_text=f"APAR di {room['room_id']} terhalang — tidak dapat diakses saat darurat",
                recommendation="Bersihkan area sekitar APAR minimal 1m, pasang tanda jelas per Permenaker 04/MEN/1980",
                eq_type="fire_extinguisher",
            ))

        if room.get("type") in _B3_AREAS:
            if not has_equipment(room, "eyewash_station"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="ERA", sub_agent="Eyewash-Auditor", room=room,
                    severity="CRITICAL", confidence=0.94,
                    label_text=f"Tidak ada emergency eyewash di area B3 {room['room_id']} — risiko cedera kimia",
                    recommendation="Pasang emergency eyewash dalam radius 10 detik jalan dari area B3 per ANSI/ISEA Z358.1",
                    eq_type="eyewash_station",
                ))

    return findings
