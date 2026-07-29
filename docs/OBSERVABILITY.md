# Observability

## Audit events

Canonical schema: `services/audit/event_schema.py`.

Writer: MinIO primary, `./data/audit` FS fallback via circuit breaker. Replay: `services/audit/replay.py`.

## Metrics

Prometheus counters/histograms in `services/common/metrics.py`:

- pipeline started/completed  
- stage duration  
- retries / rollbacks  
- gate results  
- e2e latency  

Scrape: `GET /metrics/prometheus`. Grafana dashboard: `infra/grafana/dashboards/agentic-sdlc.json`.

## Tracing

Optional LangSmith via `LANGSMITH_*` env. Agent prompts load from Hub with local `/prompts` fallback.
