"""PFA — Personnel Flow & Forklift Audit: keselamatan forklift, loading dock, koridor."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model, flow_from_model


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    rooms = rooms_from_model(world_model)
    room_map = {r["room_id"]: r for r in rooms}
    flow = flow_from_model(world_model)

    forklift_paths = flow.get("forklift_paths", [])
    hazmat_zone_ids = {r["room_id"] for r in rooms if r.get("hazmat_present") or "hazmat_zone" in r.get("zone_tags", [])}

    for path in forklift_paths:
        for zone_id in path:
            if zone_id in hazmat_zone_ids:
                room = room_map.get(zone_id)
                if room:
                    findings.append(make_finding(
                        scan_id=scan_id, domain="PFA", sub_agent="Forklift-Pedestrian-Auditor", room=room,
                        severity="HIGH", confidence=0.86,
                        label_text=f"Jalur forklift melewati area B3 {zone_id} — risiko tabrakan + tumpahan kimia",
                        recommendation="Pisahkan jalur forklift dari area B3 atau pasang barrier permanen per SMK3 PP 50/2012",
                    ))

    for room in rooms:
        tags = room.get("zone_tags", [])
        is_forklift = room.get("forklift_access") or "forklift_zone" in tags
        is_loading = "loading_zone" in tags or room.get("type") == "loading_dock"

        if is_forklift:
            if not has_equipment(room, "safety_mirror"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="PFA", sub_agent="Forklift-Pedestrian-Auditor", room=room,
                    severity="CRITICAL", confidence=0.91,
                    label_text=f"Tidak ada cermin keselamatan (safety mirror) di persimpangan forklift {room['room_id']}",
                    recommendation="Pasang cermin cembung di setiap persimpangan buta jalur forklift per SMK3 PP 50/2012",
                    eq_type="safety_mirror",
                ))
            elif not accessible_equipment(room, "safety_mirror"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="PFA", sub_agent="Forklift-Pedestrian-Auditor", room=room,
                    severity="HIGH", confidence=0.84,
                    label_text=f"Safety mirror di {room['room_id']} terhalang — titik buta forklift tidak terpantau",
                    recommendation="Pindahkan penghalang dan pastikan cermin visible dari kedua arah jalur",
                    eq_type="safety_mirror",
                ))

        if is_loading:
            if not has_equipment(room, "dock_safety_light"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="PFA", sub_agent="Loading-Dock-Safety-Auditor", room=room,
                    severity="HIGH", confidence=0.88,
                    label_text=f"Tidak ada lampu sinyal dock di {room['room_id']} — truk tidak terkonfirmasi aman",
                    recommendation="Pasang sistem lampu merah/hijau dock safety light per standar keselamatan bongkar muat",
                    eq_type="dock_safety_light",
                ))

            if not has_equipment(room, "wheel_chock"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="PFA", sub_agent="Loading-Dock-Safety-Auditor", room=room,
                    severity="HIGH", confidence=0.85,
                    label_text=f"Tidak ada wheel chock di loading dock {room['room_id']} — truk bisa bergerak saat bongkar",
                    recommendation="Sediakan wheel chock di setiap bay loading dock per prosedur keselamatan bongkar muat",
                    eq_type="wheel_chock",
                ))

    return findings
