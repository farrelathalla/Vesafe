"""Penanganan B3 — penyimpanan bahan berbahaya, MSDS/SDS, ventilasi area kimia."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    for room in rooms_from_model(world_model):
        if room.get("type") not in {"chemical_storage_area", "quality_control_lab", "production_floor"}:
            continue

        if not has_equipment(room, "safety_cabinet"):
            findings.append(make_finding(
                scan_id=scan_id, domain="MSA", sub_agent="B3-Storage-Auditor", room=room,
                severity="HIGH", confidence=0.89,
                label_text=f"Tidak ada lemari penyimpanan B3 di {room['room_id']}",
                recommendation="Pasang safety cabinet B3 per PP No. 74/2001 dan Permenaker No. 187/MEN/1999",
                eq_type="safety_cabinet",
            ))
        elif not accessible_equipment(room, "safety_cabinet"):
            findings.append(make_finding(
                scan_id=scan_id, domain="MSA", sub_agent="B3-Storage-Auditor", room=room,
                severity="HIGH", confidence=0.86,
                label_text=f"Lemari B3 di {room['room_id']} terhalang atau tidak berlabel GHS",
                recommendation="Bersihkan akses dan lengkapi label GHS/SDS per Permenaker No. 187/MEN/1999",
                eq_type="safety_cabinet",
            ))

        if not has_equipment(room, "workstation"):
            findings.append(make_finding(
                scan_id=scan_id, domain="MSA", sub_agent="MSDS-Compliance-Checker", room=room,
                severity="ADVISORY", confidence=0.74,
                label_text=f"Tidak ada stasiun MSDS/SDS di {room['room_id']} — informasi B3 tidak accessible",
                recommendation="Sediakan akses MSDS/SDS fisik atau digital di setiap area kerja B3 per PP 74/2001",
                eq_type="workstation",
            ))

    return findings
