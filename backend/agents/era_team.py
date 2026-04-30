"""ERA — Emergency Response Audit: pintu darurat, jalur evakuasi, sistem alarm."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    rooms = rooms_from_model(world_model)
    room_map = {r["room_id"]: r for r in rooms}

    rooms_with_exit = {r["room_id"] for r in rooms if r.get("has_emergency_exit")}
    rooms_with_accessible_exit = {
        r["room_id"] for r in rooms
        if r.get("has_emergency_exit") and accessible_equipment(r, "emergency_exit")
    }

    for room in rooms:
        tags = room.get("zone_tags", [])
        adjacency = room.get("adjacency", [])
        is_hazmat = room.get("hazmat_present") or "hazmat_zone" in tags

        zone_has_exit = room["room_id"] in rooms_with_exit
        adjacent_has_exit = any(adj in rooms_with_exit for adj in adjacency)

        if not zone_has_exit and not adjacent_has_exit:
            findings.append(make_finding(
                scan_id=scan_id, domain="ERA", sub_agent="Emergency-Exit-Auditor", room=room,
                severity="CRITICAL", confidence=0.95,
                label_text=f"Zona {room['room_id']} tidak memiliki akses pintu darurat di zona maupun zona tetangga",
                recommendation="Pasang pintu darurat dengan tanda EXIT yang menyala per SNI 03-6574-2001",
                eq_type="emergency_exit",
            ))
        elif zone_has_exit and room["room_id"] not in rooms_with_accessible_exit:
            findings.append(make_finding(
                scan_id=scan_id, domain="ERA", sub_agent="Emergency-Exit-Auditor", room=room,
                severity="CRITICAL", confidence=0.93,
                label_text=f"Pintu darurat di {room['room_id']} terhalang — jalur evakuasi tersumbat",
                recommendation="Singkirkan semua penghalang dari depan pintu darurat, area bebas min 1m per SNI 03-1746-2000",
                eq_type="emergency_exit",
            ))

        if is_hazmat and not zone_has_exit:
            adjacent_accessible = any(adj in rooms_with_accessible_exit for adj in adjacency)
            if not adjacent_accessible:
                findings.append(make_finding(
                    scan_id=scan_id, domain="ERA", sub_agent="Evacuation-Route-Auditor", room=room,
                    severity="CRITICAL", confidence=0.96,
                    label_text=f"Area B3 {room['room_id']} tidak memiliki jalur evakuasi yang bebas hambatan",
                    recommendation="Pastikan minimal satu jalur evakuasi bebas hambatan dari setiap area B3 per PP 50/2012",
                ))

        if not has_equipment(room, "evacuation_sign") and "circulation" in tags:
            findings.append(make_finding(
                scan_id=scan_id, domain="ERA", sub_agent="Assembly-Point-Auditor", room=room,
                severity="HIGH", confidence=0.87,
                label_text=f"Tidak ada rambu evakuasi di koridor {room['room_id']}",
                recommendation="Pasang rambu arah evakuasi fotoluminesens per SNI ISO 7010 di setiap koridor",
                eq_type="evacuation_sign",
            ))

    return findings
