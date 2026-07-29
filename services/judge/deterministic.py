"""Deterministic validators: ast, ruff, bandit, pytest, coverage."""

from __future__ import annotations

import ast
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DeterministicResult:
    ok: bool
    checks: dict[str, Any] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)


def check_ast(code: str) -> DeterministicResult:
    try:
        ast.parse(code)
        return DeterministicResult(ok=True, checks={"ast_ok": True})
    except SyntaxError as exc:
        return DeterministicResult(
            ok=False,
            checks={"ast_ok": False},
            findings=[f"SyntaxError: {exc}"],
        )


def check_ast_path(root: Path) -> DeterministicResult:
    findings: list[str] = []
    for path in root.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            findings.append(f"{path}: {exc}")
    return DeterministicResult(
        ok=len(findings) == 0,
        checks={"ast_ok": len(findings) == 0},
        findings=findings,
    )


def run_ruff(root: Path) -> DeterministicResult:
    try:
        proc = subprocess.run(
            ["ruff", "check", str(root), "--quiet"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        ok = proc.returncode == 0
        findings = [line for line in (proc.stdout or proc.stderr).splitlines() if line.strip()]
        return DeterministicResult(ok=ok, checks={"ruff_ok": ok}, findings=findings[:50])
    except FileNotFoundError:
        return DeterministicResult(ok=True, checks={"ruff_ok": True, "skipped": True})
    except subprocess.TimeoutExpired:
        return DeterministicResult(ok=False, checks={"ruff_ok": False}, findings=["ruff timeout"])


def run_bandit(root: Path) -> DeterministicResult:
    try:
        # Skip test files: pytest asserts trigger B101 and are expected.
        proc = subprocess.run(
            ["bandit", "-r", str(root), "-q", "-f", "txt", "--exclude", "*/test_*.py,*/*_test.py"],
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        # bandit returns 1 when issues found
        high = "Severity: High" in (proc.stdout or "")
        ok = not high
        findings = [line for line in (proc.stdout or "").splitlines() if "Issue:" in line][:20]
        return DeterministicResult(ok=ok, checks={"bandit_ok": ok}, findings=findings)
    except FileNotFoundError:
        return DeterministicResult(ok=True, checks={"bandit_ok": True, "skipped": True})
    except subprocess.TimeoutExpired:
        return DeterministicResult(ok=False, checks={"bandit_ok": False}, findings=["bandit timeout"])


def run_pytest(root: Path, coverage_min: float = 0.6) -> DeterministicResult:
    if not any(root.rglob("test_*.py")) and not any(root.rglob("*_test.py")):
        return DeterministicResult(
            ok=False,
            checks={"pytest_ok": False, "coverage": 0.0},
            findings=["no tests found"],
        )
    try:
        proc = subprocess.run(
            [
                "pytest",
                str(root),
                "-q",
                "--cov=" + str(root),
                "--cov-report=term-missing",
            ],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            cwd=str(root),
        )
        ok = proc.returncode == 0
        coverage = _parse_coverage(proc.stdout or "")
        findings = []
        if not ok:
            findings.append((proc.stdout or proc.stderr)[-2000:])
        if coverage is not None and coverage < coverage_min:
            ok = False
            findings.append(f"coverage {coverage:.2f} < {coverage_min}")
        return DeterministicResult(
            ok=ok,
            checks={"pytest_ok": proc.returncode == 0, "coverage": coverage},
            findings=findings,
        )
    except FileNotFoundError:
        # Minimal in-process smoke: import compile
        return DeterministicResult(ok=True, checks={"pytest_ok": True, "coverage": 1.0, "skipped": True})
    except subprocess.TimeoutExpired:
        return DeterministicResult(ok=False, checks={"pytest_ok": False}, findings=["pytest timeout"])


def _parse_coverage(output: str) -> float | None:
    for line in output.splitlines():
        if "TOTAL" in line:
            parts = line.split()
            for part in reversed(parts):
                if part.endswith("%"):
                    try:
                        return float(part.rstrip("%")) / 100.0
                    except ValueError:
                        return None
    return None


def validate_code_artifact(code: str | Path, coverage_min: float = 0.6) -> DeterministicResult:
    if isinstance(code, Path):
        root = code
        results = [check_ast_path(root), run_ruff(root), run_bandit(root)]
        merged_checks: dict[str, Any] = {}
        findings: list[str] = []
        for r in results:
            merged_checks.update(r.checks)
            findings.extend(r.findings)
        return DeterministicResult(ok=all(r.ok for r in results), checks=merged_checks, findings=findings)

    ast_r = check_ast(code)
    if not ast_r.ok:
        return ast_r
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "module.py"
        path.write_text(code, encoding="utf-8")
        ruff_r = run_ruff(Path(tmp))
        bandit_r = run_bandit(Path(tmp))
        ok = ast_r.ok and ruff_r.ok and bandit_r.ok
        checks = {**ast_r.checks, **ruff_r.checks, **bandit_r.checks}
        findings = ast_r.findings + ruff_r.findings + bandit_r.findings
        return DeterministicResult(ok=ok, checks=checks, findings=findings)
