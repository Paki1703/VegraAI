# -*- coding: utf-8 -*-
"""
Графическое приложение VegraAI: чат, переключатель Вкл/Выкл голоса.
Запуск: python gui_app.py
"""

import sys
import threading
from pathlib import Path

# Чтобы работали импорты при запуске из любой папки
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import customtkinter as ctk
from voice_input import listen_once
from voice_output import speak
from assistant import process
from neural.intents_model import IntentPredictor


# Стиль в духе Джарвиса: тёмный, с голубыми акцентами
COLORS = {
    "bg": "#0d1117",
    "surface": "#161b22",
    "user_bubble": "#1f6feb",
    "assistant_bubble": "#21262d",
    "accent": "#58a6ff",
    "text": "#e6edf3",
    "text_dim": "#8b949e",
}


def make_bubble(parent, text: str, is_user: bool, **kwargs) -> ctk.CTkFrame:
    fg = COLORS["user_bubble"] if is_user else COLORS["assistant_bubble"]
    f = ctk.CTkFrame(
        parent,
        fg_color=fg,
        corner_radius=12,
        **kwargs,
    )
    lbl = ctk.CTkLabel(
        f,
        text=text,
        wraplength=320,
        justify="left",
        text_color=COLORS["text"],
        font=ctk.CTkFont(size=14),
    )
    lbl.pack(padx=14, pady=10, anchor="w")
    return f


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VegraAI")
        self.geometry("480x640")
        self.minsize(400, 500)

        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLORS["bg"])

        self.predictor: IntentPredictor | None = None
        self.voice_on = ctk.BooleanVar(value=True)
        self.last_intent: str | None = None
        self._build_ui()
        self.after(200, self._init_model)

    def _build_ui(self):
        # ---- Верхняя панель: логотип + переключатель Вкл/Выкл ----
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            top,
            text="VegraAI",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side="left")

        # Блок переключателя: "Голос" + [Вкл|Выкл] + switch
        voice_frame = ctk.CTkFrame(top, fg_color="transparent")
        voice_frame.pack(side="right")

        ctk.CTkLabel(
            voice_frame,
            text="Голос",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 6))

        self.switch = ctk.CTkSwitch(
            voice_frame,
            text="",
            variable=self.voice_on,
            onvalue=True,
            offvalue=False,
            progress_color=COLORS["accent"],
            button_color=COLORS["assistant_bubble"],
            button_hover_color=COLORS["user_bubble"],
            width=44,
            command=self._on_voice_toggle,
        )
        self.switch.pack(side="left", padx=(0, 6))

        self.voice_label = ctk.CTkLabel(
            voice_frame,
            text="Вкл",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["accent"],
        )
        self.voice_label.pack(side="left")

        # ---- Чат (прокручиваемая область) ----
        self.chat = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["surface"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        self.chat.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Приветствие
        self._add_msg("assistant", "Привет. Я VegraAI. Пиши сюда или нажми 🎤 и говори. Переключатель «Голос» включает или выключает микрофон и озвучку.")

        # ---- Строка ввода ----
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 16))

        self.entry = ctk.CTkEntry(
            row,
            placeholder_text="Сообщение...",
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["surface"],
            border_color=COLORS["accent"],
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self._on_send())

        ctk.CTkButton(
            row,
            text="Отправить",
            width=100,
            height=40,
            fg_color=COLORS["user_bubble"],
            hover_color=COLORS["accent"],
            command=self._on_send,
        ).pack(side="left", padx=(0, 8))

        self.btn_mic = ctk.CTkButton(
            row,
            text="🎤",
            width=44,
            height=40,
            fg_color=COLORS["surface"],
            hover_color=COLORS["assistant_bubble"],
            command=self._on_voice,
        )
        self.btn_mic.pack(side="left")

        self._on_voice_toggle()  # синхронизировать подпись и кнопку с переключателем

    def _on_voice_toggle(self):
        on = self.voice_on.get()
        self.voice_label.configure(text="Вкл" if on else "Выкл")
        if on:
            self.voice_label.configure(text_color=COLORS["accent"])
        else:
            self.voice_label.configure(text_color=COLORS["text_dim"])
        self.btn_mic.configure(state="normal" if on else "disabled")

    def _init_model(self):
        try:
            if (ROOT / "data" / "intent_model.pt").exists():
                self.predictor = IntentPredictor()
                self._add_msg("assistant", "Модель загружена. Можешь писать или говорить.")
            else:
                self.predictor = None
                self._add_msg("assistant", "Модель не обучена. Выполни: python neural/train.py")
        except Exception as e:
            self.predictor = None
            self._add_msg("assistant", f"Ошибка загрузки модели: {e}")

    def _add_msg(self, role: str, text: str):
        row = ctk.CTkFrame(self.chat, fg_color="transparent")
        row.pack(fill="x", pady=4)
        bubble = make_bubble(row, text, is_user=(role == "user"))
        if role == "user":
            bubble.pack(side="right", padx=8)
        else:
            bubble.pack(side="left", padx=8)
        canvas = getattr(self.chat, "_parent_canvas", None) or getattr(self.chat, "parent_canvas", None)
        if canvas:
            canvas.yview_moveto(1.0)

    def _on_send(self):
        t = (self.entry.get() or "").strip()
        if not t:
            return
        self.entry.delete(0, "end")
        self._add_msg("user", t)
        self._run_process(t, use_speak=self.voice_on.get())

    def _on_voice(self):
        if not self.voice_on.get():
            return
        self.btn_mic.configure(state="disabled", text="…")
        threading.Thread(target=self._voice_thread, daemon=True).start()

    def _voice_thread(self):
        def enable_mic():
            self.btn_mic.configure(state="normal", text="🎤")

        text = listen_once()
        if not text:
            self.after(0, lambda: self._add_msg("assistant", "Не расслышал. Попробуй ещё раз."))
            self.after(0, enable_mic)
            return

        self.after(0, lambda: self._add_msg("user", text))

        if not self.predictor:
            self.after(0, lambda: self._add_msg("assistant", "Сначала обучи нейросеть: python neural/train.py"))
            self.after(0, enable_mic)
            return

        try:
            resp, _, tag = process(text, self.predictor, self.last_intent)
            self.after(0, lambda r=resp, t=tag: (self._add_msg("assistant", r), setattr(self, "last_intent", t)))
            if self.voice_on.get():
                speak(resp, block=True)
        except Exception as e:
            self.after(0, lambda: self._add_msg("assistant", f"Ошибка: {e}"))
        self.after(0, enable_mic)

    def _run_process(self, text: str, use_speak: bool):
        def work():
            if not self.predictor:
                self.after(0, lambda: self._add_msg("assistant", "Сначала обучи нейросеть: python neural/train.py"))
                return
            try:
                resp, _, tag = process(text, self.predictor, self.last_intent)
                self.after(0, lambda r=resp, t=tag: (self._add_msg("assistant", r), setattr(self, "last_intent", t)))
                if use_speak:
                    speak(resp, block=True)
            except Exception as e:
                self.after(0, lambda: self._add_msg("assistant", f"Ошибка: {e}"))

        threading.Thread(target=work, daemon=True).start()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
