# thought/dialogue_manager.py

import json

# Load the conversation graph once
with open("dialogue_graph/conversation_graph.json", "r") as f:
    conversation_graph = json.load(f)

# Global current state (simple approach for now)
current_state = "start"

class ActionNode:
    """
    A class representing the result of the dialogue decision.
    """
    def __init__(self, next_state, requires_kb=False):
        self.next_state = next_state
        self.requires_kb = requires_kb

def next_action(intent):
    """
    Given the detected intent, determines the next dialogue state.

    Args:
        intent (str): The detected intent.

    Returns:
        ActionNode: Contains next_state and whether it requires knowledge base access.
    """
    global current_state

    if current_state not in conversation_graph:
        print(f"⚠️ Current state '{current_state}' not in graph. Resetting to start.")
        current_state = "start"

    possible_transitions = conversation_graph[current_state]

    # Default fallback: stay in same state if no matching intent
    if intent in possible_transitions:
        next_state = possible_transitions[intent]
        print(f"🔀 Transition: {current_state} + [{intent}] ➔ {next_state}")
        current_state = next_state
    else:
        print(f"❓ No transition found for intent '{intent}' in state '{current_state}'. Staying.")
        next_state = current_state

    # Decide if next_state requires KB access (custom rule here)
    requires_kb = next_state in ["provide_information"]

    return ActionNode(next_state, requires_kb)
