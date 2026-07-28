schwab-agentic-sdlc/
├── .cursor/
│   └── rules/
│       ├── 00-project-context.mdc      # always-applied
│       ├── 10-python-style.mdc         # *.py
│       ├── 11-temporal-patterns.mdc    # services/orchestrator/**
│       ├── 12-langgraph-patterns.mdc   # services/agents/**
│       ├── 13-fastapi-patterns.mdc     # services/api/**
│       ├── 14-react-patterns.mdc       # frontend/**
│       ├── 20-testing.mdc              # tests/**
│       ├── 30-security-policy.mdc      # policies/**, services/policy_engine/**
│       ├── 40-audit-observability.mdc  # services/audit/**
│       └── 90-agent-personas.mdc       # prompts/**, services/agents/**
├── .cursorignore
├── .cursorindexingignore
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ORCHESTRATION.md          # DAG spec, gates, replanning
│   ├── GOVERNANCE.md             # policies, guardrails, compliance mapping
│   ├── OBSERVABILITY.md          # metrics, traces, audit event schema
│   ├── TESTING.md
│   ├── SETUP.md
│   ├── SCENARIOS.md              # 3 walkthroughs
│   ├── LIMITATIONS.md            # trade-offs, what's out of scope
│   ├── FINAL_SUMMARY.md          # exec summary for reviewers
│   └── adr/                      # architecture decision records
│       ├── 0001-temporal-vs-airflow.md
│       ├── 0002-declarative-dag.md
│       ├── 0003-opa-for-policy.md
│       └── ...
├── dag/
│   ├── sdlc.yaml                 # THE declarative pipeline definition
│   └── schema.json               # JSON schema for DAG validation
├── policies/
│   ├── security.rego             # OPA policies
│   ├── change_control.rego
│   ├── code_standards.rego
│   ├── pii.rego
│   └── policy_document.md        # human-readable dummy policy doc (embedded in RAG)
├── prompts/                      # local fallback; LangSmith is canonical
│   ├── classifier.md
│   ├── requirement_analyst.md
│   ├── architect.md
│   ├── implementer.md
│   ├── tester.md
│   ├── documenter.md
│   ├── reviewer_judge.md
│   └── clarifier.md              # for ambiguous scenarios
├── services/
│   ├── api/                      # FastAPI
│   │   ├── main.py
│   │   ├── routers/{pipelines,signals,audit,metrics,health}.py
│   │   ├── schemas/
│   │   ├── sse.py                # live event stream
│   │   └── deps.py
│   ├── orchestrator/             # Temporal
│   │   ├── worker.py
│   │   ├── workflows/
│   │   │   ├── sdlc_master.py    # reads dag/sdlc.yaml, drives children
│   │   │   ├── stage_workflow.py # generic stage runner
│   │   │   └── compensation.py   # saga rollback
│   │   ├── activities/
│   │   │   ├── agent_activity.py
│   │   │   ├── policy_activity.py
│   │   │   ├── judge_activity.py
│   │   │   ├── audit_activity.py
│   │   │   └── retrieval_activity.py
│   │   ├── signals.py            # approve, reject, replan, safe_stop
│   │   └── dag_loader.py         # YAML → runtime DAG object
│   ├── agents/                   # LangGraph
│   │   ├── graphs/
│   │   │   ├── requirement_graph.py
│   │   │   ├── design_graph.py
│   │   │   ├── implementation_graph.py
│   │   │   ├── test_graph.py
│   │   │   ├── doc_graph.py
│   │   │   └── classifier_graph.py
│   │   ├── nodes/                # reusable nodes: retrieve, plan, code, review
│   │   ├── tools/                # code_writer, test_runner, file_reader, etc.
│   │   ├── state.py              # typed state schemas per graph
│   │   └── prompt_loader.py      # LangSmith + local fallback
│   ├── policy_engine/
│   │   ├── opa_client.py
│   │   ├── presidio_wrapper.py
│   │   ├── guardrails_wrapper.py
│   │   └── policy_gate.py        # unified entry/exit gate check
│   ├── knowledge/
│   │   ├── ingest.py             # codebase → chunks → embeddings
│   │   ├── retrieval.py
│   │   ├── embeddings.py
│   │   ├── models.py             # SQLAlchemy
│   │   └── migrations/           # Alembic
│   ├── judge/
│   │   ├── ragas_eval.py
│   │   ├── llm_judge.py
│   │   ├── deterministic.py      # ast parse, pytest run, bandit, ruff
│   │   └── scoring.py            # composite score → gate pass/fail
│   ├── audit/
│   │   ├── event_schema.py       # Pydantic models: canonical event
│   │   ├── writer.py             # S3 primary, local FS fallback
│   │   ├── circuit_breaker.py
│   │   └── replay.py             # rebuild pipeline history from audit
│   └── common/
│       ├── logging.py            # structured JSON logs
│       ├── metrics.py            # Prometheus counters/histograms
│       └── config.py             # pydantic-settings
├── frontend/
│   ├── src/
│   │   ├── components/{DagView,ApprovalCard,AuditTable,MetricTiles,EventStream}.tsx
│   │   ├── pages/{Home,Pipeline,Audit,Metrics,Scenarios}.tsx
│   │   ├── hooks/{useSSE,usePipeline,useApproval}.ts
│   │   ├── api/client.ts
│   │   └── lib/dagLayout.ts
│   ├── tailwind.config.ts
│   └── vite.config.ts
├── infra/
│   ├── docker-compose.yml         # postgres+pgvector, temporal, minio, grafana, prometheus, api, worker, frontend, opa
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   ├── Dockerfile.frontend
│   ├── prometheus.yml
│   ├── grafana/
│   │   └── dashboards/agentic-sdlc.json
│   └── init/
│       ├── postgres/init.sql
│       └── minio/create-bucket.sh
├── scenarios/
│   ├── greenfield/
│   │   ├── requirement.md         # "Build a URL shortener with..."
│   │   ├── expected_artifacts.md
│   │   └── replay.json            # pre-recorded audit trail for demo
│   ├── brownfield/
│   │   ├── seed_repo/             # existing URL shortener (planted)
│   │   ├── change_request.md      # "Add rate limiting + Redis cache"
│   │   └── expected_artifacts.md
│   └── ambiguous/
│       ├── requirement.md         # "Make the URL shortener enterprise-ready"
│       ├── expected_clarifications.md
│       └── expected_artifacts.md
├── tests/
│   ├── unit/
│   ├── integration/               # spins up Temporal test env
│   ├── e2e/                       # docker-compose based
│   └── evaluation/
│       ├── ragas_dataset.jsonl
│       └── judge_test_cases.py
├── scripts/
│   ├── seed.sh
│   ├── ingest_codebase.py
│   ├── run_scenario.py
│   └── demo.sh
├── .env.example
├── Makefile                       # make up, make down, make demo-greenfield, make test
├── pyproject.toml
├── README.md
└── EXECUTION_PLAN.md