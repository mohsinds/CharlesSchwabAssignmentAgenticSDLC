# Orchestration

## Declarative DAG

Source of truth: [`dag/sdlc.yaml`](../dag/sdlc.yaml), validated by [`dag/schema.json`](../dag/schema.json).

Loader: `services/orchestrator/dag_loader.py` — stages, `on_result` branches, `parallel_after`, `depends_on`, HITL, retry, compensation.

## Temporal model

- **Master** (`SDLCMasterWorkflow`) — walks the DAG, starts child `StageWorkflow`s, handles `replan` / `safe_stop`, runs saga compensations on failure.  
- **Stage** (`StageWorkflow`) — entry gates → work (agent/activity) → exit gates → bounded retry → HITL when required.  
- **Signals** — `approve`, `reject`, `replan`, `safe_stop`.  
- **Compensation** — e.g. `revert_files` for implementation.

## Gates

Never silently skipped. Failure → retry (if configured) → HITL escalate → compensate → safe-stop.

## Replanning

`requirement` is a `replan_target`. Ambiguous path: classify → clarify (HITL) → requirement with refined prompt. Master also accepts a `replan` signal.

## Replay mode

`mode=replay` emits stage audit events (and optional `scenarios/*/replay.json`) without LLM calls, and **materializes the expected URL-shortener artifacts** under `artifacts/{run_id}/` so offline demos still produce reviewable outputs.
