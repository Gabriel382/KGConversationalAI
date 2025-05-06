import argparse
import json
from services.db_faq import DBFAQ
from services.llm_classifier import LLMClassifier
from services.llm_generator.openrouter import OpenRouterAPILLMGenerator
from services.llm_generator.ollama import OllamaLLMGenerator
from utils.graph_utils import load_candidate_labels_from_graph
from observation.speech_to_text import recognize_speech, recognize_speech_vad
from thought.intent_detector import detect_intent
from thought.dialogue_manager import next_action
from thought.faq_retriever import retrieve_answer
from thought.response_generator import generate_response
from action.text_to_speech import speak

# === Argument Parsing ===
parser = argparse.ArgumentParser(description="Run the TAO voice agent.")
parser.add_argument(
    "--mode", choices=["local", "api"], default="local",
    help="Choose which LLM backend to use: 'local' (Ollama) or 'api' (DeepSeek via OpenRouter)"
)
args = parser.parse_args()

# === LLM Generator Selection ===
if args.mode == "api":
    with open("secrets/apikey.json", "r") as f:
        api_key = json.load(f)["api_key"]
    llm_generator = OpenRouterAPILLMGenerator(api_key=api_key, default_model="deepseek/deepseek-r1-zero:free",
                                              model_name = "deepseek/deepseek-v3-base:free")
else:
    llm_generator = OllamaLLMGenerator(model_name = "llama3")

# === Shared Components ===
classifier = LLMClassifier()
faq_db = DBFAQ()
candidate_labels = load_candidate_labels_from_graph()
history = []

print(f"📋 Loaded candidate labels: {candidate_labels}")

def tao_cycle():
    global history

    # === OBSERVATION ===
    user_text, lang = recognize_speech_vad()
    print("Spoken language : "+lang)
    #user_text = "I want to book a meeting"

    # === THOUGHT ===
    intent = detect_intent(user_text, classifier, candidate_labels)
    print(f"🧠 Intent: {intent}")

    action_node = next_action(intent)
    print(f"➡️ Next state: {action_node.next_state}")

    knowledge = retrieve_answer(user_text, intent, faq_db, classifier)
    print(f"📚 Knowledge: {knowledge}")

    response_text = generate_response(
        history,
        intent,
        action_node,
        knowledge,
        llm_generator=llm_generator,
        model=model_name
    )

    history.append(("Agent", response_text))

    # === ACTION ===
    print(f"🗣️ Response: {response_text}")
    speak(response_text)

    return action_node.next_state  # <-- return new state

if __name__ == "__main__":
    current_state = "start"
    while current_state != "end":
        next_state = tao_cycle()
        if next_state == "end":
            print("👋 Ending the conversation. Goodbye!")
            break
        current_state = next_state

