import requests
from services.llm_generator.base import LLMGenerator

class OllamaLLMGenerator(LLMGenerator):
    def __init__(self, url="http://localhost:11434/api/generate"):
        super().__init__(chat_format=False)
        self.url = url

    def generate(self, input_data, model="llama3", max_tokens=200, temperature=0.15):
        """
        Generate a reply using a locally running Ollama instance.

        Args:
            input_data (str): A prompt string (not a list of messages).
            model (str): Name of the local Ollama model (e.g., 'llama3').
        """
        try:
            payload = {
                "model": model,
                "prompt": input_data,  # Use string prompt
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"⚠️ OllamaLLMGenerator error: {e}")
            return "I'm sorry, I couldn't generate a response right now."
