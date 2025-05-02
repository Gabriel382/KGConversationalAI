from services.llm_generator.base import LLMGenerator

class APILLMGenerator(LLMGenerator):
    def __init__(self, api_key, api_url="", default_model=""):
        """
        Base class for API-driven LLMs (e.g., OpenRouter, DeepSeek).

        Args:
            api_key (str): The API key for authentication.
            api_url (str): Endpoint to send requests to.
            default_model (str): Default model name to use.
        """
        super().__init__(chat_format=True)  # ✅ API-based generators expect chat-format messages

        self.api_key = api_key
        self.api_url = api_url
        self.default_model = default_model

    def _build_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
        }

    def generate(self, input_data, model=None, max_tokens=300, temperature=0.7):
        """
        This method should be implemented by subclasses (e.g., DeepSeek).

        Args:
            input_data: Usually a list of messages.
        """
        raise NotImplementedError("Use a concrete subclass like DeepSeekAPILLMGenerator.")
