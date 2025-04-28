# thought/faq_retriever.py

import json

# Load FAQ database once
with open("dialogue_graph/faq.json", "r") as f:
    faq_db = json.load(f)

def retrieve_answer(user_text, user_intent, classifier):
    """
    Retrieve the best answer based on user_text and user_intent.

    Args:
        user_text (str): The original user utterance.
        user_intent (str): The intent detected earlier.
        classifier: A shared zero-shot-classification pipeline.

    Returns:
        str: Retrieved FAQ answer or default message.
    """
    if not user_text.strip():
        return "I'm sorry, I didn't catch that. Could you please repeat?"

    # Get FAQ candidates under the specific intent
    if user_intent not in faq_db:
        print(f"❓ No FAQ category found for intent '{user_intent}'.")
        return "I'm not sure about that topic."

    intent_faq = faq_db[user_intent]
    candidate_questions = list(intent_faq.keys())

    if not candidate_questions:
        return "I'm sorry, I don't have information on that topic."

    # Run classification
    result = classifier(user_text, candidate_labels=candidate_questions)
    best_match = result['labels'][0]
    confidence = result['scores'][0]

    print(f"🔍 FAQ Match inside '{user_intent}': {best_match} (confidence {confidence:.2f})")

    if confidence < 0.4:
        return "I'm not fully sure, but I will try to help."

    answer = intent_faq.get(best_match, "I'm sorry, I don't have information about that yet.")
    print(f"📚 Retrieved FAQ Answer: {answer}")

    return answer
