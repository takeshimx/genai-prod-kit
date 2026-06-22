"""PII pipeline — orchestrates detect / redact / restore for the gateway.

呼出元は2関数だけ使う:
- run_pre_llm:  LLM 呼出前の検出 + 置換
- run_post_llm: LLM 応答後の復元 + leak 検出

モード:
- "off":     何もしない
- "shadow":  検出のみ。プロンプトは書き換えない (安全に観察)
- "enforce": 検出 + 書き換え + 復元 (本番防御)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .detector import RegexDetector
from .redactor import redact
from .restorer import detect_placeholder_leaks, restore
from .types import PIIMatch

Mode = Literal["off", "shadow", "enforce"]

_detector = RegexDetector()


@dataclass
class PIIPipelineResult:
    matches: list[PIIMatch] = field(default_factory=list)
    redaction_map: dict[str, str] = field(default_factory=dict)
    redacted_text: str = ""
    match_count: int = 0


def run_pre_llm(text: str, mode: Mode) -> PIIPipelineResult:
    """LLM 呼出前の検出 + 置換。例外は本流を止めないため吸収する。"""
    if mode == "off":
        return PIIPipelineResult(redacted_text=text)

    try:
        matches = _detector.detect(text)
        result = redact(text, matches)
        # shadow は元テキストを送る。enforce のみ書き換え後を送る
        out_text = result.redacted_text if mode == "enforce" else text
        return PIIPipelineResult(
            matches=matches,
            redaction_map=result.redaction_map,
            redacted_text=out_text,
            match_count=len(matches),
        )
    except Exception as e:
        print(f"[PII pre error] {e}")
        return PIIPipelineResult(redacted_text=text)


def run_post_llm(
    response_text: str,
    redaction_map: dict[str, str],
    mode: Mode,
) -> tuple[str, list[str]]:
    """LLM 応答の placeholder 復元 + leak 検出。Returns (text, leaks)。"""
    if mode == "off" or not redaction_map:
        return response_text, []

    try:
        leaks = detect_placeholder_leaks(response_text, redaction_map)
        if mode == "shadow":
            return response_text, leaks   # 復元しない
        return restore(response_text, redaction_map), leaks   # enforce
    except Exception as e:
        print(f"[PII post error] {e}")
        return response_text, []