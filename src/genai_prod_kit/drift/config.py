"""Drift monitoring — feature spec registry.

監視対象 feature の定義・統計閾値・サンプル下限を集中管理する。
ユーザーは自分の監視対象を MONITORED_FEATURES に定義する（家計簿固有値は持たない）。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os


class TestType(str, Enum):
    PSI = "psi"
    KS = "ks_test"
    CHI_SQUARE = "chi_square"


class FeatureType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"


@dataclass(frozen=True)
class FeatureSpec:
    feature: str                      # 監視対象の名前
    feature_field: str                # 監視する値の名前
    feature_type: FeatureType
    tests: tuple[TestType, ...]

    # 閾値（feature 個別に override 可）
    psi_warn_threshold: float = 0.10
    psi_alert_threshold: float = 0.25
    ks_p_threshold: float = 0.01
    chi_square_p_threshold: float = 0.01

    # サンプル数下限（これ未満は severity=OK 扱い）
    min_sample_size: int = 30


# トイ例の監視対象（ユーザーは自分の feature に差し替える）
MONITORED_FEATURES: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        feature="toy_summary",
        feature_field="input_length",
        feature_type=FeatureType.NUMERIC,
        tests=(TestType.KS, TestType.PSI),
    ),
    FeatureSpec(
        feature="toy_sentiment",
        feature_field="label_distribution",
        feature_type=FeatureType.CATEGORICAL,
        tests=(TestType.CHI_SQUARE,),
    ),
)


# shadow mode: true の間は記録のみで通知しない（既定 true = 安全に観察）
SHADOW_MODE: bool = os.getenv("DRIFT_SHADOW_MODE", "true").lower() == "true"