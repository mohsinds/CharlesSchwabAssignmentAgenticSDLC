# Testing

## Unit

- DAG loader + schema validation  
- Audit event keys + circuit breaker  
- Policy gate (PII / security)  
- Deterministic judge + composite scoring (no LLM override)  
- Classifier heuristics  

## Integration

- FastAPI `/health` and DAG meta  
- In-process **replay** pipeline end-to-end  

## Policy

`opa test policies/` (with OPA CLI) using `*_test.rego`.

## How to run

```bash
pip install -e ".[dev]"
pytest -q tests/unit tests/integration
```

Live LLM e2e is optional and requires LiteLLM + upstream keys.
