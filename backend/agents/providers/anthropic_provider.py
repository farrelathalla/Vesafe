"""Anthropic LLM provider — claude-opus-4-7 with adaptive thinking."""
from __future__ import annotations

import json
import re

import anthropic

from backend.config import get_settings


def _extract_json(text: str) -> dict | list:
    text = text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


class AnthropicProvider:
    def __init__(self, model: str = "claude-opus-4-7") -> None:
        self._model = model
        self._client = anthropic.AsyncAnthropic(api_key=get_settings().anthropic_api_key)

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.4,
        max_tokens: int = 1000,
    ) -> dict | list:
        # Opus 4.7 with adaptive thinking doesn't accept temperature
        kwargs: dict = dict(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            thinking={"type": "adaptive"},
        )
        msg = await self._client.messages.create(**kwargs)
        for block in msg.content:
            if block.type == "text":
                try:
                    return _extract_json(block.text)
                except Exception:
                    return {}
        return {}

    async def complete_text(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        kwargs: dict = dict(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            thinking={"type": "adaptive"},
        )
        msg = await self._client.messages.create(**kwargs)
        for block in msg.content:
            if block.type == "text":
                return block.text
        return ""
