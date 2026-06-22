"""PII Restorer — restore placeholders in an LLM response back to original values.

Redactor と対をなす。redaction_map (placeholder -> original) を使い、
LLM 応答内の placeholder を全て元値に書き戻す。
LLM が想定外の placeholder を生成していないか (leak) も検出する。
"""
from __future__ import annotations

import re

# placeholder 形式: <TYPE_数字>  例: <EMAIL_1>, <CARD_3>
# Redactor が生成する形式と必ず一致させること
_PLACEHOLDER_PATTERN = re.compile(r"<[A-Z_]+_\d+>")


def restore(response_text: str, redaction_map: dict[str, str]) -> str:
    """LLM 応答に含まれる placeholder を元の値に置換する。

    - redaction_map が空なら text をそのまま返す (no-op)
    - map に存在しない placeholder は触らない (leak 検出で別途扱う)
    """
    if not redaction_map:
        return response_text
    
    restored = response_text
    # 長い placeholder から処理して部分一致による誤置換を回避
    for placeholder in sorted(redaction_map.keys(), key=len, reverse=True):
        original = redaction_map[placeholder]
        restored = restored.replace(placeholder, original)
    
    return restored


def detect_placeholder_leaks(
    response_text: str,
    redaction_map: dict[str, str],
) -> list[str]:
    """LLM が想定外の placeholder を生成していないか検出する。

    - 入力には <EMAIL_1> しか無かったのに、応答に <EMAIL_2> や
      <CARD_1> が出てきた場合、それを「leak」として返す
    - 戻り値が空 list なら正常
    - 重複は排除して unique な leak 一覧を返す
    """
    placeholder_in_response = set(_PLACEHOLDER_PATTERN.findall(response_text))
    expected = set(redaction_map.keys())
    unexpected = placeholder_in_response - expected
    return sorted(unexpected)