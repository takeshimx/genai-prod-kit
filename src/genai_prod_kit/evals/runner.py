"""Eval runner — run a golden set through a predict_fn and score accuracy/latency."""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Callable


@dataclass
class EvalRun:
    ran_at: str
    feature: str
    git_sha: str
    golden_count: int
    accuracy: float
    latency_p50_ms: float
    note: str


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def load_golden(path: str | Path) -> list[dict]:
    p = Path(path)
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run_eval(
    golden: list[dict],
    predict_fn: Callable[[str], str],
    *,
    feature: str,
    note: str = "",
) -> EvalRun:
    correct = 0
    latencies: list[float] = []
    for row in golden:
        t0 = time.perf_counter()
        pred = predict_fn(row["text"])
        latencies.append((time.perf_counter() - t0) * 1000)
        if pred == row["expected"]:
            correct += 1
    
    total = len(golden)
    return EvalRun(
        ran_at=datetime.now(timezone.utc).isoformat(),
        feature=feature,
        git_sha=_git_sha(),
        golden_count=total,
        accuracy=correct / total if total else 0.0,
        latency_p50_ms=median(latencies) if latencies else 0.0,
        note=note,
    )

def append_run(record: EvalRun, path: str | Path) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")