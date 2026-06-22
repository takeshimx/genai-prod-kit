"""LLM Gateway — single entry point for every LLM call.

Measures tokens / cost / latency for each call and writes one record to a sink.
Provider and sink are injected, so neither Gemini/OpenAI nor BigQuery/JSONL are
hard-wired here.

- fail-loud: provider errors are re-raised (callers' fallbacks stay in control).
- log-quietly: a sink write failure is swallowed (it must not break the call).
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Protocol

from .pricing import calc_cost_usd


@dataclass
class InvocationRecord:
    invocation_id: str      # 呼び出しごとの固有ID（UUID）
    created_at: datetime    # いつ呼んだか
    provider: str           # "gemini" か "openai" か
    model: str              # 使ったモデル名
    feature: str            # どの機能から呼ばれたか
    input_tokens: int       # 入力トークン数
    output_tokens: int      # 出力トークン数
    latency_ms: float       # 何ミリ秒かかったか
    estimated_cost_usd: float  # 推定コスト（pricing.py で計算）
    status: str             # "success" か "error"
    error_message: Optional[str] = None
    prompt_version: Optional[str] = None
    user_id: Optional[str] = None


# --- the two injected boundaries (implementations live in providers/ and sinks/) ---
@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int


class LLMProvider(Protocol):
    name: str
    def generate(self, prompt: str, *, model: str) -> LLMResult: ...


class InvocationSink(Protocol):
    def write(self, record: InvocationRecord) -> None: ...


def call_llm(
    prompt: str,
    *,
    provider: LLMProvider,
    sink: InvocationSink,
    feature: str,
    model: str,
    prompt_version: Optional[str] = None,
    user_id: Optional[str] = None,
) -> LLMResult:
    invocation_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    t0 = time.time()

    input_tokens = 0
    output_tokens = 0
    status = "success"
    error_message: Optional[str] = None
    result: Optional[LLMResult] = None

    try:
        result = provider.generate(prompt, model=model)
        input_tokens = result.input_tokens
        output_tokens = result.output_tokens
    except Exception as e:
        status = "error"
        error_message = str(e)[:1000]
        raise
    finally:
        latency_ms = (time.time() - t0) * 1000
        record = InvocationRecord(
            invocation_id=invocation_id,
            created_at=started_at,
            provider=provider.name,
            model=model,
            feature=feature,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            estimated_cost_usd=calc_cost_usd(model, input_tokens, output_tokens),
            status=status,
            error_message=error_message,
            prompt_version=prompt_version,
            user_id=user_id,
        )
        try:
            sink.write(record)
        except Exception as e:
            print(f"[Gateway sink error] {e}")
    
    return result