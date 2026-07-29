# Agentic SDLC Platform

> Interview assignment prototype — [requirements.md](requirements.md)

A working **agentic software engineering system** that turns a natural-language requirement into reviewable engineering artifacts. The worked example is a **URL shortener** service, executed end-to-end under controlled agent autonomy with human oversight.

**Principle:** Agents execute under defined autonomy boundaries; humans own oversight, approvals, and final quality.

---

## About the project

This prototype demonstrates the full SDLC lifecycle as an **orchestrated, gated, non-linear workflow** — not a simple linear LLM chain.

| Assignment requirement | How this repo addresses it |
|---|---|
| Requirement understanding | Classifier + requirement analyst normalize intent; ambiguous inputs route to HITL clarification |
| Task decomposition | Declarative DAG (`dag/sdlc.yaml`) with dependencies, branching, and parallel plan nodes |
| Codebase reasoning (brownfield) | Ingest + retrieval over `scenarios/brownfield/seed_repo` before design/implementation |
| Workflow orchestration | Temporal master/stage workflows interpret an explicit dependency graph with entry/exit gates |
| Engineering output | Code, tests, API/docs under `artifacts/{run_id}/` |
| Validation & risk control | OPA / Presidio / Guardrails + deterministic judges (ast, ruff, bandit, pytest) before LLM-as-judge |
| Controlled autonomy | HITL for clarify + release; bounded retries, compensation, safe-stop, replan |
| Final engineering summary | [docs/FINAL_SUMMARY.md](docs/FINAL_SUMMARY.md) |

### Scope covered

- **Greenfield** — build a URL shortener from scratch  
- **Brownfield** — enhance an existing seed service (rate limiting / Redis)  
- **Ambiguous** — vague “enterprise-ready” prompt → clarify → replan → build  

---

## How it works

```
User prompt (UI / API)
        │
        ▼
   FastAPI  ──starts──►  Temporal SDLCMasterWorkflow
        │                      │
        │                      ▼
        │              Interprets dag/sdlc.yaml
        │                      │
        │         ┌────────────┼────────────┐
        │         ▼            ▼            ▼
        │    classify    (branch on result)
        │         │
        │         ├─ ambiguous  → clarify (HITL) → requirement
        │         ├─ brownfield → codebase_ingest → requirement
        │         └─ greenfield → requirement
        │                              │
        │                              ▼
        │                           design
        │                              │
        │              ┌───────────────┴───────────────┐
        │              ▼                               ▼
        │     implementation_plan               test_plan
        │              │                               │
        │              └───────────┬───────────────────┘
        │                          ▼
        │                   implementation  (retry + compensation)
        │                          │
        │                          ▼
        │                        test → documentation → release_review (HITL)
        │
        ▼
   Artifacts in artifacts/{run_id}/
   Audit events → MinIO (FS fallback)
   Metrics → Prometheus / Grafana
```

### Control plane pieces

1. **Declarative DAG** — [`dag/sdlc.yaml`](dag/sdlc.yaml) is the source of truth for stages, `on_result` branches, `depends_on`, `parallel_after`, gates, retries, and HITL. Workflows interpret it at runtime; stage order is not hardcoded.
2. **Temporal orchestration** — `SDLCMasterWorkflow` walks the DAG and starts child `StageWorkflow`s. Each stage: **entry gates → agent/activity → exit gates** (never silently skipped).
3. **Stage agents** — LangGraph-style graphs (classifier, requirement analyst, architect, implementer, tester, documenter). All LLM traffic goes through **LiteLLM**; prompts live in [`prompts/`](prompts/).
4. **Policy & validation** — Presidio → OPA (Rego) → Guardrails on gates; deterministic validators outrank LLM-as-judge.
5. **Human-in-the-loop** — Temporal signals (`approve`, `reject`, `replan`, `safe_stop`) for high-impact steps.
6. **Audit & metrics** — Canonical audit events; success/retry/rollback/latency tracked in Prometheus.

### Modes

| Mode | Behavior |
|---|---|
| **Replay** | Offline demo/CI path — no LLM calls; still materializes expected URL-shortener artifacts under `artifacts/{run_id}/` |
| **Live** | Full agent path via LiteLLM (requires upstream API key in the LiteLLM container) |

