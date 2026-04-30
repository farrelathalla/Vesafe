"""SCA — Safety Communication & Signage Audit: rambu K3, LOTO, peringatan."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    rooms = rooms_from_model(world_model)

    has_any_evacuation_sign = any(has_equipment(r, "evacuation_sign") for r in rooms)

    for room in rooms:
        tags = room.get("zone_tags", [])
        is_hazmat = room.get("hazmat_present") or "hazmat_zone" in tags
        is_circulation = "circulation" in tags
        is_utility = "utility_zone" in tags

        if not has_any_evacuation_sign:
            findings.append(make_finding(
                scan_id=scan_id, domain="SCA", sub_agent="K3-Signage-Auditor", room=room,
                severity="HIGH", confidence=0.90,
                label_text=f"Tidak ada rambu evakuasi di seluruh fasilitas — {room['room_id']} tidak memiliki petunjuk darurat",
                recommendation="Pasang rambu evakuasi fotoluminesens di semua koridor dan area kerja per SNI ISO 7010",
                eq_type="evacuation_sign",
            ))
            break

        if is_circulation and not has_equipment(room, "evacuation_sign"):
            findings.append(make_finding(
                scan_id=scan_id, domain="SCA", sub_agent="K3-Signage-Auditor", room=room,
                severity="HIGH", confidence=0.87,
                label_text=f"Koridor {room['room_id']} tidak memiliki rambu arah evakuasi",
                recommendation="Pasang rambu evakuasi dengan tanda panah arah per SNI ISO 7010 E001/E002",
                eq_type="evacuation_sign",
            ))

        if is_hazmat and not has_equipment(room, "ppe_station"):
            findings.append(make_finding(
                scan_id=scan_id, domain="SCA", sub_agent="K3-Signage-Auditor", room=room,
                severity="CRITICAL", confidence=0.92,
                label_text=f"Area B3 {room['room_id']} tidak ada rambu wajib APD — pekerja tidak tahu risiko",
                recommendation="Pasang rambu wajib APD GHS dan prosedur penanganan darurat di pintu masuk area B3",
                eq_type="ppe_station",
            ))

        if is_utility and has_equipment(room, "electrical_panel"):
            if not accessible_equipment(room, "electrical_panel"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="SCA", sub_agent="LOTO-Electrical-Auditor", room=room,
                    severity="CRITICAL", confidence=0.90,
                    label_text=f"Panel listrik di {room['room_id']} terhalang — prosedur LOTO tidak dapat dijalankan",
                    recommendation="Pastikan clearance 1m di depan panel listrik dan terapkan prosedur LOTO per PUIL 2011",
                    eq_type="electrical_panel",
                ))

    return findings
