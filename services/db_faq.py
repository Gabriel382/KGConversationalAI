import json

class DBFAQ:
    """
    Handles loading and querying the FAQ knowledge base.
    """

    def __init__(self, path="dialogue_graph/faq.json"):
        with open(path, "r") as f:
            self.data = json.load(f)

    def get_questions_by_intent(self, intent):
        return list(self.data.get(intent, {}).keys())

    def get_answer(self, intent, question):
        return self.data.get(intent, {}).get(question, None)
