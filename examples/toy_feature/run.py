import os

from genai_prod_kit.gateway import call_llm
from genai_prod_kit.providers.gemini import GeminiProvider
from genai_prod_kit.sinks.jsonl import JsonlSink
from genai_prod_kit.prompts.registry import get_prompt


def main() -> None:
    api_key = os.environ["GEMINI_API_KEY"]

    provider = GeminiProvider(api_key)
    sink = JsonlSink("invocations.jsonl")
    version, template = get_prompt("toy_summary")
    prompt = template.format(text="2026年サッカーワールドカップは、48か国が出場します。")

    result = call_llm(
        prompt,
        provider=provider,
        sink=sink,
        feature="toy_summary",
        model="gemini-2.5-flash",
        prompt_version=version,
    )

    print("--- 生成結果 ---")
    print(result.text)
    print("--- 記録は invocations.jsonl に書き込まれました ---")

if __name__ == "__main__":
    main()