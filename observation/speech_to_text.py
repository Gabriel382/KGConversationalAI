import whisper
import webrtcvad
import sounddevice as sd
import numpy as np
import collections
import queue
import time


model = whisper.load_model("small")  # Try "medium" or "large" for higher accuracy

def recognize_speech(duration=7):
    samplerate = 16000
    print("🧠 Listening... Please speak!")

    try:
        # Record from microphone
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        recording = np.squeeze(recording)
        recording = recording / np.max(np.abs(recording))  # Normalize

        # Run Whisper with translation
        result = model.transcribe(recording, fp16=False, task="translate")
        translated_text = result["text"].strip()
        detected_language = result.get("language", "unknown")

        print(f"🎤 Translated (to English): {translated_text}")
        print(f"🌍 Detected language: {detected_language}")

        return translated_text, detected_language

    except Exception as e:
        print(f"⚠️ Error during speech recognition: {e}")
        return "", "unknown"
    


def recognize_speech_vad(max_record_time=10, padding_duration_ms=300, aggressiveness=2, silence_padding=0.5):
    samplerate = 16000
    frame_duration_ms = 30  # ms
    frame_size = int(samplerate * frame_duration_ms / 1000)
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)

    vad = webrtcvad.Vad(aggressiveness)
    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time_info, status):
        audio_queue.put(bytes(indata))

    print("🧠 Listening for speech...")

    with sd.RawInputStream(samplerate=samplerate, blocksize=frame_size,
                           dtype='int16', channels=1, callback=audio_callback):
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False
        voiced_frames = []

        start_time = time.time()
        silence_start_time = None

        while True:
            if time.time() - start_time > max_record_time:
                print("⏱️ Max recording time reached.")
                break

            frame = audio_queue.get()
            is_speech = vad.is_speech(frame, samplerate)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > 0.9 * ring_buffer.maxlen:
                    triggered = True
                    voiced_frames.extend([f for f, _ in ring_buffer])
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame)
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])

                if num_unvoiced > 0.9 * ring_buffer.maxlen:
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    elif time.time() - silence_start_time > silence_padding:
                        print("🛑 Voice stopped after silence.")
                        break
                else:
                    silence_start_time = None

        audio_bytes = b''.join(voiced_frames)
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        if len(audio_np) == 0:
            print("⚠️ No speech detected.")
            return "", "unknown"

        result = model.transcribe(audio_np, fp16=False, task="translate")
        translated_text = result["text"].strip()
        language = result.get("language", "unknown")

        print(f"🎤 Translated: {translated_text}")
        print(f"🌍 Language: {language}")
        return translated_text, language
