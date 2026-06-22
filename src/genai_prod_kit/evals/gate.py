"""Regression gate — fail (exit 1) if the latest eval accuracy dropped vs the previous run.

Reads eval_runs.jsonl, compares the last two runs, and exits non-zero when
accuracy regressed by more than THRESHOLD. Wired into CI to block merges.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 許容する accuracy 低下幅（既定 0.02 = 2 ポイント）。env で上書き可。
THRESHOLD = float(os.getenv("REGRESSION_THRESHOLD", "0.02"))


def load_runs(path: str | Path) -> list[dict]:
    p = Path(path)
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(path:str = "eval_runs.jsonl") -> int:
    runs = load_runs(path)
    if len(runs) < 2:
        print("WARN: 比較対象が2件未満のためゲートをスキップします")
        return 0
    
    baseline = runs[-2]
    current = runs[-1]
    delta = current["accuracy"] - baseline["accuracy"]

    print(f"baseline : {baseline['accuracy']:.1%}  (sha={baseline['git_sha'][:8]})")
    print(f"current  : {current['accuracy']:.1%}  (sha={current['git_sha'][:8]})")
    print(f"delta    : {delta:+.2%}  (threshold={THRESHOLD:.0%})")

    if delta < -THRESHOLD:
        print(f"❌ FAIL: accuracy が {THRESHOLD:.0%} 以上低下しました")
        return 1
    print("✅ PASS")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "eval_runs.jsonl"
    sys.exit(main(path))