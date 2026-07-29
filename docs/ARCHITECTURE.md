# Architecture

## Components

1. **Frontend (React)** — prompt intake, live DAG, HITL approval, audit/metrics views.  
2. **API (FastAPI)** — starts workflows, forwards Temporal signals, SSE audit stream. Falls back to an in-process runner when Temporal is unavailable.  
3. **Orchestrator (Temporal)** — `SDLCMasterWorkflow` interprets [`dag/sdlc.yaml`](../dag/sdlc.yaml); `StageWorkflow` runs entry/exit gates + agents.  
4. **Agents (LangGraph-style)** — one graph per stage; all LLM calls via **LiteLLM** OpenAI-compatible API.  
5. **Policy engine** — Presidio → OPA → Guardrails; single entry `policy_gate.check`.  
6. **Judge** — deterministic (ast/ruff/bandit/pytest) → Ragas → LLM-as-judge (never overrides deterministic fail).  
7. **Knowledge** — ingest + embedding retrieval for brownfield (in-memory with hash/LiteLLM embeddings; Postgres/pgvector ready).  
8. **Audit** — canonical events to MinIO with FS circuit-breaker fallback.  
9. **Observability** — Prometheus metrics + Grafana dashboard.

## Control flow

```
User prompt → API → Master workflow
  → classify (on_result branch)
  → [clarify HITL | codebase_ingest | requirement]
  → design → parallel plan nodes
  → implementation (retry + compensation) → test → docs
  → release_review HITL → terminal
```

## Key decisions

- **Declarative DAG** — workflow code does not hardcode stage order.  
- **Determinism boundary** — Temporal workflows never call LiteLLM/IO.  
- **LiteLLM proxy** — provider keys stay in the proxy; agents only see `LITELLM_BASE_URL` + virtual key.  
- **Local-first** — docker-compose is the supported runtime for this assessment.

## AWS service alternatives

| Local (compose) | AWS alternative |
|---|---|
| Temporal + worker | Temporal Cloud on AWS, **or** Step Functions + ECS tasks (lower feature parity), **or** MWAA if Airflow semantics preferred |
| FastAPI `api` / `worker` | ECS Fargate (or EKS) behind an ALB |
| React frontend | S3 + CloudFront, or Amplify Hosting |
| Postgres + pgvector | RDS PostgreSQL with `pgvector`, or OpenSearch for retrieval |
| MinIO | Amazon S3 |
| OPA sidecar | OPA on ECS/EKS; optionally AWS Verified Permissions for coarse authZ |
| LiteLLM proxy | LiteLLM on ECS/Fargate; Bedrock models via LiteLLM providers |
| Prometheus + Grafana | Amazon Managed Prometheus + Amazon Managed Grafana (or CloudWatch) |
| LangSmith | LangSmith Cloud or self-host on ECS |
| Secrets in `.env` | AWS Secrets Manager / SSM Parameter Store |
| Local disk artifacts | S3 versioned bucket or EFS |

Production would also add authN/Z, multi-tenant isolation, and stronger sandboxing for generated code execution.
