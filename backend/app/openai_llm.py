"""Shared ChatOpenAI settings (timeouts) for agents hitting slow or flaky networks."""
from __future__ import annotations

from langchain_openai import ChatOpenAI

# Default OpenAI httpx client can raise ConnectTimeout / APITimeoutError on slow paths.
OPENAI_REQUEST_TIMEOUT_S = 120.0
OPENAI_MAX_RETRIES = 2


def chat_openai_mini(*, temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        timeout=OPENAI_REQUEST_TIMEOUT_S,
        max_retries=OPENAI_MAX_RETRIES,
    )
