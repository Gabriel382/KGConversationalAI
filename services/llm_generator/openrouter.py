import requests
from services.llm_generator.api_base import APILLMGenerator

class OpenRouterAPILLMGenerator(APILLMGenerator):
    def __init__(self, api_key: str, default_model="deepseek/deepseek-r1-zero:free"):
        super().__init__(
            api_key=api_key,
            api_url="https://openrouter.ai/api/v1/chat/completions",
            default_model=default_model
        )

    def generate(self, messages, model=None, max_tokens=200, temperature=0.71):
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(self.api_url, headers=self._build_headers(), json=payload)
            response.raise_for_status()
            data = response.json()

            #print("🧪 Full raw API response:", data)

            if "choices" not in data or not data["choices"]:
                raise ValueError("No 'choices' found in response.")

            return data["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"⚠️ OpenRouterAPILLMGenerator error: {e}")
            return "Sorry, I couldn't generate a response right now."