If Temporal is unreachable, the API falls back to an **in-process local runner** so UI demos still work.

---

## Quick start

```bash
cp .env.example .env
# Optional for Live mode: set OPENAI_API_KEY (consumed by LiteLLM only)

make install          # Python package + frontend deps
make seed
make up               # full docker-compose stack
```

Or API + UI only (local runner if Temporal is down):

```bash
pip install -e ".[dev]"
uvicorn services.api.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

| Service | URL |
|---|---|
| UI | http://localhost:5173 |
| API docs | http://localhost:8000/docs |
| Temporal UI | http://localhost:8088 |
| Grafana | http://localhost:3001 (`admin` / `admin`) |
| LiteLLM | http://localhost:4000 |

Demo scripts:

```bash
make demo-greenfield
make demo-brownfield
make demo-ambiguous
```

Full setup notes: **[docs/SETUP.md](docs/SETUP.md)**

---

## Stack

| Layer | Tech |
|---|---|
| UI | React + Vite + Tailwind |
| API | FastAPI + SSE |
| Orchestration | Temporal + declarative `dag/sdlc.yaml` |
| Agents | Stage graphs via LiteLLM |
| Policy | OPA Rego, Presidio, Guardrails shim |
| Audit | MinIO + local FS circuit breaker |
| Metrics | Prometheus + Grafana |
| Artifacts | `./artifacts/{run_id}/` (bind-mounted in compose) |

---

## Scenarios

1. **Greenfield** — build a URL shortener (`POST /shorten`, redirect, analytics, health)  
2. **Brownfield** — rate limit + Redis on [`scenarios/brownfield/seed_repo`](scenarios/brownfield/seed_repo)  
3. **Ambiguous** — “enterprise-ready” → HITL clarifier → replan into a concrete build  

Details: **[docs/SCENARIOS.md](docs/SCENARIOS.md)**

---

## Documentation

| Doc | Contents |
|---|---|
| [requirements.md](requirements.md) | Assignment brief (objectives, scope, evaluation) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components, control flow, key decisions, AWS alternatives |
| [docs/ORCHESTRATION.md](docs/ORCHESTRATION.md) | Declarative DAG, Temporal model, gates, replan, replay |
| [docs/GOVERNANCE.md](docs/GOVERNANCE.md) | Policy-as-code, layered validation, HITL |
| [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md) | Audit events, Prometheus/Grafana, LangSmith |
| [docs/SCENARIOS.md](docs/SCENARIOS.md) | Greenfield / brownfield / ambiguous walkthroughs |
| [docs/SETUP.md](docs/SETUP.md) | Prerequisites, env, bring-up, demos |
| [docs/TESTING.md](docs/TESTING.md) | Unit, integration, OPA policy tests |
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | Prototype boundaries and trade-offs |
| [docs/FINAL_SUMMARY.md](docs/FINAL_SUMMARY.md) | Plan, artifacts, risks, assumptions, limitations |

### Architecture decision records

- [ADR 0001 — Temporal vs Airflow](docs/adr/0001-temporal-vs-airflow.md)  
- [ADR 0002 — Declarative DAG](docs/adr/0002-declarative-dag.md)  
- [ADR 0003 — OPA for policy](docs/adr/0003-opa-for-policy.md)  

---

## Testing

```bash
pip install -e ".[dev]"
pytest -q tests/unit tests/integration
# Optional: opa test policies/
```

See **[docs/TESTING.md](docs/TESTING.md)**.

---

## Artifacts & outputs

Successful runs write under `artifacts/{run_id}/`, for example:

- `requirements.json`, `design.json`  
- `url_shortener/app.py`, `url_shortener/test_app.py`, `url_shortener/README.md`  
- `test_report.json`, `API.md`  

Audit trail: MinIO bucket `sdlc-audit` (primary) or `./data/audit` (fallback).

---

## Limitations

This is a **local docker-compose prototype**, not a production multi-tenant platform (no authN/Z, hardened sandbox, or managed Temporal cluster). AWS service mapping is documented only — see [Architecture → AWS alternatives](docs/ARCHITECTURE.md#aws-service-alternatives) and [docs/LIMITATIONS.md](docs/LIMITATIONS.md).
