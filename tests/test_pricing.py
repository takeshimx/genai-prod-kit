"""H1 pricing — calc_cost_usd の単体テスト（LLM 不要・課金ゼロ）。"""
from genai_prod_kit.pricing import calc_cost_usd


def test_flash_cost():
    # 1M input + 1M output → input 0.30 + output 2.50 = 2.80 USD
    cost = calc_cost_usd("gemini-2.5-flash", 1_000_000, 1_000_000)
    assert cost == 0.30 + 2.50


def test_pro_cost():
    cost = calc_cost_usd("gemini-2.5-pro", 1_000_000, 1_000_000)
    assert cost == 1.25 + 10.00


def test_embedding_output_is_free():
    # embedding は入力のみ課金、output 単価 0
    cost = calc_cost_usd("gemini-embedding-001", 1_000_000, 999)
    assert cost == 0.15


def test_zero_tokens():
    assert calc_cost_usd("gemini-2.5-flash", 0, 0) == 0.0


def test_unknown_model_is_zero():
    # 未登録モデルは黙って 0（fail-loud しない設計）
    assert calc_cost_usd("nonexistent-model", 1_000_000, 1_000_000) == 0.0


def test_partial_tokens_scale_linearly():
    # 500k input のみ → 0.30 * 0.5 = 0.15
    cost = calc_cost_usd("gemini-2.5-flash", 500_000, 0)
    assert cost == 0.15
