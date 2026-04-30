"""
K3 Domain Swarm — Pharmaceutical Warehouse
===========================================
6 domain swarms, each with 3 parallel sub-agents analyzing the spatial bundle
for occupational safety and health (K3) violations.

Domains:
  ICA: Industrial Chemical Audit — storage, segregation, labeling, containment
  MSA: Material Safety Audit — PPE, MSDS, handling procedures
  FRA: Fire Risk Audit — extinguishers, flammable storage, ignition sources
  ERA: Emergency Response Audit — exits, evacuation routes, alarm systems
  PFA: Personnel Flow & Forklift Audit — pedestrian zones, forklift safety
  SCA: Safety Communication & Signage Audit — K3 signs, LOTO, warnings
"""
from __future__ import annotations

import asyncio

from backend.agents.providers.base import LLMProvider


def _bundle_text(bundle: dict) -> str:
    lines = ["=== PHARMACEUTICAL WAREHOUSE SPATIAL BUNDLE ==="]
    lines.append(f"Facility type: {bundle.get('facility_type', 'pharmaceutical_manufacturing_warehouse')}")

    for room in bundle.get("rooms", []):
        eq_parts = []
        for e in room.get("equipment", []):
            state = "BLOCKED" if not e.get("accessible", True) else "accessible"
            conf = e.get("confidence", 0)
            eq_parts.append(f"{e['type']}({state},conf={conf:.2f})")
        eq_str = "; ".join(eq_parts) or "none"

        tags = room.get("zone_tags", [])
        hazmat = "HAZMAT=YES" if room.get("hazmat_present") else "HAZMAT=NO"
        forklift = "FORKLIFT=YES" if room.get("forklift_access") else "FORKLIFT=NO"
        exit_present = "EXIT=YES" if room.get("has_emergency_exit") else "EXIT=NO"

        lines.append(
            f"  {room['room_id']} type={room['type']} tags={tags} "
            f"{hazmat} {forklift} {exit_present} "
            f"adj={room.get('adjacency', [])} equip=[{eq_str}]"
        )

    hazmat_zones = bundle.get("flow_annotations", {}).get("hazmat_zones", [])
    evac_routes = bundle.get("flow_annotations", {}).get("evacuation_routes", [])
    forklift_paths = bundle.get("flow_annotations", {}).get("forklift_paths", [])

    if hazmat_zones:
        lines.append(f"Hazmat zones: {hazmat_zones}")
    if evac_routes:
        lines.append(f"Evacuation routes: {evac_routes}")
    if forklift_paths:
        lines.append(f"Forklift paths: {forklift_paths}")

    lines.append("=== END BUNDLE ===")
    return "\n".join(lines)


_SCHEMA = """
Respond ONLY with valid JSON: {"findings": [...]}
Each finding must match this schema exactly (0–6 findings max):
{
  "room_id": "<exact room_id from the bundle>",
  "equipment_ref": "<equipment type from the bundle, or omit for zone-level>",
  "severity": "CRITICAL" | "HIGH" | "ADVISORY",
  "confidence": <0.0–1.0>,
  "label_text": "<≤80 chars, in Indonesian/English>",
  "recommendation": "<≤150 chars, actionable K3 corrective action>",
  "evidence": "<1 sentence citing specific bundle data>"
}
RULES:
- Only reference room_ids and equipment types from the bundle.
- Do NOT invent rooms or equipment not in the bundle.
- Be aggressive — flag any missing, blocked, or low-confidence safety equipment.
- Low confidence (<0.75) on safety-critical equipment = at least HIGH severity.
- Return {"findings": []} only if the zone is genuinely fully compliant.
"""


