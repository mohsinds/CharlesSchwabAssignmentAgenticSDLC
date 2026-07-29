"""OPA HTTP client."""

from __future__ import annotations

from typing import Any

import httpx

from services.common.config import get_settings
from services.common.logging import get_logger

logger = get_logger(__name__)

PACKAGE_PATHS = {
    "security": "data/security",
    "change_control": "data/change_control",
    "code_standards": "data/code_standards",
    "pii": "data/pii",
}


class OPAClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or get_settings().opa_url).rstrip("/")

    async def evaluate(self, package: str, input_doc: dict[str, Any]) -> dict[str, Any]:
        path = PACKAGE_PATHS.get(package, f"data/{package}")
        url = f"{self.base_url}/v1/{path}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"input": input_doc})
                resp.raise_for_status()
                result = resp.json().get("result", {})
                if isinstance(result, bool):
                    return {"allow": result, "deny": []}
                allow = result.get("allow", True) if isinstance(result, dict) else True
                deny = result.get("deny", []) if isinstance(result, dict) else []
                if isinstance(deny, str):
                    deny = [deny]
                return {"allow": bool(allow), "deny": list(deny or [])}
        except Exception as exc:  # noqa: BLE001 — fail closed with local fallback
            logger.warning("opa_unavailable", error=str(exc), package=package)
            return self._local_fallback(package, input_doc)

    def _local_fallback(self, package: str, input_doc: dict[str, Any]) -> dict[str, Any]:
        """Deterministic offline checks when OPA is down (prototype resilience)."""
        content = str(input_doc.get("content") or "")
        denies: list[str] = []
        lower = content.lower()
        if package == "pii":
            import re

            if re.search(r"\b\d{3}-\d{2}-\d{4}\b", content):
                denies.append("SSN-like pattern detected")
        if package == "security":
            if "eval(" in lower:
                denies.append("eval() is forbidden in generated code")
            if "pickle.loads" in lower:
                denies.append("pickle.loads is forbidden")
            if input_doc.get("requires_destructive") and not input_doc.get("approved"):
                denies.append("destructive change requires explicit approval")
        if package == "change_control":
            if (
                input_doc.get("stage_id") == "release_review"
                and input_doc.get("phase") == "exit"
                and not input_doc.get("hitl_approved")
            ):
                denies.append("release_review requires human approval before exit")
            if (
                input_doc.get("stage_id") == "implementation"
                and input_doc.get("phase") == "entry"
                and not input_doc.get("design_present", True)
            ):
                denies.append("implementation entry requires design artifact")
        if package == "code_standards":
            if input_doc.get("ast_ok") is False:
                denies.append("AST parse failed")
            if input_doc.get("ruff_ok") is False:
                denies.append("ruff lint failed")
            if input_doc.get("pytest_ok") is False:
                denies.append("pytest failed")
            cov = input_doc.get("coverage")
            cov_min = input_doc.get("coverage_min")
            if cov is not None and cov_min is not None and cov < cov_min:
                denies.append(f"coverage {cov:.2f} below minimum {cov_min:.2f}")
        return {"allow": len(denies) == 0, "deny": denies}
