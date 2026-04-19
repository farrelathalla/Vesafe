"""Komunikasi K3 — pos keselamatan, rambu K3, sistem komunikasi darurat."""
from __future__ import annotations

from backend.agents.team_utils import has_equipment, make_finding, rooms_from_model

_WORK_ZONES = {"production_floor", "warehouse_storage", "chemical_storage_area",
               "quality_control_lab", "utility_room"}


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    rooms = rooms_from_model(world_model)
    safety_posts = [r for r in rooms if r.get("type") == "nursing_station"]
    work_rooms   = [r for r in rooms if r.get("type") in _WORK_ZONES]

    if not safety_posts:
        for room in work_rooms:
            findings.append(make_finding(
                scan_id=scan_id, domain="SCA", sub_agent="SafetyPost-Auditor", room=room,
                severity="HIGH", confidence=0.86,
                label_text=f"Tidak ada pos K3 — {room['room_id']} tidak memiliki pusat informasi keselamatan",
                recommendation="Dirikan pos K3 terpusat per SMK3 PP No. 50/2012 elemen 6",
            ))
        return findings

    for sp in safety_posts:
        if not has_equipment(sp, "workstation"):
            findings.append(make_finding(
                scan_id=scan_id, domain="SCA", sub_agent="SafetyPost-Auditor", room=sp,
                severity="HIGH", confidence=0.88,
                label_text=f"Pos K3 {sp['room_id']} tidak memiliki workstation — dokumentasi K3 tidak tersedia",
                recommendation="Pasang workstation dengan akses MSDS, prosedur darurat per SMK3 PP 50/2012",
                eq_type="workstation",
            ))

    for room in work_rooms:
        no_sightline = not room.get("sightline_to_nursing_station", True)
        no_calllight  = not has_equipment(room, "call_light")
        if no_sightline and no_calllight:
            findings.append(make_finding(
                scan_id=scan_id, domain="SCA", sub_agent="EmergencyComms-Checker", room=room,
                severity="CRITICAL", confidence=0.94,
                label_text=f"{room['room_id']}: tidak ada sightline ke pos K3 DAN tidak ada alarm darurat",
                recommendation="Pasang alarm darurat + intercom segera per SMK3 PP 50/2012 dan ISO 45001:2018 §8.2",
                eq_type="call_light",
            ))

    return findings
