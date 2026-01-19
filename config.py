# -*- coding: utf-8 -*-
"""
Конфигурация голосового помощника VegraAI (в стиле Джарвиса)
"""

# ============ Язык ============
LANGUAGE = "ru-RU"  # Русский для распознавания речи

# ============ Приложения для команды "Открыть X" ============
# Ключ — как пользователь может назвать приложение (в нижнем регистре)
# Значение — полный путь к .exe или имя программы в PATH
APPS = {
    "блокнот": "notepad",
    "notepad": "notepad",
    "калькулятор": "calc",
    "calc": "calc",
    "проводник": "explorer",
    "explorer": "explorer",
    "проводник файлов": "explorer",
    "браузер": "chrome",  # или "msedge", "firefox" — подставь свой
    "chrome": "chrome",
    "гугл хром": "chrome",
    "хром": "chrome",
    "edge": "msedge",
    "эдж": "msedge",
    "firefox": "firefox",
    "файрфокс": "firefox",
    "диспетчер задач": "taskmgr",
    "диспетчер": "taskmgr",
    "настройки": "ms-settings:",
    "параметры": "ms-settings:",
}

# Если Chrome/Edge установлены не по умолчанию — укажи полный путь, например:
# "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",

# ============ Поиск в интернете ============
# Какую поисковую систему использовать
SEARCH_URL = "https://www.google.com/search?q={query}"
# Альтернатива: "https://yandex.ru/search/?text={query}"

# ============ Нейросеть: путь к модели и данным ============
INTENTS_FILE = "data/intents.json"
MODEL_PATH = "data/intent_model.pt"
VOCAB_PATH = "data/vocab.json"

# ============ Голос (pyttsx3) ============
# Номер голоса: 0 — обычно мужской, 1 — женский (зависит от системы)
VOICE_INDEX = 0
SPEECH_RATE = 150   # Скорость речи (слов в минуту)
VOLUME = 1.0        # Громкость 0.0–1.0

# ============ LLM (Ollama) — ответы нейросетью, не шаблонами ============
# 1) Установи Ollama: https://ollama.com
# 2) Скачай модель (одну на выбор):
#       ollama pull qwen2.5:3b          — Qwen, лёгкая, хорошо по-русски
#       ollama pull qwen2.5:7b          — Qwen, мощнее
#       ollama pull deepseek-r1:7b-qwen-distill-q4_K_M   — DeepSeek R1 7B
#       ollama pull deepseek-r1:14b-qwen-distill-q4_K_M  — DeepSeek R1 14B (нужно больше RAM)
#       ollama pull llama3.2            — Llama
# 3) Укажи ниже то же имя, что после "ollama pull"
LLM_ENABLED = True
LLM_MODEL = "qwen2.5:3b"   # или: deepseek-r1:7b-qwen-distill-q4_K_M, deepseek-r1:14b-qwen-distill-q4_K_M, llama3.2
LLM_MAX_LENGTH = 600       # макс. длина ответа для озвучки
