"""Simple circuit breaker for MinIO audit writes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0
    failure_count: int = 0
    opened_at: float | None = None
    state: BreakerState = BreakerState.CLOSED
    _half_open_trial: bool = field(default=False, repr=False)

    def allow(self) -> bool:
        if self.state == BreakerState.CLOSED:
            return True
        if self.state == BreakerState.OPEN:
            assert self.opened_at is not None
            if time.monotonic() - self.opened_at >= self.recovery_timeout_seconds:
                self.state = BreakerState.HALF_OPEN
                self._half_open_trial = True
                return True
            return False
        # HALF_OPEN — allow one trial
        return self._half_open_trial

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = BreakerState.CLOSED
        self.opened_at = None
        self._half_open_trial = False

    def record_failure(self) -> None:
        self.failure_count += 1
        self._half_open_trial = False
        if self.failure_count >= self.failure_threshold or self.state == BreakerState.HALF_OPEN:
            self.state = BreakerState.OPEN
            self.opened_at = time.monotonic()
