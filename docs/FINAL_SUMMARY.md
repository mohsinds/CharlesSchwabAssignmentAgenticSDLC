# Final engineering summary

## Plan / rationale

We built an agentic SDLC control plane that demonstrates **non-linear, gated orchestration** rather than a linear LLM chain. The URL shortener is the worked example across greenfield, brownfield, and ambiguous inputs.

## Artifacts

- Declarative DAG, Temporal master/stage workflows, FastAPI + React UI  
- LiteLLM-routed stage agents with local prompt fallbacks  
- OPA/Presidio/Guardrails policy gate + layered judge  
- Audit trail (MinIO/FS), Prometheus/Grafana  
- Three scenarios + replay mode  

## Risks / trade-offs / validation

- Autonomy bounded by entry/exit gates and HITL  
- Deterministic validators outrank LLM judge  
- Replay mode de-risks demos without LLM spend  

## Assumptions

- Reviewers run docker-compose locally  
- LiteLLM virtual key `sk-agentic-sdlc-local` for the bundled proxy  
- Single-operator UI (no auth) acceptable for interview scope  

## Limitations

See [LIMITATIONS.md](LIMITATIONS.md). Principle upheld: **agents execute under defined autonomy boundaries; humans own oversight, approvals, and final quality.**
