"""Prompt registry — version-pinned prompt loader.

各 feature の現役プロンプト版を ACTIVE_VERSIONS で集中管理する。
プロンプト本文は同フォルダ配下の {feature}/{version}.txt に置く。

運用ルール:
  - プロンプトを変えたいときは v2.txt を新設 → ACTIVE_VERSIONS を書き換え → commit
  - 旧版 (v1.txt) は履歴目的で消さず残す
  - get_prompt() が返す version を gateway の prompt_version に渡せば記録に乗る
"""
from pathlib import Path

# 各 feature の現役プロンプト版。差し替え時はここを更新する。
ACTIVE_VERSIONS: dict[str, str] = {
    "toy_summary": "v1",
    "toy_sentiment": "v1",
}

_BASE = Path(__file__).parent


def get_prompt(feature: str) -> tuple[str, str]:
    """指定 feature の (version, template_text) を返す。
    """
    if feature not in ACTIVE_VERSIONS:
        raise KeyError(f"No prompt registered for feature: {feature}")
    version = ACTIVE_VERSIONS[feature]
    path = _BASE / feature / f"{version}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file missing: {path}")
    return version, path.read_text(encoding="utf-8")