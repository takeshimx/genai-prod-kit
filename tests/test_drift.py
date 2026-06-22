"""H5 drift — monitor の単体テスト（LLM 不要・課金ゼロ）。

H5 手動検証（KS / PSI・Chi-square / サンプル不足スキップ）を pytest 化したもの。
"""
from genai_prod_kit.drift.config import FeatureSpec, FeatureType, TestType
from genai_prod_kit.drift.monitor import monitor_numeric, monitor_categorical


NUMERIC_SPEC = FeatureSpec(
    feature="toy", feature_field="len",
    feature_type=FeatureType.NUMERIC, tests=(TestType.KS,),
)
CATEGORICAL_SPEC = FeatureSpec(
    feature="toy", feature_field="dist",
    feature_type=FeatureType.CATEGORICAL,
    tests=(TestType.PSI, TestType.CHI_SQUARE),
)


# ===== monitor_numeric (KS) =====
def test_numeric_same_distribution_is_ok():
    res = monitor_numeric(NUMERIC_SPEC, list(range(50)), list(range(50)))
    assert len(res) == 1
    assert res[0].statistic == 0.0
    assert res[0].severity == "OK"


def test_numeric_full_separation_is_alert():
    res = monitor_numeric(NUMERIC_SPEC, list(range(50)), list(range(1000, 1050)))
    assert len(res) == 1
    assert res[0].statistic == 1.0
    assert res[0].severity == "ALERT"


# ===== monitor_categorical (PSI / Chi-square) =====
def test_categorical_same_distribution_is_ok():
    ref = {"pos": 60, "neu": 30, "neg": 10}
    res = monitor_categorical(CATEGORICAL_SPEC, ref, dict(ref))
    psi = next(r for r in res if r.test == "psi")
    assert psi.statistic == 0.0
    assert psi.severity == "OK"


def test_categorical_shift_raises_psi_severity():
    ref = {"pos": 60, "neu": 30, "neg": 10}
    det = {"pos": 10, "neu": 20, "neg": 70}
    res = monitor_categorical(CATEGORICAL_SPEC, ref, det)
    psi = next(r for r in res if r.test == "psi")
    chi = next(r for r in res if r.test == "chi_square")
    assert psi.severity in ("WARN", "ALERT")
    assert chi.statistic > 0


# ===== min_sample_size スキップ =====
def test_below_min_sample_size_skips():
    # 29 < 30 → 空リスト
    res = monitor_numeric(NUMERIC_SPEC, list(range(29)), list(range(29)))
    assert res == []


def test_exactly_min_sample_size_runs():
    # ちょうど 30 → 判定される
    res = monitor_numeric(NUMERIC_SPEC, list(range(30)), list(range(30)))
    assert len(res) == 1


def test_one_side_below_min_skips():
    # min(50, 10) = 10 < 30 → 空リスト
    res = monitor_numeric(NUMERIC_SPEC, list(range(50)), list(range(10)))
    assert res == []
