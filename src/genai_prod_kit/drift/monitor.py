"""Drift monitor — run the configured tests for a feature and report severity."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Mapping

from .config import FeatureSpec, TestType
from .statistics import (
    compute_psi, classify_psi_severity,
    compute_ks_statistic, classify_ks_severity,
    compute_chi_square,
)


@dataclass
class DriftResult:
    feature: str
    feature_field: str
    test: str
    statistic: float
    severity: str


def monitor_numeric(
    spec: FeatureSpec,
    reference_samples: Sequence[float],
    detection_samples: Sequence[float],
) -> list[DriftResult]:
    """数値 feature を KS で監視する。"""
    results: list[DriftResult] = []
    n_ref, n_det = len(reference_samples), len(detection_samples)

    # サンプル下限未満は判定しない（OK 扱い）
    if min(n_ref, n_det) < spec.min_sample_size:
        return results
    
    if TestType.KS in spec.tests:
        d = compute_ks_statistic(reference_samples, detection_samples)
        sev = classify_ks_severity(d, n_ref, n_det, spec)
        results.append(DriftResult(
            spec.feature, spec.feature_field, "ks_test", d, sev
        ))
    return results


def monitor_categorical(
    spec: FeatureSpec,
    reference_counts: Mapping[str, int],
    detection_counts: Mapping[str, int],
) -> list[DriftResult]:
    """カテゴリ feature を PSI / Chi-square で監視する。"""
    results: list[DriftResult] = []

    if TestType.PSI in spec.tests:
        psi = compute_psi(reference_counts, detection_counts)
        sev = classify_psi_severity(psi, spec)
        results.append(DriftResult(spec.feature, spec.feature_field, "psi", psi, sev))

    if TestType.CHI_SQUARE in spec.tests:
        chi = compute_chi_square(reference_counts, detection_counts)
        # chi は閾値を別途要するが、トイでは統計量のみ記録（severity は PSI に委ねる設計も可）
        results.append(DriftResult(spec.feature, spec.feature_field, "chi_square", chi, "OK"))

    return results