.PHONY: up down logs test seed demo-greenfield demo-brownfield demo-ambiguous install lint

COMPOSE = docker compose -f infra/docker-compose.yml --env-file .env

up:
	$(COMPOSE) up -d --build
	@echo "API:       http://localhost:8000"
	@echo "Frontend:  http://localhost:5173"
	@echo "Temporal:  http://localhost:8088"
	@echo "Grafana:   http://localhost:3001 (admin/admin)"
	@echo "LiteLLM:   http://localhost:4000"
	@echo "MinIO:     http://localhost:9001"

down:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f --tail=200

install:
	python -m pip install -e ".[dev]"
	cd frontend && npm install

test:
	pytest -q tests/unit tests/integration

lint:
	ruff check services tests
	cd frontend && npm run build --if-present

seed:
	bash scripts/seed.sh

demo-greenfield:
	python scripts/run_scenario.py --scenario greenfield --mode replay

demo-brownfield:
	python scripts/run_scenario.py --scenario brownfield --mode replay

demo-ambiguous:
	python scripts/run_scenario.py --scenario ambiguous --mode replay
