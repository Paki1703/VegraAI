@echo off
echo Скачиваю Qwen для Ollama (пару минут)...
ollama pull qwen2.5:3b
echo.
echo Готово. В config.py поставь: LLM_MODEL = "qwen2.5:3b"
pause
