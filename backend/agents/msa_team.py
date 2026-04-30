"""MSA — Material Safety Audit: APD, penanganan B3, emergency shower."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model

_PPE_REQUIRED = {"production_zone", "hazmat_storage", "chemical_storage", "gowning_room", "loading_dock"}


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    for room in rooms_from_model(world_model):
        zone_type = room.get("type", "")
        tags = room.get("zone_tags", [])
        needs_ppe = zone_type in _PPE_REQUIRED or "hazmat_zone" in tags or "ppe_required" in tags
        is_hazmat = room.get("hazmat_present") or "hazmat_zone" in tags

        if needs_ppe:
            if not has_equipment(room, "ppe_station"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="MSA", sub_agent="PPE-Station-Auditor", room=room,
                    severity="CRITICAL", confidence=0.92,
                    label_text=f"Tidak ada stasiun APD di zona wajib APD {room['room_id']}",
                    recommendation="Pasang stasiun APD lengkap (helm, sarung tangan, goggle, apron) di akses zona per SMK3",
                    eq_type="ppe_station",
                ))
            elif not accessible_equipment(room, "ppe_station"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="MSA", sub_agent="PPE-Station-Auditor", room=room,
                    severity="HIGH", confidence=0.86,
                    label_text=f"Stasiun APD di {room['room_id']} terhalang atau kosong",
                    recommendation="Bersihkan akses stasiun APD dan isi ulang perlengkapan yang habis",
                    eq_type="ppe_station",
                ))

        if is_hazmat:
            if not has_equipment(room, "emergency_shower"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="MSA", sub_agent="Emergency-Shower-Auditor", room=room,
                    severity="CRITICAL", confidence=0.94,
                    label_text=f"Tidak ada emergency shower di area B3 {room['room_id']} — risiko cedera kimia akut",
                    recommendation="Pasang emergency shower + eyewash dalam radius 10 detik jalan per ANSI Z358.1",
                    eq_type="emergency_shower",
                ))
            elif not accessible_equipment(room, "emergency_shower"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="MSA", sub_agent="Emergency-Shower-Auditor", room=room,
                    severity="CRITICAL", confidence=0.90,
                    label_text=f"Emergency shower di {room['room_id']} terhalang — tidak dapat digunakan saat paparan kimia",
                    recommendation="Bersihkan jalur akses emergency shower, area bebas halangan min 1m per ANSI Z358.1",
                    eq_type="emergency_shower",
                ))

    return findings