_DOMAINS: dict[str, list[dict]] = {
    "ICA": [
        {
            "sub_agent": "Chemical-Storage-Auditor",
            "system": (
                "You are a K3 chemical storage auditor for a pharmaceutical manufacturing warehouse.\n"
                "Check every zone with HAZMAT=YES or tag 'chemical_storage':\n"
                "- chemical_rack must be present and accessible. Missing = CRITICAL.\n"
                "- secondary_containment must be present under chemical_rack. Missing = CRITICAL.\n"
                "- Any chemical_rack with confidence < 0.80 = HIGH (labeling/segregation risk).\n"
                "- Zones with HAZMAT=YES but no secondary_containment = CRITICAL spill risk.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Chemical-Segregation-Auditor",
            "system": (
                "You are a K3 auditor specializing in chemical segregation compliance.\n"
                "For every hazmat_zone or chemical_storage zone:\n"
                "- Verify secondary_containment is present and accessible. Blocked = CRITICAL.\n"
                "- If a zone has chemical_rack but no spill_kit: flag as HIGH (no spill response).\n"
                "- If a zone is adjacent to a forklift_zone without a corridor buffer: HIGH (collision + spill risk).\n"
                "- Zones with hazmat_present=YES and no emergency_shower within adjacency: HIGH.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Spill-Response-Auditor",
            "system": (
                "You are a K3 auditor checking spill response readiness in a pharmaceutical warehouse.\n"
                "For every zone with HAZMAT=YES:\n"
                "- spill_kit must be present AND accessible. Missing = CRITICAL. Blocked = CRITICAL.\n"
                "- emergency_shower must be accessible within the zone or adjacent zone. Missing = HIGH.\n"
                "- If spill_kit confidence < 0.75: flag as HIGH (kit may be depleted or missing).\n"
                "- If emergency_shower confidence < 0.75: flag as HIGH.\n"
                + _SCHEMA
            ),
        },
    ],
    "MSA": [
        {
            "sub_agent": "PPE-Station-Auditor",
            "system": (
                "You are a K3 PPE compliance auditor for a pharmaceutical warehouse.\n"
                "Every zone tagged 'production_zone', 'hazmat_zone', or 'ppe_required' must have:\n"
                "- ppe_station present and accessible. Missing = CRITICAL.\n"
                "- ppe_station with confidence < 0.80 = HIGH (station may be empty or inadequate).\n"
                "- Zones adjacent to hazmat_zone without their own ppe_station = HIGH.\n"
                "- loading_zone without ppe_station = HIGH.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Hazmat-Handling-Auditor",
            "system": (
                "You are a K3 auditor for hazardous material handling procedures.\n"
                "Check all hazmat_zone and chemical_storage zones:\n"
                "- Any zone with HAZMAT=YES and no spill_kit = CRITICAL.\n"
                "- Any zone with chemical_rack but BLOCKED secondary_containment = CRITICAL.\n"
                "- Forklift zones adjacent to hazmat zones without safety_mirror = HIGH (blind approach risk).\n"
                "- Any equipment with confidence < 0.70 in a hazmat zone = HIGH.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Emergency-Shower-Auditor",
            "system": (
                "You are a K3 auditor checking emergency decontamination equipment.\n"
                "For every zone with HAZMAT=YES or 'chemical_storage' tag:\n"
                "- emergency_shower must be present and accessible. Missing = CRITICAL.\n"
                "- Blocked emergency_shower = CRITICAL (cannot reach during chemical exposure).\n"
                "- emergency_shower with confidence < 0.75 = HIGH.\n"
                "- If no emergency_shower in zone OR adjacent zones: CRITICAL.\n"
                + _SCHEMA
            ),
        },
    ],
    "FRA": [
        {
            "sub_agent": "Fire-Extinguisher-Auditor",
            "system": (
                "You are a K3 fire safety auditor for a pharmaceutical manufacturing warehouse.\n"
                "Every zone must have at least one fire_extinguisher present and accessible:\n"
                "- Missing fire_extinguisher in any zone = CRITICAL.\n"
                "- Blocked fire_extinguisher = CRITICAL (cannot reach during fire).\n"
                "- fire_extinguisher with confidence < 0.75 = HIGH (may be discharged or missing).\n"
                "- Zones with HAZMAT=YES need fire_extinguisher with confidence > 0.85. Lower = HIGH.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Flammable-Storage-Auditor",
            "system": (
                "You are a K3 fire risk auditor specializing in flammable material storage.\n"
                "Check all hazmat_zone and chemical_storage zones for fire risk:\n"
                "- Zones with chemical_rack (flammable chemicals) adjacent to forklift_zone: HIGH (ignition risk).\n"
                "- charging_station in forklift zones must be present. If accessible=BLOCKED: CRITICAL (hydrogen gas).\n"
                "- Any hazmat zone without fire_extinguisher within the zone or adjacent zone: CRITICAL.\n"
                "- chemical_rack with confidence < 0.80 in a zone with forklift_access: HIGH.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Ignition-Source-Auditor",
            "system": (
                "You are a K3 auditor checking ignition source control near flammables.\n"
                "- forklift_zone adjacent to chemical_storage without safety_mirror: HIGH.\n"
                "- electrical_panel in utility zones must be accessible. Blocked = CRITICAL.\n"
                "- electrical_panel with confidence < 0.75 in any zone = HIGH (panel damage risk).\n"
                "- charging_station near chemical_rack without secondary_containment: HIGH.\n"
                + _SCHEMA
            ),
        },
    ],
    "ERA": [
        {
            "sub_agent": "Emergency-Exit-Auditor",
            "system": (
                "You are a K3 emergency evacuation auditor for a pharmaceutical warehouse.\n"
                "Every zone must have an accessible emergency_exit reachable via adjacency:\n"
                "- Zone with EXIT=NO and no adjacent zone with EXIT=YES = CRITICAL.\n"
                "- emergency_exit with accessible=BLOCKED = CRITICAL (evacuation blocked).\n"
                "- emergency_exit with confidence < 0.80 = HIGH (sign or door may be obstructed).\n"
                "- Zones with HAZMAT=YES must have emergency_exit in zone or directly adjacent. Missing = CRITICAL.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Evacuation-Route-Auditor",
            "system": (
                "You are a K3 auditor checking evacuation route integrity.\n"
                "Using the evacuation_routes in flow_annotations and nav_edges:\n"
                "- If any zone on an evacuation route has a BLOCKED emergency_exit: CRITICAL.\n"
                "- If a hazmat_zone has only one exit route (no alternative path): HIGH.\n"
                "- circulation zones without evacuation_sign: HIGH.\n"
                "- evacuation_sign with confidence < 0.80: HIGH.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Assembly-Point-Auditor",
            "system": (
                "You are a K3 auditor checking emergency assembly point access.\n"
                "- loading_zone must have dock_safety_light. Missing = HIGH.\n"
                "- Zones with forklift_access and no safety_mirror = HIGH (collision during evacuation).\n"
                "- Any zone with HAZMAT=YES that has no nav_edge path to a loading_zone or exit: CRITICAL.\n"
                "- If evacuation_routes in flow_annotations is empty: HIGH (no defined route).\n"
                + _SCHEMA
            ),
        },
    ],
    "PFA": [
        {
            "sub_agent": "Forklift-Pedestrian-Auditor",
            "system": (
                "You are a K3 auditor for forklift and pedestrian safety separation.\n"
                "For every zone with FORKLIFT=YES or tag 'forklift_zone':\n"
                "- safety_mirror must be present at any intersection or corner. Missing = CRITICAL.\n"
                "- safety_mirror with accessible=BLOCKED or confidence < 0.75 = HIGH.\n"
                "- Forklift zones directly adjacent to production_zone without circulation buffer: HIGH.\n"
                "- If forklift_paths in flow_annotations pass through a hazmat_zone: HIGH.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Loading-Dock-Safety-Auditor",
            "system": (
                "You are a K3 auditor for loading dock operations safety.\n"
                "For every zone with type 'loading_dock' or tag 'loading_zone':\n"
                "- dock_safety_light must be present and accessible. Missing = HIGH.\n"
                "- wheel_chock must be present. Missing = HIGH (vehicle rollaway risk).\n"
                "- fire_extinguisher must be accessible at the dock. Missing = HIGH.\n"
                "- Any loading zone with FORKLIFT=YES but no safety_mirror: HIGH.\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Circulation-Safety-Auditor",
            "system": (
                "You are a K3 auditor for personnel circulation and movement safety.\n"
                "For every circulation_corridor zone:\n"
                "- emergency_exit must be present and accessible. Missing = CRITICAL.\n"
                "- evacuation_sign must be present. Missing = HIGH.\n"
                "- fire_extinguisher must be present. Missing = HIGH.\n"
                "- If a corridor is the only connection between hazmat_zone and a loading_zone: HIGH.\n"
                + _SCHEMA
            ),
        },
    ],
    "SCA": [
        {
            "sub_agent": "K3-Signage-Auditor",
            "system": (
                "You are a K3 safety signage compliance auditor for a pharmaceutical warehouse.\n"
                "Check signage adequacy across all zones:\n"
                "- Any hazmat_zone without evacuation_sign in zone or adjacent circulation: HIGH.\n"
                "- evacuation_sign with confidence < 0.80: HIGH (sign may be missing or obscured).\n"
                "- Any zone with HAZMAT=YES missing ppe_station or spill_kit: CRITICAL (no response guidance).\n"
                "- loading_zone missing dock_safety_light: HIGH (no signal for truck safety).\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "LOTO-Electrical-Auditor",
            "system": (
                "You are a K3 auditor for lockout/tagout (LOTO) and electrical safety.\n"
                "For every utility_zone or zone with electrical_panel:\n"
                "- electrical_panel must be accessible. Blocked = CRITICAL.\n"
                "- electrical_panel with confidence < 0.75 = HIGH (panel damage or door open).\n"
                "- charging_station in forklift zones must be accessible. Blocked = CRITICAL.\n"
                "- Any zone with electrical_panel adjacent to chemical_rack: HIGH (electrical + chemical risk).\n"
                + _SCHEMA
            ),
        },
        {
            "sub_agent": "Safety-Equipment-Completeness-Auditor",
            "system": (
                "You are a K3 auditor doing a completeness check of all safety equipment.\n"
                "Audit every zone systematically:\n"
                "- Count zones with HAZMAT=YES that have no fire_extinguisher: each = CRITICAL.\n"
                "- Count zones with HAZMAT=YES that have no spill_kit: each = CRITICAL.\n"
                "- Count zones with FORKLIFT=YES that have no safety_mirror: each = HIGH.\n"
                "- Count zones with EXIT=NO and no adjacent EXIT=YES zone: each = CRITICAL.\n"
                "- Any equipment with confidence < 0.70 anywhere = HIGH (likely missing or non-functional).\n"
                + _SCHEMA
            ),
        },
    ],
}


async def _run_sub_agent(
    provider: LLMProvider,
    domain: str,
    agent_def: dict,
    bundle_text: str,
) -> list[dict]:
    user = (
        f"Analyze this pharmaceutical warehouse spatial bundle for K3 domain {domain}, "
        f"sub-agent role '{agent_def['sub_agent']}':\n\n{bundle_text}"
    )
    try:
        result = await provider.complete_json(
            agent_def["system"],
            user,
            temperature=0.2,
            max_tokens=1200,
        )
        candidates: list = result.get("findings", []) if isinstance(result, dict) else result
    except Exception:
        return []

    for c in candidates:
        c["domain"] = domain
        c["sub_agent"] = agent_def["sub_agent"]

    return candidates


async def run_domain_swarm(
    provider: LLMProvider,
    domain: str,
    bundle: dict,
) -> list[dict]:
    agent_defs = _DOMAINS.get(domain, [])
    if not agent_defs:
        return []

    text = _bundle_text(bundle)
    tasks = [_run_sub_agent(provider, domain, a, text) for a in agent_defs]
    results = await asyncio.gather(*tasks)
    return [c for sub in results for c in sub]


DOMAIN_AGENTS = _DOMAINS
