"""Unified policy gate: Presidio → OPA → Guardrails."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.common.config import get_settings
from services.policy_engine.guardrails_wrapper import GuardrailsWrapper
from services.policy_engine.opa_client import OPAClient
from services.policy_engine.presidio_wrapper import PresidioWrapper

GATE_TO_PACKAGES: dict[str, list[str]] = {
    "pii_check": ["pii"],
    "policy_check": ["security", "change_control"],
    "final_policy_check": ["security", "change_control", "code_standards"],
    "structural_validation": [],
    "judge_requirement": [],
    "judge_design": [],
    "judge_code": [],
    "ast_parse": ["code_standards"],
    "ruff": ["code_standards"],
    "bandit": ["code_standards"],
    "pytest_run": ["code_standards"],
    "coverage_min": ["code_standards"],
}


@dataclass
class PolicyDecision:
    allowed: bool
    violations: list[str] = field(default_factory=list)
    requires_hitl: bool = False
    redactions: dict[str, Any] = field(default_factory=dict)
    redacted_content: str | None = None
    gate: str | None = None
    phase: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class PolicyGate:
    def __init__(self) -> None:
        self.presidio = PresidioWrapper()
        self.opa = OPAClient()
        self.guardrails = GuardrailsWrapper()
        self.settings = get_settings()

    async def check(
        self,
        stage_id: str,
        phase: str,
        payload: dict[str, Any],
        gate: str | None = None,
    ) -> PolicyDecision:
        content = str(payload.get("content") or payload.get("prompt") or "")
        violations: list[str] = []
        redactions: dict[str, Any] = {}
        redacted_content = content

        # 1) Presidio
        pii = self.presidio.analyze(content)
        if pii.findings:
            redactions["pii_entities"] = [f["entity_type"] for f in pii.findings]
            redacted_content = pii.redacted_text
            # Block only on high-risk financial PII for entry prompts
            high_risk = {"US_SSN", "CREDIT_CARD", "US_BANK_NUMBER", "IBAN_CODE"}
            if any(f["entity_type"] in high_risk for f in pii.findings):
                if gate in {None, "pii_check"} or phase == "entry":
                    violations.append("high-risk PII detected; content redacted")

        # 2) OPA packages for this gate
        packages = GATE_TO_PACKAGES.get(gate or "policy_check", ["security", "change_control"])
        opa_input = {
            **payload,
            "stage_id": stage_id,
            "phase": phase,
            "content": redacted_content,
            "coverage_min": payload.get("coverage_min", self.settings.coverage_min),
        }
        for package in packages:
            result = await self.opa.evaluate(package, opa_input)
            if not result.get("allow", True):
                violations.extend(result.get("deny") or [f"{package} denied"])

        # 3) Guardrails for structured LLM outputs on exit
        requires_hitl = bool(payload.get("requires_hitl"))
        if phase == "exit" and payload.get("structured") is not None:
            required = payload.get("required_keys") or []
            gr = self.guardrails.validate_structured(payload["structured"], required)
            if not gr.ok:
                violations.extend(gr.violations)
                requires_hitl = True

        # Structural validation gate: require classification fields
        if gate == "structural_validation":
            structured = payload.get("structured") or {}
            if "classification" not in structured and "verdict" not in structured:
                violations.append("classifier output missing classification/verdict")

        allowed = len(violations) == 0
        if stage_id in {"clarify", "release_review"} and phase == "exit":
            if not payload.get("hitl_approved"):
                requires_hitl = True
                if stage_id == "release_review":
                    allowed = False
                    violations.append("HITL approval required")

        return PolicyDecision(
            allowed=allowed,
            violations=violations,
            requires_hitl=requires_hitl or (not allowed and stage_id in {"clarify", "release_review"}),
            redactions=redactions,
            redacted_content=redacted_content if pii.redacted else None,
            gate=gate,
            phase=phase,
            details={"packages": packages},
        )


_gate: PolicyGate | None = None


def get_policy_gate() -> PolicyGate:
    global _gate
    if _gate is None:
        _gate = PolicyGate()
    return _gate


async def check(stage_id: str, phase: str, payload: dict[str, Any], gate: str | None = None) -> PolicyDecision:
    """Module-level single entry point required by project rules."""
    return await get_policy_gate().check(stage_id, phase, payload, gate=gate)
