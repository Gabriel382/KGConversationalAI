from transformers import pipeline

class LLMClassifier:
    """
    A zero-shot classifier using Hugging Face Transformers.
    Useful for intent detection or FAQ matching with candidate labels.
    """

    def __init__(self, model_name="facebook/bart-large-mnli"):
        """
        Initializes the zero-shot classification pipeline.
        """
        self.pipeline = pipeline("zero-shot-classification", model=model_name)

    def classify(self, text, candidate_labels):
        """
        Classifies the input text against the given candidate labels.

        Args:
            text (str): The user message.
            candidate_labels (list of str): Possible labels to classify against.

        Returns:
            str: The most likely label.
        """
        try:
            result = self.pipeline(text, candidate_labels)
            return result["labels"][0]  # return top label
        except Exception as e:
            print(f"⚠️ LLMClassifier error: {e}")
            return None
