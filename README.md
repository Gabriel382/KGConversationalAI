# 🎤🧠🔊 Graph-Driven Voice Agent with TAO Cycle

_A modular, fully local conversational AI system following the Thought-Action-Observation cycle._

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-green)](https://ollama.com/)
[![Whisper](https://img.shields.io/badge/ASR-Whisper-lightgrey)](https://github.com/openai/whisper)
[![Transformers](https://img.shields.io/badge/NLU-Transformers-blue)](https://huggingface.co/)

---

**Graph-Driven Voice Agent** is a voice-controlled conversational agent that follows the **Thought-Action-Observation (TAO) Cycle**.  
It uses **local speech-to-text**, **intent detection**, **graph-based dialogue management**, **optional FAQ retrieval**, and **LLM-driven response generation** — all running **entirely offline**.

Designed to simulate realistic **phone call interactions** through **modular components**.

---

## 📂 Project Structure

```
graph_voice_agent/
├── main.py                  # Runs the full TAO cycle
├── observation/              # Captures and processes user speech
│   └── speech_to_text.py
├── thought/                  # Reasoning, planning, and decision-making
│   ├── intent_detector.py
│   ├── dialogue_manager.py
│   ├── faq_retriever.py
│   └── response_generator.py
├── action/                   # Acting back into the environment
│   └── text_to_speech.py
├── dialogue_graph/           # Dialogue and template definitions
│   ├── conversation_graph.json
│   ├── faq.json
│   └── templates.json
├── utils/
│   └── logger.py
├── imgs/                     # Project diagrams and images
│   └── uml.png
├── requirements.txt          # Project dependencies
├── LICENSE                   # Project license
└── README.md                 # Project documentation
```

---

## 🔥 Key Features

- **TAO Cycle**: Structured into Observation → Thought → Action phases.
- **Speech-to-Text**: Real-time voice transcription using OpenAI Whisper (locally).
- **Intent Detection**: Zero-shot classification with Hugging Face Transformers.
- **Graph-Based Dialogue Manager**: Control conversation flow via JSON graph.
- **FAQ Retrieval**: Optional, using zero-shot matching over a knowledge base.
- **Natural Language Generation**: Smart responses using Ollama and LLaMA 3 locally.
- **Text-to-Speech**: Voice output via pyttsx3 (offline).
- **Fully Offline Operation**: No paid APIs required.

---

## 🧩 Technologies Used

| Category | Technology |
|:---------|:------------|
| ASR (Speech Recognition) | [Whisper](https://github.com/openai/whisper) |
| NLU (Intent Detection) | [Transformers](https://huggingface.co/) |
| NLG (Response Generation) | [Ollama](https://ollama.com/) (LLaMA 3) |
| Graph Traversal | Custom JSON-based dialogue manager |
| TTS (Speech Output) | [pyttsx3](https://pyttsx3.readthedocs.io/en/latest/) |
| Programming Language | Python 3.10+ |

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Whisper

```bash
pip install openai-whisper
pip install sounddevice numpy scipy
```

### 3. Set up Transformers (Intent Detection)

```bash
pip install transformers
```

### 4. (Optional) Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

### 5. Set up Ollama (Local LLM Engine)

- Download and install Ollama from [official website](https://ollama.com/).
- Pull the LLaMA 3 model:
    ```bash
    ollama pull llama3
    ```
- Start the Ollama server:
    ```bash
    ollama serve
    ```

> Ollama API will run locally at `http://localhost:11434`. Keep it running during agent execution.

### 6. Run the Voice Agent

```bash
python main.py
```

✅ Speak when prompted, and the system will respond intelligently through speech.

---

## 🧠 TAO Cycle Architecture Diagram

```mermaid
flowchart TD
    A[Microphone Input] --> B[Observation Phase\nSpeech-to-Text (Whisper)]
    B --> C[Thought Phase\nIntent Detection (Zero-Shot)]
    C --> D[Dialogue Manager\nGraph Traversal]
    D --> E{Needs Knowledge?}
    E -- Yes --> F[FAQ Retriever\nText Matching]
    E -- No --> G
    F --> G[Response Generator\nTemplate + Ollama LLM + History]
    G --> H[Action Phase\nText-to-Speech (pyttsx3)]
    H --> I[Spoken Output]
```

## 🗂️ Full System UML Diagram

The following UML diagram shows the full architecture, including all modules and internal dependencies:

![UML Diagram](imgs/uml.png)

---

## 🌟 Future Improvements

- 🌐 Add a simple GUI (Streamlit / Gradio)
- 🧠 Dynamic dialogue graph updates
- 🗣️ Multi-language support (templates and FAQs)
- 🔍 Real-time external knowledge fetching
- 🧠 Fine-tuning lightweight local LLMs
- 💾 Session memory persistence

---

## 📚 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

Developed by **Gabriel Henrique Alencar Medeiros**.

---
