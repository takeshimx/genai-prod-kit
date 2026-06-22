"""Drift statistics — PSI / KS / Chi-square, pure stdlib (no scipy)."""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Mapping

from .config import FeatureSpec


# ===== PSI =====
def _to_probabilities(counts: Mapping[str, int]) -> dict[str, float]:
    total = sum(counts.values())
    if total == 0:
        return {}
    return {k: v / total for k, v in counts.items()}


def compute_psi(
    reference_count: Mapping[str, int],
    detection_count: Mapping[str, int],
    epsilon: float = 1e-6,
) -> float:
    p_ref = _to_probabilities(reference_count)
    p_det = _to_probabilities(detection_count)
    if not p_ref or not p_det:
        return 0.0
    psi = 0.0
    for bin_key in set(p_ref) | set(p_det):
        pr = max(p_ref.get(bin_key, 0.0), epsilon)
        pd = max(p_det.get(bin_key, 0.0), epsilon)
        psi += (pd - pr) * math.log(pd / pr)
    return psi


def classify_psi_severity(psi: float, spec: FeatureSpec) -> str:
    if psi < spec.psi_warn_threshold:
        return "OK"
    if psi < spec.psi_alert_threshold:
        return "WARN"
    return "ALERT"


def compute_ks_statistic(
    reference_samples: Sequence[float],
    detection_samples: Sequence[float],
) -> float:
    if not reference_samples or not detection_samples:
        return 0.0
    ref = sorted(reference_samples)
    det = sorted(detection_samples)
    n_ref, n_det = len(ref), len(det)
    d = 0.0
    for v in sorted(set(ref) | set(det)):
        cdf_ref = _count_le(ref, v) / n_ref
        cdf_det = _count_le(det, v) / n_det
        d = max(d, abs(cdf_ref - cdf_det))
    return d


def _count_le(sorted_samples: list[float], value: float) -> int:
    lo, hi = 0, len(sorted_samples)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_samples[mid] <= value:
            lo = mid + 1
        else:
            hi = mid
    return lo


def classify_ks_severity(
    d_statistic: float, n_ref: int, n_det: int, spec: FeatureSpec
) -> str:
    if n_ref == 0 or n_det == 0:
        return "OK"
    factor = math.sqrt((n_ref + n_det) / (n_ref * n_det))
    crit_05 = 1.36 * factor   # alpha=0.05
    crit_01 = 1.63 * factor   # alpha=0.01
    if d_statistic <= crit_05:
        return "OK"
    if d_statistic <= crit_01:
        return "WARN"
    return "ALERT"


# ===== Chi-square (自前実装、scipy 不使用) =====
def compute_chi_square(
    reference_counts: Mapping[str, int],
    detection_counts: Mapping[str, int],
) -> float:
    """detection を観測、reference の割合を期待分布として chi-square 統計量を返す。"""
    ref_total = sum(reference_counts.values())
    det_total = sum(detection_counts.values())
    if ref_total == 0 or det_total == 0:
        return 0.0
    chi = 0.0
    for key in set(reference_counts) | set(detection_counts):
        observed = detection_counts.get(key, 0)
        expected = reference_counts.get(key, 0) / ref_total * det_total
        if expected > 0:
            chi += (observed - expected) ** 2 / expected
    return chi