from __future__ import annotations

from backend.config import get_settings


def get_llm_provider():
    """Return the appropriate LLM provider based on config.

    Priority: Azure OpenAI → OpenAI direct → Synthetic (fallback)
    """
    s = get_settings()

    if s.use_synthetic_fallbacks:
        from backend.agents.providers.synthetic import SyntheticProvider
        return SyntheticProvider()

    if s.azure_openai_api_key and s.azure_openai_endpoint:
        from backend.agents.providers.azure_openai_provider import AzureOpenAIProvider
        return AzureOpenAIProvider()

    if s.openai_api_key:
        from backend.agents.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()

    from backend.agents.providers.synthetic import SyntheticProvider
    return SyntheticProvider()
