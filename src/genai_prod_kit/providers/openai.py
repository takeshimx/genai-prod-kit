from openai import OpenAI
from ..gateway import LLMResult

class OpenAIProvider:
    def __init__(self, api_key: str):
        self.name = "openai"
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self._client = OpenAI(api_key=api_key)
    
    def generate(self, prompt: str, *, model: str) -> LLMResult:
        response = self._client.responses.create(
            model=model,
            input=prompt,
        )
        usage = response.usage
        return LLMResult(
            text=response.output_text or "",
            input_tokens=usage.input_tokens or 0,
            output_tokens=usage.output_tokens or 0,
        )