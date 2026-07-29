"""Prompt loader — LangSmith Hub canonical, local /prompts fallback."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from services.common.config import get_settings
from services.common.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=64)
def get(name: str, version: str | None = None) -> str:
    settings = get_settings()
    if settings.langsmith_api_key and settings.langsmith_tracing:
        try:
            from langsmith import Client

            client = Client()
            # Hub path convention: agentic-sdlc/{name}
            prompt = client.pull_prompt(f"agentic-sdlc/{name}")
            if prompt:
                return str(prompt)
        except Exception as exc:  # noqa: BLE001
            logger.warning("langsmith_prompt_pull_failed", name=name, error=str(exc))

    path = Path(settings.prompts_dir) / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"You are the {name} agent for an agentic SDLC pipeline. Do your single job well."
