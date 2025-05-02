def retrieve_answer(user_text, user_intent, faq_db, classifier, confidence_threshold=0.4):
    """
    Retrieve the best answer from the FAQ based on user input and intent.

    Args:
        user_text (str): The user's original utterance.
        user_intent (str): Detected intent category for the question.
        faq_db (DBFAQ): Instance of the DBFAQ class.
        classifier (LLMClassifier): Instance of the LLMClassifier.
        confidence_threshold (float): Minimum score to accept the result.

    Returns:
        str: Retrieved answer string or fallback message.
    """
    if not user_text.strip():
        return "I'm sorry, I didn't catch that. Could you please repeat?"

    # Step 1: Get candidate questions for this intent
    candidate_questions = faq_db.get_questions_by_intent(user_intent)
    if not candidate_questions:
        print(f"❓ No FAQ entries found for intent '{user_intent}'.")
        return "I'm not sure about that topic."

    # Step 2: Run zero-shot classification
    try:
        result = classifier.pipeline(user_text, candidate_questions)
        best_match = result["labels"][0]
        confidence = result["scores"][0]
    except Exception as e:
        print(f"⚠️ FAQ classification error: {e}")
        return "I'm having trouble understanding your question right now."

    print(f"🔍 FAQ Match inside '{user_intent}': {best_match} (confidence {confidence:.2f})")

    # Step 3: Fallback if confidence is too low
    if confidence < confidence_threshold:
        return "I'm not fully sure, but I will try to help."

    # Step 4: Retrieve answer
    answer = faq_db.get_answer(user_intent, best_match)
    if not answer:
        return "I'm sorry, I don't have information about that yet."

    print(f"📚 Retrieved FAQ Answer: {answer}")
    return answer
