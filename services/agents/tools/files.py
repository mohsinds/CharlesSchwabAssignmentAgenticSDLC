"""Agent tools — file IO gated by policy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.common.config import get_settings
from services.common.logging import get_logger

logger = get_logger(__name__)


def artifact_root(run_id: str) -> Path:
    root = Path(get_settings().artifacts_dir) / run_id
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_file(run_id: str, relative: str, content: str) -> str:
    path = artifact_root(run_id) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("tool_code_writer", run_id=run_id, path=str(path), bytes=len(content))
    return str(path)


def read_file(run_id: str, relative: str) -> str:
    path = artifact_root(run_id) / relative
    return path.read_text(encoding="utf-8")


def list_artifacts(run_id: str) -> list[str]:
    root = Path(get_settings().artifacts_dir) / run_id
    if not root.exists():
        return []
    return [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()]


async def policy_gated_write(run_id: str, relative: str, content: str) -> dict[str, Any]:
    from services.policy_engine.policy_gate import check

    decision = await check(
        "implementation",
        "exit",
        {"content": content, "stage_id": "implementation"},
        gate="policy_check",
    )
    if not decision.allowed:
        return {"ok": False, "violations": decision.violations}
    path = write_file(run_id, relative, content)
    return {"ok": True, "path": path}
