# -*- coding: utf-8 -*-
"""
Главный модуль ассистента: связывает голос, нейросеть и управление ПК.
"""

import json
import random
from datetime import datetime
from pathlib import Path

from neural.intents_model import IntentPredictor
from pc_controller import open_app, search_in_browser
from config import INTENTS_FILE, APPS


# Триггеры для поиска — убираем их из начала фразы, остаток = поисковый запрос
SEARCH_TRIGGERS = [
    "найди в интернете",
    "поищи в интернете",
    "найди в гугл",
    "поищи в гугле",
    "найди в браузере",
    "открой в браузере",
    "поиск в интернете",
    "найди в яндексе",
    "найди",
    "поищи",
    "загугли",
]


def _load_intents() -> dict:
    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_app_name(text: str) -> str | None:
    """Определяет, какое приложение из config.APPS имелось в виду."""
    t = text.lower().strip()
    # Выбираем самое длинное совпадение (чтобы "гугл хром" имел приоритет над "хром")
    found = [k for k in APPS if k in t]
    return max(found, key=len) if found else None


def _extract_search_query(text: str) -> str:
    """Убирает триггеры поиска и возвращает запрос."""
    t = text.strip()
    for tr in sorted(SEARCH_TRIGGERS, key=len, reverse=True):
        if t.lower().startswith(tr):
            return t[len(tr) :].strip()
    return t


def process(text: str, predictor: IntentPredictor | None = None) -> tuple[str, bool]:
    """
    Обрабатывает фразу пользователя через нейросеть и выполняет действие.
    Возвращает (ответ_ассистента, нужно_ли_выйти).
    """
    if predictor is None:
        predictor = IntentPredictor()
    intents_data = _load_intents()
    tag = predictor.predict(text)

    # Находим данные по тегу
    intent = next((i for i in intents_data["intents"] if i["tag"] == tag), None)
    if not intent:
        return "Не удалось определить намерение.", False

    responses = intent.get("responses", ["Понял."])
    should_exit = tag == "прощание"

    # --- Действия и подстановки в ответ ---

    if tag == "открыть_приложение":
        app_key = _extract_app_name(text)
        if not app_key:
            return "Не понял, какое приложение открыть. Назови, например: блокнот, калькулятор, браузер.", False
        ok = open_app(app_key)
        rep = random.choice(responses).replace("%app%", app_key)
        return rep if ok else f"Не получилось открыть {app_key}. Проверь название в config.APPS.", False

    if tag == "поиск_в_интернете":
        query = _extract_search_query(text)
        if not query:
            return "Уточни, что искать в интернете.", False
        ok = search_in_browser(query)
        rep = random.choice(responses).replace("%query%", query)
        return rep if ok else "Не удалось открыть браузер.", False

    if tag == "текущее_время":
        time_str = datetime.now().strftime("%H:%M")
        return random.choice(responses).replace("%time%", time_str), False

    if tag == "текущая_дата":
        # "понедельник, 15 января 2024"
        months = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()
        d = datetime.now()
        weekday = ["понедельник","вторник","среда","четверг","пятница","суббота","воскресенье"][d.weekday()]
        date_str = f"{weekday}, {d.day} {months[d.month-1]} {d.year}"
        return random.choice(responses).replace("%date%", date_str), False

    # Приветствие, прощание, благодарность, общий_разговор — просто ответ
    return random.choice(responses), should_exit
