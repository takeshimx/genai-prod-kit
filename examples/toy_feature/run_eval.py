import os

from genai_prod_kit.gateway import call_llm
from genai_prod_kit.providers.gemini import GeminiProvider
from genai_prod_kit.sinks.jsonl import JsonlSink
from genai_prod_kit.prompts.registry import get_prompt
from genai_prod_kit.evals.runner import load_golden, run_eval, append_run


def main() -> None:
    provider = GeminiProvider(os.environ["GEMINI_API_KEY"])
    sink = JsonlSink("invocations.jsonl")
    version, template = get_prompt("toy_sentiment")

    # 実 LLM で感情分類する predict_fn。runner に注入する。
    def classify(text: str) -> str:
        prompt = template.format(text=text)
        result = call_llm(
            prompt,
            provider=provider,
            sink=sink,
            feature="toy_sentiment",
            model="gemini-2.5-flash",
            prompt_version=version,
        )
        return result.text.strip().lower()
    
    golden = load_golden("src/genai_prod_kit/evals/golden/toy_sentiment.jsonl")
    run = run_eval(golden, classify, feature="toy_sentiment", note="real_gemini")

    print(f"accuracy = {run.accuracy:.1%}  ({run.golden_count} items)")
    append_run(run, "eval_runs.jsonl")
    print("eval_runs.jsonl に保存しました")


if __name__ == "__main__":
    main()