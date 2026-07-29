"""Temporal signal payload helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApproveSignal:
    stage_id: str
    approver: str = "human"
    notes: str = ""


@dataclass
class RejectSignal:
    stage_id: str
    reason: str
    approver: str = "human"


@dataclass
class ReplanSignal:
    from_stage: str
    hint: str = ""


@dataclass
class SafeStopSignal:
    reason: str = "operator_stop"


def signal_to_dict(signal: Any) -> dict[str, Any]:
    if hasattr(signal, "__dataclass_fields__"):
        return {k: getattr(signal, k) for k in signal.__dataclass_fields__}
    if isinstance(signal, dict):
        return signal
    return {"value": str(signal)}
