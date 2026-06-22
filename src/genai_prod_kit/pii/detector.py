"""Tier-1 PII detector — regex based, locale-neutral by default.

Detects high-confidence structured PII (email, credit card) without any
locale-specific or domain-specific rules. NER (Tier-2) is an optional add-on.
"""
from __future__ import annotations

import re

from .types import PIIMatch, PIIType


# 正規表現1本で完結する locale 中立カテゴリ
_PATTERNS: dict[PIIType, tuple[re.Pattern[str], float]] = {
    PIIType.EMAIL: (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        0.98,
    ),
}

# CARD: 形だけ正規表現で拾い、Luhn 検証を通ったものだけ採用する
_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")


class RegexDetector:
    """正規表現で locale 中立な PII を検出する。state-less。"""

    def detect(self, text: str) -> list[PIIMatch]:
        matches: list[PIIMatch] = []

        for pii_type, (pattern, confidence) in _PATTERNS.items():
            for m in pattern.finditer(text):
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    start=m.start(),
                    end=m.end(),
                    original_value=m.group(),
                    confidence=confidence,
                    detection_method="regex",
                ))
        
        matches.extend(self._detect_cards(text))
        return matches
    
    def _detect_cards(self, text: str) -> list[PIIMatch]:
        result: list[PIIMatch] = []
        for m in _CARD_PATTERN.finditer(text):
            digits = re.sub(r"[-\s]", "", m.group())
            if _luhn_check(digits):
                result.append(PIIMatch(
                    pii_type=PIIType.CARD,
                    start=m.start(),
                    end=m.end(),
                    original_value=m.group(),
                    confidence=1.0,
                    detection_method="regex",
                ))
        return result
    
def _luhn_check(digits: str) -> bool:
    """Luhn アルゴリズムでカード番号の checksum を検証する。"""
    if not digits.isdigit() or len(digits) < 13:
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

