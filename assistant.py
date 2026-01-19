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
from config import INTENTS_FILE, APPS, LLM_ENABLED, LLM_MODEL, LLM_MAX_LENGTH


# Команды поиска: если фраза НАЧИНАЕТСЯ с одного из них — это всегда поиск (мимо нейросети)
SEARCH_PREFIXES = [
    "найди в интернете",
    "поищи в интернете",
    "найди в гугл",
    "поищи в гугле",
    "найди в браузере",
    "найди в яндексе",
    "открой в браузере",
    "поиск в интернете",
    "найдите",
    "поищите",
    "загугли",
    "погугли",
    "найди",
    "найти",
    "поищи",
]

# Команды открыть приложение: если фраза начинается с них — всегда открыть (мимо нейросети)
OPEN_APP_PREFIXES = ("открой ", "запусти ", "включи ")

# Неявный поиск: «как сделать», «рецепт» и т.п. без «найди/поищи» — всё равно поиск
IMPLICIT_SEARCH_PREFIXES = (
    "как сделать",
    "как приготовить",
    "как готовить",
    "как сварить",
    "как запечь",
    "как испечь",
    "рецепт ",
)

# Продолжение поиска после предыдущего: «а теперь смартфон», «теперь X», «ещё X»
FOLLOW_UP_PREFIXES = ("а теперь ", "теперь ", "и ещё ", "ещё ", "а ещё ")
FOLLOW_UP_BLOCKLIST = frozenset(("что", "как", "это", "всё", "так", "да", "нет", "хорошо", "понятно", "ладно", "окей"))


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
    """Убирает команду поиска из начала фразы и возвращает запрос."""
    t = text.strip()
    for p in sorted(SEARCH_PREFIXES, key=len, reverse=True):
        if t.lower().startswith(p):
            return t[len(p) :].strip()
    return t


def _is_search_command(text: str) -> bool:
    """Фраза явно начинается с команды поиска — не отдаём в нейросеть."""
    t = text.strip().lower()
    return any(t.startswith(p) for p in SEARCH_PREFIXES)


def _is_open_app_command(text: str) -> bool:
    """Фраза явно начинается с «открой / запусти / включи» — не отдаём в нейросеть."""
    t = text.strip().lower()
    return any(t.startswith(p) for p in OPEN_APP_PREFIXES)


def _is_implicit_search(text: str) -> bool:
    """«Как сделать X», «рецепт X» и т.п. — неявный запрос на поиск."""
    t = text.strip().lower()
    return any(t.startswith(p) for p in IMPLICIT_SEARCH_PREFIXES)


def _llm_reply(user_text: str, intent_tag: str) -> str | None:
    """
    Ответ от LLM (Ollama) вместо шаблона. Возвращает None при отключении/ошибке — тогда используется шаблон.
    """
    if not LLM_ENABLED:
        return None
    system = (
        "Ты VegraAI — голосовой помощник в стиле Джарвиса. Отвечай на русском, кратко (1–4 предложения) и по-человечески. "
        "Можешь шутить, подбадривать, давать советы. Не говори «я нейросеть» или «я программа», если не спросят. "
        "Стиль: дружелюбный, умный, с лёгким юмором. Контекст реплики: " + intent_tag.replace("_", " ") + "."
    )
    try:
        from ollama import chat

        r = chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_text},
            ],
        )
        content = (r.message.content or "").strip()
        if not content:
            return None
        if len(content) > LLM_MAX_LENGTH:
            cut = content[: LLM_MAX_LENGTH + 1]
            last = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "), cut.rfind("\n"))
            content = cut[: last + 1].strip() if last > LLM_MAX_LENGTH // 2 else cut[:LLM_MAX_LENGTH].rstrip(" .,!?") + "."
        return content
    except Exception:
        return None


def _get_follow_up_search_query(text: str, last_intent: str | None) -> str | None:
    """Если прошлый ответ был поиск и фраза «а теперь X» / «теперь X» / «ещё X» — вернуть X как запрос."""
    if last_intent != "поиск_в_интернете":
        return None
    t = text.strip().lower()
    for p in FOLLOW_UP_PREFIXES:
        if t.startswith(p):
            rest = t[len(p) :].strip()
            if len(rest) >= 2 and rest not in FOLLOW_UP_BLOCKLIST:
                return rest
    return None


def process(text: str, predictor: IntentPredictor | None = None, last_intent: str | None = None) -> tuple[str, bool, str | None]:
    """
    Обрабатывает фразу: жёсткий фильтр (продолжение поиска, неявный поиск, явный поиск, открыть),
    потом нейросеть (поболтать, время, дата и т.п.). Возвращает (ответ, выйти?, тег_намерения).
    """
    if predictor is None:
        predictor = IntentPredictor()
    intents_data = _load_intents()
    t = text.strip().lower()
    search_query_override: str | None = None

    # 1) Продолжение поиска: «а теперь смартфон», «теперь X», «ещё X» после прошлого поиска
    if (q := _get_follow_up_search_query(text, last_intent)) is not None:
        tag = "поиск_в_интернете"
        search_query_override = q
    # 2) Неявный поиск: «как сделать мясо», «рецепт борща» — без «найди/поищи»
    elif _is_implicit_search(text):
        tag = "поиск_в_интернете"
        search_query_override = text.strip()
    # 3) Явные команды поиска: «найди», «поищи», «загугли» …
    elif _is_search_command(text):
        tag = "поиск_в_интернете"
    # 4) «Открой / запусти / включи»
    elif _is_open_app_command(text):
        tag = "открыть_приложение"
    # 5) Всё остальное — нейросеть
    else:
        tag = predictor.predict(text)

    intent = next((i for i in intents_data["intents"] if i["tag"] == tag), None)
    if not intent:
        return "Не удалось определить намерение.", False, None

    responses = intent.get("responses", ["Понял."])
    should_exit = tag == "прощание"

    # --- Действия ---

    if tag == "открыть_приложение":
        app_key = _extract_app_name(text)
        if not app_key:
            return "Не понял, какое приложение открыть. Назови, например: блокнот, калькулятор, браузер.", False, tag
        ok = open_app(app_key)
        rep = random.choice(responses).replace("%app%", app_key)
        return rep if ok else f"Не получилось открыть {app_key}. Проверь название в config.APPS.", False, tag

    if tag == "поиск_в_интернете":
        query = search_query_override if search_query_override is not None else _extract_search_query(text)
        if not query:
            return "Уточни, что искать в интернете.", False, tag
        ok = search_in_browser(query)
        rep = random.choice(responses).replace("%query%", query)
        return rep if ok else "Не удалось открыть браузер.", False, tag

    if tag == "текущее_время":
        time_str = datetime.now().strftime("%H:%M")
        return random.choice(responses).replace("%time%", time_str), False, tag

    if tag == "текущая_дата":
        months = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()
        d = datetime.now()
        weekday = ["понедельник","вторник","среда","четверг","пятница","суббота","воскресенье"][d.weekday()]
        date_str = f"{weekday}, {d.day} {months[d.month-1]} {d.year}"
        return random.choice(responses).replace("%date%", date_str), False, tag

    # Разговорные интенты: ответ даёт LLM (Ollama), иначе — шаблон
    if LLM_ENABLED:
        llm = _llm_reply(text, tag)
        if llm:
            return llm, should_exit, tag
    return random.choice(responses), should_exit, tag
