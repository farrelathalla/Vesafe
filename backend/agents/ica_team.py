"""Pencegahan Kontaminasi — gowning area, sanitasi stasiun, dan jalur bersih/kotor."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model

_SKIP = {"building_exterior", "office_area"}
_CLEAN_ROOM_TYPES = {"production_floor", "quality_control_lab", "gowning_room"}


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    for room in rooms_from_model(world_model):
        if room.get("type") in _SKIP:
            continue

        if room.get("type") in _CLEAN_ROOM_TYPES:
            if not has_equipment(room, "hand_hygiene_dispenser"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="ICA", sub_agent="Gowning-Auditor", room=room,
                    severity="CRITICAL", confidence=0.93,
                    label_text=f"Tidak ada dispensing sanitizer di akses {room['room_id']} — pelanggaran CPOB",
                    recommendation="Pasang ABHR dispenser di setiap akses masuk area produksi per CPOB Bab 3 BPOM RI",
                    eq_type="hand_hygiene_dispenser",
                ))
            elif not accessible_equipment(room, "hand_hygiene_dispenser"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="ICA", sub_agent="Gowning-Auditor", room=room,
                    severity="HIGH", confidence=0.80,
                    label_text=f"Dispensing sanitizer di {room['room_id']} terhalang atau kosong",
                    recommendation="Bersihkan halangan atau tambah dispenser kedua per persyaratan higiene personel CPOB",
                    eq_type="hand_hygiene_dispenser",
                ))

        if room.get("type") == "production_floor":
            if not has_equipment(room, "safety_station"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="ICA", sub_agent="CrossFlow-Mapper", room=room,
                    severity="HIGH", confidence=0.85,
                    label_text=f"Tidak ada stasiun K3/sanitasi di area produksi {room['room_id']}",
                    recommendation="Pasang safety station dengan sanitizer dan APD di setiap zona produksi per CPOB Bab 3",
                    eq_type="safety_station",
                ))

    return findings
