# utils/graph_utils.py

import json

def load_candidate_labels_from_graph(graph_path="dialogue_graph/conversation_graph.json"):
    """
    Loads candidate intent labels from the conversation graph.

    Args:
        graph_path (str): Path to the conversation graph JSON file.

    Returns:
        List[str]: A list of unique candidate labels (intents).
    """
    with open(graph_path, "r") as f:
        conversation_graph = json.load(f)

    candidate_labels = set()

    for state_transitions in conversation_graph.values():
        for intent in state_transitions.keys():
            candidate_labels.add(intent)

    return list(candidate_labels)
