"""Azure OpenAI LLM provider — primary CSE synthesis engine."""
from __future__ import annotations

import json

from openai import AsyncAzureOpenAI

from backend.config import get_settings


class AzureOpenAIProvider:
    def __init__(self) -> None:
        s = get_settings()
        self._client = AsyncAzureOpenAI(
            azure_endpoint=s.azure_openai_endpoint,
            api_key=s.azure_openai_api_key,
            api_version="2024-02-01",
        )
        self._deployment = s.azure_openai_deployment

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.4,
        max_tokens: int = 1000,
    ) -> dict | list:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)

    async def complete_text(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
