# -*- coding: utf-8 -*-
"""
Управление ПК: открытие приложений, поиск в браузере.
"""

import subprocess
import urllib.parse
from pathlib import Path

from config import APPS, SEARCH_URL


def open_app(name: str) -> bool:
    """
    Открывает приложение по имени.
    name — как пользователь назвал (например, "блокнот", "калькулятор").
    Возвращает True, если команда запущена.
    """
    name = name.strip().lower()
    # Прямое совпадение
    if name in APPS:
        cmd = APPS[name]
        return _run(cmd)
    # Ищем по частичному совпадению (на случай "открой блокнот" -> name может быть "блокнот")
    for key, exe in APPS.items():
        if key in name or name in key:
            return _run(exe)
    return False


def _run(cmd: str) -> bool:
    if not cmd:
        return False
    try:
        # Для ms-settings:, URL и браузеров — start, чтобы Windows нашёл программу
        if cmd.startswith("ms-") or "://" in cmd or cmd in ("chrome", "msedge", "firefox"):
            subprocess.Popen(f"start {cmd}", shell=True)
        else:
            subprocess.Popen(cmd, shell=True)
        return True
    except Exception:
        return False


def search_in_browser(query: str) -> bool:
    """Открывает в браузере по умолчанию страницу поиска с запросом."""
    if not query or not query.strip():
        return False
    url = SEARCH_URL.format(query=urllib.parse.quote_plus(query.strip()))
    try:
        subprocess.Popen(f"start {url}", shell=True)
        return True
    except Exception:
        return False
