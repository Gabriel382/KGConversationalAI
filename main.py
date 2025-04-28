from transformers import pipeline
from utils.graph_utils import load_candidate_labels_from_graph
from observation.speech_to_text import recognize_speech
from thought.intent_detector import detect_intent
from thought.dialogue_manager import next_action
from thought.faq_retriever import retrieve_answer
from thought.response_generator import generate_response
from action.text_to_speech import speak

# Load shared classifier once
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Load candidate labels dynamically from the graph
candidate_labels = load_candidate_labels_from_graph()

print(f"📋 Loaded candidate labels: {candidate_labels}")

# History of conversation
history = []

def tao_cycle():
    global history
    # OBSERVATION
    user_text = recognize_speech()

    # THOUGHT
    intent = detect_intent(user_text, classifier, candidate_labels)
    print(intent)
    action_node = next_action(intent)
    print(action_node.next_state)
    knowledge = retrieve_answer(user_text, intent, classifier)
    print(knowledge)
    response_text = generate_response(history, intent, action_node, knowledge, model="llama3")
    history += [response_text]
    
    history.append(("Agent", response_text))

    # ACTION
    speak(response_text)

if __name__ == "__main__":
    while True:
        tao_cycle()
