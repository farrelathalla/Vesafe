"""ICA — Industrial Chemical Audit: penyimpanan, segregasi, kontainmen bahan kimia."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model

_HAZMAT_TYPES = {"hazmat_storage", "chemical_storage", "production_zone"}


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    for room in rooms_from_model(world_model):
        zone_type = room.get("type", "")
        tags = room.get("zone_tags", [])
        is_hazmat = zone_type in _HAZMAT_TYPES or "hazmat_zone" in tags or "chemical_storage" in tags

        if not is_hazmat:
            continue

        if not has_equipment(room, "secondary_containment"):
            findings.append(make_finding(
                scan_id=scan_id, domain="ICA", sub_agent="Chemical-Storage-Auditor", room=room,
                severity="CRITICAL", confidence=0.93,
                label_text=f"Tidak ada bak penampung sekunder (secondary containment) di {room['room_id']}",
                recommendation="Pasang bak penampung di bawah semua drum kimia per PP No. 74/2001 Pasal 16",
                eq_type="secondary_containment",
            ))
        elif not accessible_equipment(room, "secondary_containment"):
            findings.append(make_finding(
                scan_id=scan_id, domain="ICA", sub_agent="Chemical-Storage-Auditor", room=room,
                severity="CRITICAL", confidence=0.88,
                label_text=f"Secondary containment di {room['room_id']} terhalang — tumpahan tidak tertampung",
                recommendation="Bersihkan halangan dan pastikan bak penampung bebas dari obstruksi",
                eq_type="secondary_containment",
            ))

        if not has_equipment(room, "spill_kit"):
            findings.append(make_finding(
                scan_id=scan_id, domain="ICA", sub_agent="Spill-Response-Auditor", room=room,
                severity="CRITICAL", confidence=0.91,
                label_text=f"Tidak ada spill kit di area kimia {room['room_id']}",
                recommendation="Sediakan spill kit B3 lengkap dalam radius 10m per Permenaker No. 187/MEN/1999",
                eq_type="spill_kit",
            ))
        elif not accessible_equipment(room, "spill_kit"):
            findings.append(make_finding(
                scan_id=scan_id, domain="ICA", sub_agent="Spill-Response-Auditor", room=room,
                severity="CRITICAL", confidence=0.87,
                label_text=f"Spill kit di {room['room_id']} terhalang — tidak dapat digunakan saat tumpahan",
                recommendation="Pindahkan spill kit ke posisi mudah dijangkau, beri tanda jelas",
                eq_type="spill_kit",
            ))

        if not has_equipment(room, "chemical_rack"):
            findings.append(make_finding(
                scan_id=scan_id, domain="ICA", sub_agent="Chemical-Segregation-Auditor", room=room,
                severity="HIGH", confidence=0.85,
                label_text=f"Tidak ada rak penyimpanan kimia terstruktur di {room['room_id']}",
                recommendation="Sediakan rak kimia dengan pemisah per golongan GHS dan label per PP 74/2001",
                eq_type="chemical_rack",
            ))

    return findings
