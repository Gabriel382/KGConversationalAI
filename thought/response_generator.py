# thought/response_generator.py

import requests
import json

# Load templates once
with open("dialogue_graph/templates.json", "r", encoding="utf-8") as f:
    templates = json.load(f)


def call_ollama(prompt, model="llama3", max_tokens=200, temperature=0.3):
    """
    Sends a prompt to the local Ollama server and returns the generated text.

    Args:
        prompt (str): Prompt to send.
        model (str): Model name in Ollama (e.g., 'llama3', 'mistral', etc.)
        max_tokens (int): Max number of tokens to generate.
        temperature (float): Sampling temperature.

    Returns:
        str: Generated text from the model.
    """
    try:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        return data.get('response', "").strip()

    except Exception as e:
        print(f"⚠️ Ollama API error: {e}")
        return "I'm sorry, I'm having trouble generating a response right now."


def generate_response(history, intent, action_node, knowledge, model=None):
    """
    Generate a response using Ollama if model is specified, else fallback to simple templates.

    Args:
        history (list): Conversation history.
        intent (str): Detected intent.
        action_node (ActionNode): Result of dialogue manager.
        knowledge (str, optional): Retrieved FAQ answer.
        model (str, optional): Model name for Ollama (e.g., 'llama3'). If None, use simple generation.

    Returns:
        str: Final response.
    """

    # If no model is provided, use fallback simple responses
    if model is None:
        if knowledge:
            return knowledge
        return templates.get(intent, "I'm here to assist you!")

    # Otherwise, use Ollama to generate a smarter response
    # Build history text
    history_text = ""
    for speaker, text in history[-6:]:  # Limit history to last 6 exchanges
        history_text += f"{speaker}: {text}\n"

    instruction = templates.get(intent, "Assist the user politely.")

    knowledge_text = f"Use this information if needed: {knowledge}\n" if knowledge else ""

    # Compose the prompt
    prompt = (
        f"You are a helpful voice assistant.\n"
        f"Instruction: {instruction}\n"
        f"{knowledge_text}\n"
        f"Conversation so far:\n"
        f"{history_text}"
        f"Now continue as the Agent:"
    )
    
    return call_ollama(prompt, model=model)