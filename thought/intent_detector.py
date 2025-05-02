def detect_intent(user_text, classifier, candidate_labels):
    """
    Detects the user's intent using a shared LLMClassifier instance.

    Args:
        user_text (str): User input.
        classifier (LLMClassifier): Instance of LLMClassifier.
        candidate_labels (List[str]): List of possible intent labels.

    Returns:
        str: The best matching intent label.
    """
    if not user_text.strip():
        return "unknown"

    intent = classifier.classify(user_text, candidate_labels)

    if intent:
        print(f"🔍 Detected intent: {intent}")
        return intent
    else:
        return "unknown"
