# -*- coding: utf-8 -*-
"""
Голосовой ввод: микрофон -> текст (Speech-to-Text).
Используется sounddevice (вместо PyAudio) — проще ставить на Windows.
"""

import speech_recognition as sr
import sounddevice as sd

from config import LANGUAGE

SAMPLE_RATE = 16000


def listen(timeout: int = 5, phrase_time_limit: int = 10) -> str | None:
    """
    Слушает микрофон и возвращает распознанный текст.
    Записывает до phrase_time_limit секунд (3–15), затем отправляет в Google.
    Возвращает None, если не удалось распознать или ошибка.
    """
    duration = max(3, min(phrase_time_limit, 15))
    try:
        recording = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        sd.wait()
    except Exception:
        return None

    raw = recording.flatten().tobytes()
    audio = sr.AudioData(raw, SAMPLE_RATE, 2)

    r = sr.Recognizer()
    try:
        text = r.recognize_google(audio, language=LANGUAGE)
        return text.strip()
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None


def listen_once(phrase_time_limit: int = 8) -> str | None:
    """Удобная обёртка: записать фразу (по умолчанию 8 секунд) и распознать."""
    return listen(timeout=5, phrase_time_limit=phrase_time_limit)
