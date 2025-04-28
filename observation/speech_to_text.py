# observation/speech_to_text.py

import whisper
import sounddevice as sd
import numpy as np

# Load Whisper model
model = whisper.load_model("base")

def recognize_speech(duration=5):
    """
    Record and transcribe speech using Whisper directly from NumPy array.
    """
    samplerate = 16000  # Whisper expects 16kHz
    print("🧠 Listening... Please speak!")

    try:
        # Record audio
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()

        # Whisper expects float32 audio in [-1, 1] and 16kHz
        recording = np.squeeze(recording)  # Remove extra dimension if needed

        # Transcribe directly from memory
        result = model.transcribe(recording, fp16=False)  # Force fp32
        text = result["text"].strip()

        print(f"🎤 You said: {text}")
        return text

    except Exception as e:
        print(f"⚠️ Error during speech recognition: {e}")
        return ""
