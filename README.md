# 🎤🧠🔊 Graph-Driven Voice Agent with TAO Cycle

*A modular, fully local conversational AI system following the Thought-Action-Observation cycle.*

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-green)](https://ollama.com/)
[![Whisper](https://img.shields.io/badge/ASR-Whisper-lightgrey)](https://github.com/openai/whisper)
[![Transformers](https://img.shields.io/badge/NLU-Transformers-blue)](https://huggingface.co/)

---

**Graph-Driven Voice Agent** is a voice-controlled conversational agent that follows the **Thought-Action-Observation (TAO) Cycle**.
It uses **real-time voice detection (VAD)**, **speech-to-text via Whisper**, **zero-shot intent classification**, **graph-based dialogue**, **optional knowledge retrieval**, and **LLM-driven generation** — all offline or via local models.

---

## 📂 Project Structure

```
graph_voice_agent/
├── main.py                     # Run the TAO loop
├── observation/                # Speech input (with VAD support)
│   └── speech_to_text.py
├── thought/                    # Reasoning and planning
│   ├── intent_detector.py
│   ├── dialogue_manager.py
│   ├── faq_retriever.py
│   └── response_generator.py
├── action/                     # Speaking responses
│   └── text_to_speech.py
├── dialogue_graph/             # Dialogue logic and templates
│   ├── conversation_graph.json
│   ├── faq.json
│   └── templates.json
├── services/                   # Encapsulated logic for LLM and DB
│   ├── db_faq.py
│   ├── llm_classifier.py
│   └── llm_generator/
│       ├── base.py
│       ├── api_base.py
│       ├── openrouter.py
│       └── ollama.py
├── utils/
│   ├── graph_utils.py
│   └── logger.py
├── imgs/                       # Architecture diagrams
│   └── uml.png
├── secrets/                    # API key (excluded from Git)
│   └── apikey.json
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔥 Key Features

* ✅ **Real-Time VAD (Voice Activity Detection)** using `webrtcvad`
* 🗣️ **Multilingual ASR + English translation** via Whisper
* 🧠 **Intent Detection** via Hugging Face zero-shot models
* 🔀 **Graph-Based Dialogue** with modular transitions
* 📚 **FAQ Answering** per dialogue state
* 🧾 **Template + LLM Response Generation**
* 🔊 **Offline Text-to-Speech (pyttsx3)**
* 🔌 **Fully offline or API-based setups**

---

## 🧩 Technologies Used

| Category         | Technology                                                          |
| ---------------- | ------------------------------------------------------------------- |
| ASR (Speech)     | [Whisper](https://github.com/openai/whisper)                        |
| VAD              | [webrtcvad](https://github.com/wiseman/py-webrtcvad)                |
| Intent Detection | [Transformers](https://huggingface.co/)                             |
| Dialogue Manager | JSON-based state graphs                                             |
| LLM Generator    | [Ollama](https://ollama.com/), [OpenRouter](https://openrouter.ai/) |
| TTS              | [pyttsx3](https://pyttsx3.readthedocs.io/)                          |
| Language         | Python 3.10+                                                        |

---

## 🚀 Getting Started

### 1. Install Python packages

```bash
pip install -r requirements.txt
```

If `webrtcvad` fails to install on Windows, install Visual Studio Build Tools:
👉 [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### 2. Install Whisper + Audio dependencies

```bash
pip install openai-whisper sounddevice numpy scipy
```

### 3. (Optional) Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
```

### 4. Ollama Setup (Local LLMs)

* Install Ollama: [https://ollama.com/](https://ollama.com/)
* Pull a model:

  ```bash
  ollama pull llama3
  ```
* Start the server:

  ```bash
  ollama serve
  ```

### 5. (Optional) Use OpenRouter API

* Create a file at `secrets/apikey.json`:

```json
{
  "api_key": "your-openrouter-key"
}
```

* Run with:

```bash
python main.py --mode api
```

### 6. Run the Voice Agent

```bash
python main.py
```

Speak clearly when prompted. The system will listen, classify your intent, retrieve knowledge, and respond.

---

## 🧠 TAO Cycle Architecture

![TAO Architecture](imgs/uml.png)

---

## ✅ Example Intents & States

* `greet → ask_information`
* `book_meeting → confirm_booking → end`
* `cancel → end`
* `ask_information → provide_information`

---

## 🌟 Coming Soon


* 📡 Knowledge-based (Ontology + KG) integration
* 🧠 Fine-tuned local intent models
* 💬 Session memory and logging
* 🌍 Full multilingual response support
* 🎛️ GUI (Streamlit or Gradio) ?

---

## 📚 License

MIT License — see [LICENSE](LICENSE)

Developed by **Gabriel Henrique Alencar Medeiros**
