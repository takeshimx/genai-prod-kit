"""PII redaction — shared types.

Detector / Redactor / Restorer / Pipeline が共通参照するデータ契約。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class PIIType(Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CARD = "CARD"
    # NER 拡張用（既定の regex detector では未使用）
    PERSON = "PERSON"
    ADDRESS = "ADDRESS"
    ORGANIZATION = "ORGANIZATION"


DetectionMethod = Literal["regex", "ner"]


@dataclass(frozen=True)
class PIIMatch:
    pii_type: PIIType
    start: int
    end: int
    original_value: str
    confidence: float
    detection_method: DetectionMethod


@dataclass
class RedactionResult:
    redacted_text: str
    redaction_map: dict[str, str] = field(default_factory=dict)
    matches: list[PIIMatch] = field(default_factory=list)