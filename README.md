# 🎤🧠🔊 Graph-Driven Voice Agent with TAO Cycle

This project implements a **voice-controlled conversational agent** based on the **Thought-Action-Observation (TAO) Cycle**.  
It follows a modular architecture where **speech input** is converted to **text**, analyzed through a **graph-controlled dialogue manager**, and replied through **speech synthesis**.

The agent is designed to simulate realistic **phone call interactions** using **controlled dialogue flows**, **intent detection**, and optional **knowledge retrieval**.

---

## 🛠️ Project Structure

```
graph_voice_agent/
├── main.py                  # Runs the full TAO cycle
├── observation/             # Modules for capturing user input
│   └── speech_to_text.py
├── thought/                 # Modules for reasoning and planning
│   ├── intent_detector.py
│   ├── dialogue_manager.py
│   ├── faq_retriever.py
│   └── response_generator.py
├── action/                  # Modules for acting in the environment
│   └── text_to_speech.py
├── dialogue_graph/          # Conversation flow definition
│   └── conversation_graph.json
├── utils/
│   └── logger.py
├── requirements.txt         # Project dependencies
├── LICENSE         # Project license
└── README.md
```

---

## 🔥 Key Features

- **TAO Architecture**: Thought-Action-Observation cycle design for intelligent agent behavior.
- **Automatic Speech Recognition (ASR)**: Convert user speech to text (Observation).
- **Natural Language Understanding (NLU)**: Detect intents from user utterances (Thought).
- **Graph-Based Dialogue Manager**: Control dialogue flow with minimal hallucination (Thought).
- **Knowledge Retrieval (Optional)**: Query simple knowledge bases during conversation (Thought).
- **Natural Language Generation (NLG)**: Create text responses from structured intents (Thought).
- **Text-to-Speech (TTS)**: Generate and play spoken responses (Action).

---

## 🧩 Technologies Used

- **ASR**: Whisper (small model) / AssemblyAI / SpeechRecognition
- **NLU**: Hugging Face zero-shot pipeline (`distilbert-base-uncased`)
- **Graph Control**: NetworkX (or custom lightweight graph engine)
- **NLG**: Template-based or lightweight GPT generation
- **TTS**: pyttsx3 / CoquiTTS / Google Text-to-Speech
- **Python 3.10+**

---

## 🚀 How to Run

1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2. Run the main agent:
    ```bash
    python main.py
    ```

3. Speak when prompted, and listen to the intelligent reply!

---

## 🧠 Thought-Action-Observation Cycle

| Phase         | Description |
|---------------|-------------|
| **Observation** | Capture user speech and recognize text |
| **Thought** | Analyze text, detect intent, plan next move using graph |
| **Action** | Generate spoken response |

---

## 🌟 Future Improvements

- GUI Interface (Streamlit, Flask, or Gradio)
- More complex dynamic conversation graphs
- Real-time Knowledge Retrieval using APIs
- Fine-tuned LLMs for more natural NLG

---

## 📚 Credits & License

Inspired by the architecture of **real-world dialogue agents**. **MIT License**.

Developed by: Gabriel Henrique Alencar Medeiros



---
