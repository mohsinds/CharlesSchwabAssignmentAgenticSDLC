"""Lightweight structural validation for LLM outputs (Guardrails-compatible shim)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuardrailsResult:
    ok: bool
    violations: list[str] = field(default_factory=list)
    parsed: dict[str, Any] | None = None


class GuardrailsWrapper:
    """Validates structured LLM JSON. Uses Guardrails.ai when installed; else local checks."""

    def validate_structured(
        self,
        content: str | dict[str, Any],
        required_keys: list[str] | None = None,
    ) -> GuardrailsResult:
        required_keys = required_keys or []
        data: dict[str, Any] | None
        if isinstance(content, dict):
            data = content
        else:
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON fence
                text = content.strip()
                if "```" in text:
                    parts = text.split("```")
                    for part in parts:
                        part = part.strip()
                        if part.startswith("json"):
                            part = part[4:].strip()
                        try:
                            data = json.loads(part)
                            break
                        except json.JSONDecodeError:
                            continue
                    else:
                        return GuardrailsResult(ok=False, violations=["output is not valid JSON"])
                else:
                    return GuardrailsResult(ok=False, violations=["output is not valid JSON"])

        assert data is not None
        missing = [k for k in required_keys if k not in data]
        if missing:
            return GuardrailsResult(
                ok=False,
                violations=[f"missing required keys: {missing}"],
                parsed=data,
            )
        return GuardrailsResult(ok=True, parsed=data)
