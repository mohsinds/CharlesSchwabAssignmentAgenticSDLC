"""SSE helpers for live audit streams."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from services.audit.writer import get_audit_writer


async def event_generator(run_id: str, poll_seconds: float = 1.0) -> AsyncIterator[str]:
    seen: set[str] = set()
    writer = get_audit_writer()
    idle_rounds = 0
    while idle_rounds < 600:
        events = writer.list_run(run_id)
        new = False
        for e in events:
            if e.event_id in seen:
                continue
            seen.add(e.event_id)
            new = True
            payload = e.model_dump(mode="json")
            yield f"data: {json.dumps(payload, default=str)}\n\n"
        if not new:
            idle_rounds += 1
        else:
            idle_rounds = 0
        # Stop if pipeline completed
        if any(e.event_type.value == "PipelineCompleted" for e in events):
            yield f"data: {json.dumps({'event_type': 'stream_end', 'run_id': run_id})}\n\n"
            break
        await asyncio.sleep(poll_seconds)
