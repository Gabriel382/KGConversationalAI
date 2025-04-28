# action/text_to_speech.py

import pyttsx3

# Initialize the TTS engine once
tts_engine = pyttsx3.init()

# Optionally configure voice properties
tts_engine.setProperty('rate', 175)     # Speed (default ~200 wpm)
tts_engine.setProperty('volume', 1.0)    # Volume (max = 1.0)

def speak(text):
    """
    Convert text to speech and play it through the speakers.

    Args:
        text (str): The text to speak.
    """
    if not text.strip():
        print("⚠️ Empty text, nothing to speak.")
        return

    print(f"🗣️ Speaking: {text}")
    tts_engine.say(text)
    tts_engine.runAndWait()
