from google import genai
from ..gateway import LLMResult



class GeminiProvider:
    def __init__(self, api_key: str):
        # 受け取った API キーで genai クライアントを作り、インスタンスに保存
        self.name = "gemini"
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        self._client = genai.Client(api_key=api_key)
        

    def generate(self, prompt: str, *, model:str) -> LLMResult:
        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
        )
        um = response.usage_metadata
        return LLMResult(
            text=response.text or "",
            input_tokens=um.prompt_token_count or 0,
            output_tokens=um.candidates_token_count or 0,
        )


