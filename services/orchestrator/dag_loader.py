"""Load and validate declarative SDLC DAG from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from services.common.config import get_settings


@dataclass
class StageDef:
    id: str
    agent: str | None = None
    activity: str | None = None
    entry_gates: list[str] = field(default_factory=list)
    exit_gates: list[str] = field(default_factory=list)
    on_result: dict[str, str] = field(default_factory=dict)
    next: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    parallel_after: list[str] = field(default_factory=list)
    requires_hitl: bool = False
    hitl_timeout_seconds: int = 3600
    replan_target: bool = False
    terminal: bool = False
    retry_max: int = 0
    retry_backoff: str = "exponential"
    compensation: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> StageDef:
        retry = raw.get("retry") or {}
        return cls(
            id=raw["id"],
            agent=raw.get("agent"),
            activity=raw.get("activity"),
            entry_gates=list(raw.get("entry_gates") or []),
            exit_gates=list(raw.get("exit_gates") or []),
            on_result=dict(raw.get("on_result") or {}),
            next=list(raw.get("next") or []),
            depends_on=list(raw.get("depends_on") or []),
            parallel_after=list(raw.get("parallel_after") or []),
            requires_hitl=bool(raw.get("requires_hitl", False)),
            hitl_timeout_seconds=int(raw.get("hitl_timeout_seconds") or 3600),
            replan_target=bool(raw.get("replan_target", False)),
            terminal=bool(raw.get("terminal", False)),
            retry_max=int(retry.get("max") or 0),
            retry_backoff=str(retry.get("backoff") or "exponential"),
            compensation=raw.get("compensation"),
        )


@dataclass
class DAG:
    version: str
    name: str
    stages: dict[str, StageDef]
    order: list[str]

    def get(self, stage_id: str) -> StageDef:
        if stage_id not in self.stages:
            raise KeyError(f"unknown stage: {stage_id}")
        return self.stages[stage_id]

    def entry_stage(self) -> StageDef:
        return self.stages[self.order[0]]

    def successors(self, stage_id: str, result_key: str | None = None) -> list[str]:
        stage = self.get(stage_id)
        if result_key and result_key in stage.on_result:
            return [stage.on_result[result_key]]
        if stage.parallel_after:
            return list(stage.parallel_after)
        return list(stage.next)

    def replan_targets(self) -> list[str]:
        return [s.id for s in self.stages.values() if s.replan_target]


def load_dag(path: Path | None = None, schema_path: Path | None = None) -> DAG:
    settings = get_settings()
    dag_path = path or settings.dag_path
    schema_file = schema_path or settings.dag_schema_path
    raw = yaml.safe_load(dag_path.read_text(encoding="utf-8"))
    if schema_file.exists():
        schema = __import__("json").loads(schema_file.read_text(encoding="utf-8"))
        jsonschema.validate(instance=raw, schema=schema)
    stages = [StageDef.from_dict(s) for s in raw["stages"]]
    by_id = {s.id: s for s in stages}
    # Synthetic plan stages referenced by parallel_after / depends_on
    for s in stages:
        for pid in s.parallel_after:
            if pid not in by_id:
                by_id[pid] = StageDef(id=pid, activity="noop_plan")
        for dep in s.depends_on:
            if dep not in by_id:
                by_id[dep] = StageDef(id=dep, activity="noop_plan")
    return DAG(
        version=str(raw["version"]),
        name=str(raw["name"]),
        stages=by_id,
        order=[s.id for s in stages],
    )
