"""FRA — Fire Risk Audit: APAR, penyimpanan flammable, sumber ignisi."""
from __future__ import annotations

from backend.agents.team_utils import accessible_equipment, has_equipment, make_finding, rooms_from_model


async def run(scan_id: str, world_model: dict) -> list[dict]:
    findings: list[dict] = []
    rooms = rooms_from_model(world_model)
    has_any_apar = any(has_equipment(r, "fire_extinguisher") for r in rooms)

    for room in rooms:
        zone_type = room.get("type", "")
        tags = room.get("zone_tags", [])
        is_hazmat = room.get("hazmat_present") or "hazmat_zone" in tags
        is_forklift = room.get("forklift_access") or "forklift_zone" in tags

        if not has_any_apar:
            findings.append(make_finding(
                scan_id=scan_id, domain="FRA", sub_agent="APAR-Mapper", room=room,
                severity="CRITICAL", confidence=0.97,
                label_text=f"Tidak ada APAR ditemukan di fasilitas — {room['room_id']} tidak terlindungi",
                recommendation="Pasang APAR dengan jarak ≤15m antar titik per Permenaker No. 04/MEN/1980",
                eq_type="fire_extinguisher",
            ))
        elif has_equipment(room, "fire_extinguisher") and not accessible_equipment(room, "fire_extinguisher"):
            findings.append(make_finding(
                scan_id=scan_id, domain="FRA", sub_agent="APAR-Mapper", room=room,
                severity="CRITICAL", confidence=0.92,
                label_text=f"APAR di {room['room_id']} terhalang — tidak dapat diakses saat kebakaran",
                recommendation="Bersihkan area APAR min 1m, pasang tanda lantai merah per Permenaker 04/MEN/1980",
                eq_type="fire_extinguisher",
            ))
        elif not has_equipment(room, "fire_extinguisher") and is_hazmat:
            findings.append(make_finding(
                scan_id=scan_id, domain="FRA", sub_agent="APAR-Mapper", room=room,
                severity="CRITICAL", confidence=0.90,
                label_text=f"Tidak ada APAR di area B3 {room['room_id']} — risiko kebakaran kimia tanpa proteksi",
                recommendation="Pasang APAR jenis dry powder atau CO2 khusus kebakaran kimia per Permenaker 04/MEN/1980",
                eq_type="fire_extinguisher",
            ))

        if is_forklift and has_equipment(room, "charging_station") and not accessible_equipment(room, "charging_station"):
            findings.append(make_finding(
                scan_id=scan_id, domain="FRA", sub_agent="Ignition-Source-Auditor", room=room,
                severity="HIGH", confidence=0.84,
                label_text=f"Charging station forklift di {room['room_id']} terhalang — gas hidrogen tidak terventilasi",
                recommendation="Pastikan charging station bebas hambatan dan ventilasi memadai per SNI 04-6292",
                eq_type="charging_station",
            ))

        if "electrical_panel" in [e.get("type") for e in room.get("equipment", [])]:
            if not accessible_equipment(room, "electrical_panel"):
                findings.append(make_finding(
                    scan_id=scan_id, domain="FRA", sub_agent="Ignition-Source-Auditor", room=room,
                    severity="CRITICAL", confidence=0.89,
                    label_text=f"Panel listrik di {room['room_id']} terhalang — risiko kebakaran listrik tidak terkontrol",
                    recommendation="Bersihkan area panel listrik min 1m per PUIL 2011 dan pasang LOTO procedure",
                    eq_type="electrical_panel",
                ))

    return findings
