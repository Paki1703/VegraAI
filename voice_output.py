# -*- coding: utf-8 -*-
"""
Голосовой вывод: текст -> речь (Text-to-Speech)
"""

import pyttsx3

from config import VOICE_INDEX, SPEECH_RATE, VOLUME


def get_engine():
    """Создаёт и настраивает движок синтеза речи."""
    engine = pyttsx3.init()
    engine.setProperty("rate", SPEECH_RATE)
    engine.setProperty("volume", VOLUME)
    voices = engine.getProperty("voices")
    if 0 <= VOICE_INDEX < len(voices):
        engine.setProperty("voice", voices[VOICE_INDEX].id)
    return engine


def speak(text: str, block: bool = True) -> None:
    """
    Озвучивает текст.
    block: если True — ждёт окончания речи, иначе говорит в фоне.
    """
    if not text or not text.strip():
        return
    engine = get_engine()
    engine.say(text)
    if block:
        engine.runAndWait()
    else:
        engine.startLoop(False)
        engine.iterate()
        engine.endLoop()
