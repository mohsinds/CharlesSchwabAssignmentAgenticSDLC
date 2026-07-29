"""Presidio PII detection with graceful fallback."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from services.common.logging import get_logger

logger = get_logger(__name__)

# Financial-services oriented entities when Presidio is available
ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "US_SSN",
    "US_BANK_NUMBER",
    "IBAN_CODE",
    "US_ITIN",
]

_FALLBACK_PATTERNS = [
    ("US_SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]*?){13,19}\b")),
    ("EMAIL_ADDRESS", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
]


@dataclass
class PIIResult:
    findings: list[dict[str, Any]] = field(default_factory=list)
    redacted_text: str = ""
    redacted: bool = False


class PresidioWrapper:
    def __init__(self) -> None:
        self._analyzer = None
        self._anonymizer = None
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine

            self._analyzer = AnalyzerEngine()
            self._anonymizer = AnonymizerEngine()
        except Exception as exc:  # noqa: BLE001
            logger.warning("presidio_unavailable", error=str(exc))

    def analyze(self, text: str) -> PIIResult:
        if not text:
            return PIIResult(redacted_text=text)
        if self._analyzer and self._anonymizer:
            try:
                results = self._analyzer.analyze(text=text, language="en", entities=ENTITIES)
                findings = [
                    {
                        "entity_type": r.entity_type,
                        "start": r.start,
                        "end": r.end,
                        "score": r.score,
                    }
                    for r in results
                ]
                if findings:
                    anonymized = self._anonymizer.anonymize(text=text, analyzer_results=results)
                    return PIIResult(
                        findings=findings,
                        redacted_text=anonymized.text,
                        redacted=True,
                    )
                return PIIResult(redacted_text=text)
            except Exception as exc:  # noqa: BLE001
                logger.warning("presidio_analyze_failed", error=str(exc))

        # Regex fallback
        findings = []
        redacted = text
        for entity, pattern in _FALLBACK_PATTERNS:
            for m in pattern.finditer(text):
                findings.append(
                    {"entity_type": entity, "start": m.start(), "end": m.end(), "score": 0.8}
                )
                redacted = redacted.replace(m.group(0), f"<{entity}>")
        return PIIResult(
            findings=findings,
            redacted_text=redacted,
            redacted=bool(findings),
        )
