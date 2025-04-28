# thought/intent_detector.py
def detect_intent(user_text, classifier, candidate_labels):
    """
    Detects the user's intent using a shared classifier.

    Args:
        user_text (str): User input.
        classifier: Shared pipeline.
        candidate_labels (List[str]): List of intents.

    Returns:
        str: The best matching intent label.
    """
    if not user_text.strip():
        return "unknown"

    result = classifier(user_text, candidate_labels=candidate_labels)
    intent = result['labels'][0]

    print(f"🔍 Detected intent: {intent}")
    return intent
