# Agentic SDLC Platform

Working prototype that turns a natural-language requirement into reviewable engineering artifacts through a **declarative Temporal DAG**, **LangGraph stage agents** (via **LiteLLM**), **policy gates** (OPA / Presidio / Guardrails), and a **React** control UI.

## Quick start (local)

```bash
cp .env.example .env
# Optional for live LLM: set OPENAI_API_KEY (consumed by LiteLLM container)
make install          # python package + frontend deps
make seed
# Option A — full stack
make up
# Option B — API only (falls back to in-process runner if Temporal is down)
pip install -e ".[dev]"
uvicorn services.api.main:app --reload --port 8000
cd frontend && npm run dev
```

- UI: http://localhost:5173  
- API docs: http://localhost:8000/docs  
- Temporal UI: http://localhost:8088  
- Grafana: http://localhost:3001 (admin/admin)  
- LiteLLM: http://localhost:4000  

**Replay mode** (default in UI) runs the DAG without calling LiteLLM — use for demos/CI.

```bash
make demo-greenfield
```

## What you get

| Layer | Tech |
|---|---|
| UI | React + Vite + Tailwind |
| API | FastAPI + SSE |
| Orchestration | Temporal + `dag/sdlc.yaml` |
| Agents | LangGraph-style stage graphs via LiteLLM |
| Policy | OPA Rego, Presidio, Guardrails shim |
| Audit | MinIO + local FS circuit breaker |
| Metrics | Prometheus + Grafana |

## Scenarios

1. **Greenfield** — build a URL shortener  
2. **Brownfield** — rate limit + Redis on `scenarios/brownfield/seed_repo`  
3. **Ambiguous** — “enterprise-ready” → HITL clarifier → replan  

See [docs/SCENARIOS.md](docs/SCENARIOS.md) and [docs/SETUP.md](docs/SETUP.md).

## AWS alternatives (docs only)

This prototype is **local docker-compose only**. Mapping to AWS services is documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#aws-service-alternatives).

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Orchestration](docs/ORCHESTRATION.md)
- [Governance](docs/GOVERNANCE.md)
- [Observability](docs/OBSERVABILITY.md)
- [Testing](docs/TESTING.md)
- [Limitations](docs/LIMITATIONS.md)
- [Final summary](docs/FINAL_SUMMARY.md)
