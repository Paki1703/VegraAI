# -*- coding: utf-8 -*-
"""
Точка входа: голосовой помощник VegraAI (в стиле Джарвиса).
Запуск: python main.py
"""

import sys
from pathlib import Path

# Чтобы работали импорты при запуске из любой папки
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice_input import listen_once
from voice_output import speak
from assistant import process
from neural.intents_model import IntentPredictor


def main():
    print("VegraAI (как Джарвис) запущен. Говори в микрофон. Для выхода скажи «Пока» или «Стоп».\n")
    speak("ВебграАй на связи. Слушаю тебя.", block=True)

    predictor = IntentPredictor()
    if not (ROOT / "data" / "intent_model.pt").exists():
        print("Сначала обучи нейросеть: python neural/train.py")
        return

    last_intent: str | None = None
    while True:
        print("Говори...")
        text = listen_once()
        if not text:
            print("(не расслышал)\n")
            continue
        print(f"Ты: {text}")

        response, should_exit, tag = process(text, predictor, last_intent)
        last_intent = tag
        print(f"VegraAI: {response}\n")
        speak(response, block=True)

        if should_exit:
            break

    print("До встречи.")


if __name__ == "__main__":
    main()
