"""Whisper-based ASR with optional VAD-driven recording.

The heavy dependencies (``whisper``, ``sounddevice``, ``numpy``,
``webrtcvad``) are imported lazily so that ``import kgconvai`` works in
environments without audio hardware or the ``[voice]`` extras installed.
"""

from __future__ import annotations

import collections
import queue
import time
from typing import TYPE_CHECKING

from kgconvai.asr.base import ASR, SpeechResult
from kgconvai.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover
    pass

log = get_logger(__name__)


class WhisperASR(ASR):
    """Records audio (optionally with WebRTC VAD) and transcribes via Whisper."""

    def __init__(
        self,
        model_name: str = "base",
        *,
        use_vad: bool = True,
        max_record_seconds: float = 10.0,
        silence_padding_seconds: float = 0.5,
        vad_aggressiveness: int = 2,
        sample_rate: int = 16000,
        translate: bool = True,
    ) -> None:
        self.model_name = model_name
        self.use_vad = use_vad
        self.max_record_seconds = max_record_seconds
        self.silence_padding_seconds = silence_padding_seconds
        self.vad_aggressiveness = vad_aggressiveness
        self.sample_rate = sample_rate
        self.task = "translate" if translate else "transcribe"
        self._model = None  # lazy

    def _load_model(self):  # pragma: no cover - requires whisper
        if self._model is None:
            import whisper

            log.info("whisper.loading_model", model=self.model_name)
            self._model = whisper.load_model(self.model_name)
        return self._model

    def listen(self) -> SpeechResult:
        if self.use_vad:
            return self._listen_vad()
        return self._listen_fixed_window(duration=7.0)

    def _listen_fixed_window(self, duration: float) -> SpeechResult:  # pragma: no cover
        import numpy as np
        import sounddevice as sd

        model = self._load_model()
        log.info("asr.listening", mode="fixed", duration=duration)
        try:
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
            )
            sd.wait()
            recording = np.squeeze(recording)
            peak = float(np.max(np.abs(recording))) or 1.0
            recording = recording / peak
            result = model.transcribe(recording, fp16=False, task=self.task)
            return SpeechResult(
                text=str(result.get("text", "")).strip(),
                language=str(result.get("language", "unknown")),
            )
        except Exception as exc:
            log.warning("asr.error", err=str(exc))
            return SpeechResult("", "unknown")

    def _listen_vad(self) -> SpeechResult:  # pragma: no cover
        import numpy as np
        import sounddevice as sd
        import webrtcvad

        model = self._load_model()
        frame_ms = 30
        frame_size = int(self.sample_rate * frame_ms / 1000)
        padding_frames = int(300 / frame_ms)

        vad = webrtcvad.Vad(self.vad_aggressiveness)
        audio_queue: queue.Queue[bytes] = queue.Queue()

        def _cb(indata, frames, time_info, status):
            audio_queue.put(bytes(indata))

        log.info("asr.listening", mode="vad")
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=frame_size,
                dtype="int16",
                channels=1,
                callback=_cb,
            ):
                ring: collections.deque = collections.deque(maxlen=padding_frames)
                ring_capacity = padding_frames  # mypy-friendly alias for ring.maxlen
                triggered = False
                voiced: list[bytes] = []
                start = time.time()
                silence_start: float | None = None

                while True:
                    if time.time() - start > self.max_record_seconds:
                        break
                    frame = audio_queue.get()
                    is_speech = vad.is_speech(frame, self.sample_rate)
                    if not triggered:
                        ring.append((frame, is_speech))
                        if sum(1 for _, s in ring if s) > 0.9 * ring_capacity:
                            triggered = True
                            voiced.extend(f for f, _ in ring)
                            ring.clear()
                    else:
                        voiced.append(frame)
                        ring.append((frame, is_speech))
                        unvoiced = sum(1 for _, s in ring if not s)
                        if unvoiced > 0.9 * ring_capacity:
                            if silence_start is None:
                                silence_start = time.time()
                            elif time.time() - silence_start > self.silence_padding_seconds:
                                break
                        else:
                            silence_start = None

            if not voiced:
                return SpeechResult("", "unknown")

            audio_np = np.frombuffer(b"".join(voiced), dtype=np.int16).astype(np.float32) / 32768.0
            result = model.transcribe(audio_np, fp16=False, task=self.task)
            return SpeechResult(
                text=str(result.get("text", "")).strip(),
                language=str(result.get("language", "unknown")),
            )
        except Exception as exc:
            log.warning("asr.error", err=str(exc))
            return SpeechResult("", "unknown")
