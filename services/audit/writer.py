"""Audit writer: MinIO primary, local FS fallback via circuit breaker."""

from __future__ import annotations

import json
from pathlib import Path

from services.audit.circuit_breaker import CircuitBreaker
from services.audit.event_schema import AuditEvent
from services.common.config import get_settings
from services.common.logging import get_logger

logger = get_logger(__name__)


class AuditWriter:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.breaker = CircuitBreaker()
        self._s3 = None
        self.fs_root = Path(self.settings.audit_fs_fallback_dir)
        self.fs_root.mkdir(parents=True, exist_ok=True)

    def _client(self):
        if self._s3 is None:
            import boto3
            from botocore.client import Config

            self._s3 = boto3.client(
                "s3",
                endpoint_url=(
                    f"{'https' if self.settings.minio_secure else 'http'}://"
                    f"{self.settings.minio_endpoint}"
                ),
                aws_access_key_id=self.settings.minio_access_key,
                aws_secret_access_key=self.settings.minio_secret_key,
                config=Config(signature_version="s3v4"),
                region_name="us-east-1",
            )
        return self._s3

    def _write_fs(self, event: AuditEvent) -> str:
        path = self.fs_root / event.object_key()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(event.model_dump_json(indent=2), encoding="utf-8")
        return str(path)

    def write(self, event: AuditEvent) -> dict:
        body = event.model_dump_json().encode("utf-8")
        key = event.object_key()
        used_fallback = False
        location = key

        if self.breaker.allow():
            try:
                self._client().put_object(
                    Bucket=self.settings.minio_bucket,
                    Key=key,
                    Body=body,
                    ContentType="application/json",
                )
                self.breaker.record_success()
                location = f"s3://{self.settings.minio_bucket}/{key}"
            except Exception as exc:  # noqa: BLE001 — fall back deliberately
                self.breaker.record_failure()
                logger.warning("minio_write_failed", error=str(exc), key=key)
                location = self._write_fs(event)
                used_fallback = True
        else:
            location = self._write_fs(event)
            used_fallback = True

        return {"location": location, "fallback": used_fallback, "event_id": event.event_id}

    def list_run(self, run_id: str) -> list[AuditEvent]:
        events: list[AuditEvent] = []
        # Prefer FS (always available); merge MinIO if healthy
        run_dir = self.fs_root / run_id
        if run_dir.exists():
            for path in sorted(run_dir.rglob("*.json")):
                try:
                    events.append(AuditEvent.model_validate_json(path.read_text(encoding="utf-8")))
                except Exception:  # noqa: BLE001
                    continue
        if self.breaker.allow():
            try:
                resp = self._client().list_objects_v2(
                    Bucket=self.settings.minio_bucket, Prefix=f"{run_id}/"
                )
                for obj in resp.get("Contents") or []:
                    raw = self._client().get_object(
                        Bucket=self.settings.minio_bucket, Key=obj["Key"]
                    )["Body"].read()
                    events.append(AuditEvent.model_validate_json(raw))
                self.breaker.record_success()
            except Exception as exc:  # noqa: BLE001
                self.breaker.record_failure()
                logger.warning("minio_list_failed", error=str(exc))

        # Dedup by event_id
        by_id = {e.event_id: e for e in events}
        return sorted(by_id.values(), key=lambda e: e.timestamp)


_writer: AuditWriter | None = None


def get_audit_writer() -> AuditWriter:
    global _writer
    if _writer is None:
        _writer = AuditWriter()
    return _writer
