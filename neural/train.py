# -*- coding: utf-8 -*-
"""
Скрипт обучения нейросети для классификации намерений.
Запусти один раз: python neural/train.py
"""
import sys
from pathlib import Path

# Чтобы импорты config и neural работали при любом текущем каталоге
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
import re

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from neural.intents_model import IntentClassifier, tokenize
from config import INTENTS_FILE, MODEL_PATH, VOCAB_PATH


def load_intents(path: str) -> tuple[list[tuple[list[str], str]]]:
    """Загружает (фразы, тег) из intents.json."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    samples = []
    for item in data["intents"]:
        tag = item["tag"]
        for p in item["patterns"]:
            samples.append((tokenize(p), tag))
    return samples


class IntentsDataset(Dataset):
    def __init__(self, samples, vocab, tags, max_len=20):
        self.samples = samples
        self.vocab = vocab
        self.tags = tags
        self.tag_to_idx = {t: i for i, t in enumerate(tags)}
        self.max_len = max_len

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        words, tag = self.samples[i]
        ids = [self.vocab.get(w, self.vocab.get("<unk>", 1)) for w in words]
        if len(ids) > self.max_len:
            ids = ids[: self.max_len]
        while len(ids) < self.max_len:
            ids.append(0)
        return torch.tensor(ids, dtype=torch.long), self.tag_to_idx[tag]


def build_vocab(samples) -> dict[str, int]:
    vocab = {"<pad>": 0, "<unk>": 1}
    for words, _ in samples:
        for w in words:
            if w not in vocab:
                vocab[w] = len(vocab)
    return vocab


def main():
    path = ROOT / INTENTS_FILE
    if not path.exists():
        print(f"Файл не найден: {path}")
        return
    samples = load_intents(str(path))
    tags = sorted(set(s[1] for s in samples))
    vocab = build_vocab(samples)

    (ROOT / MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / VOCAB_PATH).parent.mkdir(parents=True, exist_ok=True)

    dataset = IntentsDataset(samples, vocab, tags)
    loader = DataLoader(dataset, batch_size=16, shuffle=True)
    print(f"Интентов: {len(tags)}, примеров: {len(samples)}")

    model = IntentClassifier(
        vocab_size=len(vocab),
        embedding_dim=64,
        hidden_dim=64,
        num_classes=len(tags),
    )
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(60):
        total = 0
        for x, y in loader:
            opt.zero_grad()
            logits = model(x)
            loss = loss_fn(logits, y)
            loss.backward()
            opt.step()
            total += loss.item()
        if (epoch + 1) % 10 == 0:
            print(f"Эпоха {epoch+1}, loss: {total/len(loader):.4f}")

    torch.save(model.state_dict(), ROOT / MODEL_PATH)
    with open(ROOT / VOCAB_PATH, "w", encoding="utf-8") as f:
        json.dump({"vocab": vocab, "tags": tags}, f, ensure_ascii=False, indent=2)
    print(f"Модель сохранена: {ROOT / MODEL_PATH}")
    print(f"Словарь: {ROOT / VOCAB_PATH}")


if __name__ == "__main__":
    main()
