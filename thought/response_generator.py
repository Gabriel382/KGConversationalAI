import json

# Load templates once at the top
with open("dialogue_graph/templates.json", "r", encoding="utf-8") as f:
    templates = json.load(f)

def generate_response(history, intent, action_node, knowledge, llm_generator=None, model=None):
    """
    Generate a response using an LLMGenerator, or fallback to templates.

    Args:
        history (list): Conversation history [(speaker, text), ...].
        intent (str): User's detected intent.
        action_node (ActionNode): Dialogue manager result (with next_state).
        knowledge (str, optional): FAQ result or external info.
        llm_generator (LLMGenerator, optional): Generator instance.
        model (str, optional): Model name (e.g. 'llama3', 'deepseek/...').

    Returns:
        str: Generated response or fallback answer.
    """
    if llm_generator is None:
        if knowledge:
            return knowledge
        return templates.get(intent, "I'm here to assist you!")

    # Template instruction
    instruction = templates.get(intent, "Assist the user politely.")
    next_state_note = f"You are now moving to the dialogue state: '{action_node.next_state}'."
    knowledge_text = f"Use this information if needed: {knowledge}" if knowledge else ""
    
    # Chat-format model: use role-based message list
    if llm_generator.chat_format:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful and concise English-speaking voice assistant. "
                    "Always respond briefly and naturally in English. "
                    "Do not use code formatting, document outlines, or markdown."
                )
            }
        ]

        # Include conversation history (optional, last 6 exchanges)
        for speaker, text in history[-6:]:
            role = "user" if speaker.lower() == "user" else "assistant"
            messages.append({"role": role, "content": text})

        # Build a natural prompt for the LLM
        instruction = templates.get(intent, "Assist the user politely.")
        knowledge_text = f"Here's some useful example: {knowledge}" if knowledge else ""

        user_prompt = (
            f"The user would like to {intent.replace('_', ' ')}.\n"
            f"{instruction}\n"
            f"{knowledge_text}\n"
            f"Now, give me as output what would be a good assistant reply."
        ).strip()

        messages.append({"role": "user", "content": user_prompt})

        #print("📥 Prompt to LLM (chat format):", messages)

        # Generate and return response
        response = llm_generator.generate(messages, model=model)

        if not response.strip():
            print("⚠️ Empty LLM response, using fallback template.")
            return knowledge or templates.get(intent, "I'm here to assist you!")

        return response



    # Prompt-based model: use full instruction string
    else:
        history_text = "\n".join(f"{speaker}: {text}" for speaker, text in history[-6:])
        prompt = (
            f"You are a helpful voice assistant.\n"
            f"Always reply in short, natural English sentences.\n"
            f"Intent detected: {intent}\n"
            f"{next_state_note}\n"
            f"{knowledge_text}\n"
            f"Conversation history:\n{history_text}\n"
            f"Now continue as the Agent."
        )
        return llm_generator.generate(prompt, model=model)
