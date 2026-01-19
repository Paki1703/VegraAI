# -*- coding: utf-8 -*-
"""
Нейронная сеть для классификации намерений (intent) по тексту пользователя.
"""

import json
import re
from pathlib import Path

import torch
import torch.nn as nn

from config import INTENTS_FILE, MODEL_PATH, VOCAB_PATH


def tokenize(text: str) -> list[str]:
    """Разбивает текст на слова (нижний регистр, только буквы и цифры)."""
    text = text.lower().strip()
    # Оставляем буквы, цифры, апостроф (для "что-то")
    words = re.findall(r"[a-zа-яё0-9]+", text, re.IGNORECASE)
    return [w.lower() for w in words] if words else ["<пусто>"]


class IntentClassifier(nn.Module):
    """Простая сеть: Embedding -> LSTM -> FC -> класс намерения."""

    def __init__(self, vocab_size: int, embedding_dim: int, hidden_dim: int, num_classes: int, pad_idx: int = 0):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_idx)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)
        self.num_classes = num_classes

    def forward(self, x):
        # x: [batch, seq_len]
        e = self.embed(x)
        out, (h, _) = self.lstm(e)
        # Берём последний скрытый слой
        logits = self.fc(h.squeeze(0))
        return logits


class IntentPredictor:
    """Загружает модель и словарь, предсказывает намерение по фразе."""

    def __init__(self, intents_path: str = None, model_path: str = None, vocab_path: str = None):
        self.intents_path = Path(intents_path or INTENTS_FILE)
        self.model_path = Path(model_path or MODEL_PATH)
        self.vocab_path = Path(vocab_path or VOCAB_PATH)
        self.vocab: dict[str, int] = {}
        self.idx_to_tag: list[str] = []
        self.model: IntentClassifier | None = None
        self.max_len = 20
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        if not self.model_path.exists() or not self.vocab_path.exists():
            raise FileNotFoundError(
                "Модель не обучена. Сначала запусти: python neural/train.py"
            )
        with open(self.vocab_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.vocab = data["vocab"]
        self.idx_to_tag = data["tags"]
        num_classes = len(self.idx_to_tag)
        vocab_size = len(self.vocab)
        self.model = IntentClassifier(
            vocab_size=vocab_size,
            embedding_dim=64,
            hidden_dim=64,
            num_classes=num_classes,
        )
        self.model.load_state_dict(torch.load(self.model_path, map_location="cpu"))
        self.model.eval()
        self._loaded = True

    def predict(self, text: str) -> str:
        """Возвращает тег намерения (например, 'открыть_приложение')."""
        self._ensure_loaded()
        words = tokenize(text)
        ids = [self.vocab.get(w, self.vocab.get("<unk>", 1)) for w in words]
        if len(ids) > self.max_len:
            ids = ids[: self.max_len]
        while len(ids) < self.max_len:
            ids.append(0)  # PAD
        x = torch.tensor([ids], dtype=torch.long)
        with torch.no_grad():
            logits = self.model(x)
        pred = logits.argmax(dim=1).item()
        return self.idx_to_tag[pred]
