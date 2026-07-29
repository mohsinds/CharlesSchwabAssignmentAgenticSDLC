# Governance

## Policy as code

Rego packages in [`policies/`](../policies/):

- `security.rego` — dangerous sinks, secrets  
- `change_control.rego` — design required for impl; HITL for release  
- `code_standards.rego` — ast/ruff/pytest/coverage  
- `pii.rego` — pattern deny lists  

Each package has `*_test.rego`.

## Policy gate pipeline

`policy_gate.check(stage_id, phase, payload)`:

1. **Presidio** (financial PII entities) — redact; block high-risk on entry  
2. **OPA** — package set from gate name  
3. **Guardrails shim** — structured JSON validation for LLM outputs  

Offline OPA fallback keeps demos working when the sidecar is down (fail closed on known bad patterns).

## Layered validation

Deterministic validators run first. LLM-as-judge **cannot** override a deterministic failure (`services/judge/scoring.py`).

## Human-in-the-loop

- `clarify` — answers ambiguity before requirement  
- `release_review` — final approval before terminal success  
- API: `POST /signals/{run_id}` with `approve|reject|replan|safe_stop`
