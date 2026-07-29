"""Prometheus reliability metrics."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, Info

PIPELINE_STARTED = Counter(
    "sdlc_pipeline_started_total",
    "Pipelines started",
    ["scenario_type", "mode"],
)
PIPELINE_COMPLETED = Counter(
    "sdlc_pipeline_completed_total",
    "Pipelines completed",
    ["scenario_type", "status"],
)
STAGE_DURATION = Histogram(
    "sdlc_stage_duration_seconds",
    "Stage wall-clock duration",
    ["stage_id", "status"],
    buckets=(1, 5, 15, 30, 60, 120, 300, 600, 1800),
)
RETRY_TOTAL = Counter(
    "sdlc_retry_total",
    "Stage retries",
    ["stage_id"],
)
ROLLBACK_TOTAL = Counter(
    "sdlc_rollback_total",
    "Compensation / rollback invocations",
    ["stage_id", "compensation"],
)
GATE_RESULTS = Counter(
    "sdlc_gate_results_total",
    "Entry/exit gate outcomes",
    ["stage_id", "gate", "phase", "allowed"],
)
HITL_WAITING = Gauge(
    "sdlc_hitl_waiting",
    "Pipelines waiting on human approval",
    ["stage_id"],
)
E2E_LATENCY = Histogram(
    "sdlc_e2e_latency_seconds",
    "End-to-end pipeline latency",
    ["scenario_type"],
    buckets=(30, 60, 120, 300, 600, 1200, 3600),
)
BUILD_INFO = Info("sdlc_build", "Build metadata")
BUILD_INFO.info({"version": "0.1.0"})
