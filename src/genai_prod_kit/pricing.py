# ==================================
# PRICING Map
# ==================================

PRICING: dict[str, dict[str, float]] = {
    # --- OpenAI (2026-06 時点・standard tier / short context) ---
    "gpt-5.5": {
        "input_per_1m_usd": 5.00,
        "output_per_1m_usd": 30.00,
    },
    "gpt-5.4": {
        "input_per_1m_usd": 2.50,
        "output_per_1m_usd": 15.00,
    },
    "gpt-5.4-mini": {
        "input_per_1m_usd": 0.75,
        "output_per_1m_usd": 4.50,
    },
    "gpt-5.4-nano": {
        "input_per_1m_usd": 0.20,
        "output_per_1m_usd": 1.25,
    },
    # gemini-2.5-flash — テキスト生成
    "gemini-2.5-flash": {
        "input_per_1m_usd": 0.30,
        "output_per_1m_usd": 2.50,
    },
    # gemini-2.5-pro — テキスト生成 (≤200k context tier)
    "gemini-2.5-pro": {
        "input_per_1m_usd": 1.25,
        "output_per_1m_usd": 10.00,
    },
    # gemini-embedding-001 — Embedding (入力のみ課金)
    "gemini-embedding-001": {
        "input_per_1m_usd": 0.15,
        "output_per_1m_usd": 0.0,
    },
}

def calc_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """input/output トークン数からモデル別 USD コストを算出。未登録モデルは 0。"""
    p = PRICING.get(model)
    if not p:
        return 0.0
    return (
        input_tokens * p["input_per_1m_usd"] / 1_000_000
        + output_tokens * p["output_per_1m_usd"] / 1_000_000
    )