# Limitations & trade-offs

- **Prototype, not production** — no authN/Z, multi-tenancy, or hardened code sandbox.  
- **Local-only runtime** — AWS mapping is documentation only.  
- **LiteLLM dependency for live mode** — without upstream keys, agents use deterministic heuristics/fallbacks.  
- **Knowledge store** — in-memory by default; Postgres/pgvector schema is initialized but not required for demos.  
- **Ragas / Guardrails / Presidio** — best-effort imports with offline fallbacks so CI works without heavy ML stacks.  
- **Temporal auto-setup** — fine for demos; production would use a dedicated Temporal cluster and separate task-queue workers.  
- **Generated code quality** — bounded by model + validators; judge thresholds are configurable.  
- **HITL timeout** — configurable per stage; expired HITL rejects the stage.
