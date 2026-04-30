from __future__ import annotations

import base64
import json
import logging
import re
from collections.abc import Mapping

logger = logging.getLogger(__name__)

WAREHOUSE_CATEGORIES = [
    "production_zone",
    "hazmat_storage",
    "loading_dock",
    "forklift_zone",
    "utility_corridor",
    "gowning_room",
    "circulation_corridor",
    "general_area",
]

_VISION_SYSTEM = """\
You are a K3 (Keselamatan dan Kesehatan Kerja / Occupational Safety) inspection AI.
You analyze photographs of industrial warehouse and pharmaceutical manufacturing facilities.
Identify the zone type and any visible safety violations or hazardous conditions.

Return ONLY valid JSON with no additional text."""

_VISION_USER = """\
Analyze this industrial facility photograph.

ZONE TYPES (choose exactly one):
- production_zone: manufacturing floor with machinery, equipment, production lines
- hazmat_storage: chemical/B3 storage with drums, containers, shelving
- loading_dock: truck loading/unloading bay area
- forklift_zone: forklift operating area or blind intersection
- utility_corridor: electrical panels, pipes, utility infrastructure
- gowning_room: PPE/gowning area before entering production
- circulation_corridor: walkways, corridors, aisles
- general_area: general work area not matching above

VISIBLE CONDITIONS TO DETECT (include all that apply):
- spill_present: liquid or chemical spill visible on floor
- blocked_fire_extinguisher: fire extinguisher is obstructed or inaccessible
- blocked_emergency_exit: emergency exit door is blocked by objects
- blocked_electrical_panel: electrical panel is blocked or covered
- blocked_emergency_shower: emergency shower is blocked or obstructed
- no_evacuation_sign: no evacuation direction sign visible in corridor area
- blocked_ppe_station: PPE station is blocked, empty, or inaccessible
- no_safety_mirror: no safety mirror at forklift intersection or blind corner
- deformed_rack: damaged, bent, or deformed storage rack or shelving
- improper_chemical_storage: chemicals stored without segregation or secondary containment
- tangled_cords: electrical cords tangled or on floor as tripping hazard
- no_secondary_containment: hazmat area lacks secondary containment (no drip tray/berm)
- scorched_panel: burn marks or scorch damage on electrical panel or wall

Return JSON:
{
  "zone_type": "<zone_type>",
  "confidence": <0.0-1.0>,
  "conditions": ["<condition1>", "<condition2>"],
  "description": "<one sentence describing key safety observations>"
}"""


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def _vision_classify(image_bytes: bytes) -> dict:
    """Call Claude Haiku 4.5 vision to classify zone and detect K3 conditions."""
    try:
        import anthropic
        from backend.config import get_settings

        settings = get_settings()
        if not settings.anthropic_api_key:
            return {}

        b64 = base64.standard_b64encode(image_bytes).decode()
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        msg = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            system=_VISION_SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": _VISION_USER},
                ],
            }],
        )

        for block in msg.content:
            if block.type == "text":
                return json.loads(_strip_fence(block.text))

    except Exception as exc:
        logger.warning("Vision classify failed: %s", exc)

    return {}


async def classify_image(image_bytes: bytes, source: str, metadata: Mapping[str, object] | None = None) -> dict:
    metadata = metadata or {}

    if source == "supplemental_upload" and image_bytes:
        vision = await _vision_classify(image_bytes)
        if vision and vision.get("zone_type") in WAREHOUSE_CATEGORIES:
            return {
                "category": vision["zone_type"],
                "confidence": min(float(vision.get("confidence", 0.82)), 0.98),
                "notes": vision.get("description", ""),
                "source": source,
                "conditions": vision.get("conditions", []),
            }

    # Fallback heuristics for non-supplemental or vision failure
    if source == "street_view":
        heading = int(metadata.get("heading", 0))
        category = "loading_dock" if heading in {135, 180, 225} else "general_area"
        return {"category": category, "confidence": 0.74, "notes": "Street view heuristic", "source": source, "conditions": []}

    if source == "places":
        index = int(metadata.get("index", 1))
        sequence = ["circulation_corridor", "general_area", "production_zone", "hazmat_storage", "loading_dock"]
        category = sequence[(index - 1) % len(sequence)]
        return {"category": category, "confidence": 0.71, "notes": "Places heuristic", "source": source, "conditions": []}

    if source == "supplemental_upload":
        return {"category": "general_area", "confidence": 0.60, "notes": "Vision unavailable — fallback", "source": source, "conditions": []}

    fingerprint = sum(image_bytes) % len(WAREHOUSE_CATEGORIES) if image_bytes else 0
    return {
        "category": WAREHOUSE_CATEGORIES[fingerprint],
        "confidence": round(0.60 + (fingerprint / max(len(WAREHOUSE_CATEGORIES) - 1, 1)) * 0.15, 2),
        "notes": f"Heuristic for {source}",
        "source": source,
        "conditions": [],
    }
