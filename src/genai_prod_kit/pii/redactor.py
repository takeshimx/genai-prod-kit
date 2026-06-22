"""PII Redactor — replace detected PII with placeholders and build a restore map.

Restorer と対をなすコンポーネント。
- 重なり合う match は信頼度の高い方を採用 (Detector 横断の重複解決もここで)
- 同じ PII カテゴリの 2 回目以降は連番 (<EMAIL_1>, <EMAIL_2>, ...)
- 同一値が複数箇所に出現した場合は同じ placeholder を使い回す (LLM の文脈一貫性のため)
"""
from __future__ import annotations

from .types import PIIMatch, PIIType, RedactionResult


def redact(text: str, matches: list[PIIMatch]) -> RedactionResult:
    """text 中の matches を placeholder に置換し RedactionResult を返す。

    Placeholder 形式: <{TYPE}_{COUNTER}>
    """
    if not matches:
        return RedactionResult(redacted_text=text, redaction_map={}, matches=[])

    # 1. 重なり合う match を解決
    deduped = _resolve_overlapping_matches(matches)

    # 2. 同一値には同じ placeholder を付ける (value -> placeholder)
    value_to_placeholder: dict[tuple[PIIType, str], str] = {}
    counter: dict[PIIType, int] = {}
    for match in sorted(deduped, key=lambda m: m.start):  # 出現順に番号付け
        key = (match.pii_type, match.original_value)
        if key not in value_to_placeholder:
            counter[match.pii_type] = counter.get(match.pii_type, 0) + 1
            value_to_placeholder[key] = (
                f"<{match.pii_type.value}_{counter[match.pii_type]}>"
            )

    # 3. 後ろから置換 (start 降順) して文字位置のズレを回避
    redacted = text
    for match in sorted(deduped, key=lambda m: m.start, reverse=True):
        placeholder = value_to_placeholder[(match.pii_type, match.original_value)]
        redacted = redacted[: match.start] + placeholder + redacted[match.end :]

    # 4. redaction_map は placeholder -> original の逆引き
    redaction_map = {
        placeholder: original_value
        for (_, original_value), placeholder in value_to_placeholder.items()
    }

    return RedactionResult(
        redacted_text=redacted,
        redaction_map=redaction_map,
        matches=deduped,
    )


def _resolve_overlapping_matches(matches: list[PIIMatch]) -> list[PIIMatch]:
    """範囲が重なる match のうち confidence が高い方を採用。

    複数の Detector (例: 既定の regex に加えて任意の NER) が同じ範囲を
    検出したとき、強い方だけを残す。
    同じ confidence なら 範囲が長い方 を採用 (より具体的な検出を優先)。
    """
    # 開始位置で昇順、同じなら範囲が長い順
    sorted_matches = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))

    result: list[PIIMatch] = []
    for current in sorted_matches:
        if not result:
            result.append(current)
            continue

        last = result[-1]
        # current が last と重なるか
        if current.start < last.end:
            # 重なる → どちらを残すか判定
            if _is_stronger(current, last):
                result[-1] = current
            # 弱い側は捨てる (何もしない)
        else:
            result.append(current)

    return result


def _is_stronger(a: PIIMatch, b: PIIMatch) -> bool:
    """a が b より「強い」(優先すべき) か判定。

    1. confidence が高い方が強い
    2. 同じなら範囲が長い方が強い (具体性優先)
    """
    if a.confidence != b.confidence:
        return a.confidence > b.confidence
    return (a.end - a.start) > (b.end - b.start)
