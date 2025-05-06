from abc import ABC, abstractmethod

class LLMGenerator(ABC):
    """
    Abstract base class for all LLM text generators.
    """
    def __init__(self, chat_format: bool = False, model_name = ""):
        self.chat_format = chat_format
        self.model_name = model_name

    @abstractmethod
    def generate(self, prompt, model=None, max_tokens=200, temperature=0.7) -> str:
        pass
