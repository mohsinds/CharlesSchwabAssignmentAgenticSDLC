"""Unit tests for audit event schema and circuit breaker."""

from services.audit.circuit_breaker import BreakerState, CircuitBreaker
from services.audit.event_schema import AuditEvent, EventType


def test_event_object_key():
    e = AuditEvent(event_type=EventType.PIPELINE_STARTED, run_id="r1", stage_id="classify")
    key = e.object_key()
    assert key.startswith("r1/classify/")
    assert key.endswith(".json")


def test_circuit_breaker_opens():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=60)
    assert cb.allow()
    cb.record_failure()
    assert cb.state == BreakerState.CLOSED
    cb.record_failure()
    assert cb.state == BreakerState.OPEN
    assert not cb.allow()
