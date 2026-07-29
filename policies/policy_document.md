# Human-readable policy document (embedded in RAG for agents)

## Agentic SDLC Policy Summary

1. **PII**: Never persist raw SSN, PAN, bank account, or routing numbers. Redact first.
2. **Security**: No `eval`, `pickle.loads`, hardcoded secrets, or unrestricted shell in generated code.
3. **Change control**: Implementation requires a design artifact. Release requires human approval.
4. **Code standards**: AST-valid Python, ruff-clean, bandit without high findings, pytest green with coverage floor.
5. **Autonomy**: Agents execute within DAG gates; humans own HITL checkpoints and final release.
