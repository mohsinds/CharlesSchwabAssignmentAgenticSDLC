# ADR 0001: Temporal vs Airflow

## Status

Accepted

## Context

We need durable, signal-driven orchestration with HITL pauses, child workflows, and saga compensation.

## Decision

Use **Temporal** for the orchestration runtime.

## Consequences

- Excellent fit for long-running HITL and retries  
- Requires Temporal server in compose  
- AWS alternative: Temporal Cloud, or Step Functions/MWAA with reduced parity (see ARCHITECTURE.md)
