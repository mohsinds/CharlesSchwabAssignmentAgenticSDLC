"""Policy gate unit tests."""

import pytest

from services.policy_engine.policy_gate import check


@pytest.mark.asyncio
async def test_pii_gate_flags_ssn():
    decision = await check(
        "classify",
        "entry",
        {"content": "Customer SSN is 123-45-6789"},
        gate="pii_check",
    )
    assert decision.allowed is False
    assert decision.redactions or decision.violations


@pytest.mark.asyncio
async def test_clean_prompt_allowed():
    decision = await check(
        "classify",
        "entry",
        {"content": "Build a URL shortener with analytics"},
        gate="pii_check",
    )
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_security_denies_eval():
    decision = await check(
        "implementation",
        "exit",
        {"content": "x = eval(user_input)"},
        gate="policy_check",
    )
    assert decision.allowed is False
