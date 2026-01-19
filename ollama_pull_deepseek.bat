@echo off
echo Скачиваю DeepSeek R1 (7B) для Ollama, может занять несколько минут...
ollama pull deepseek-r1:7b-qwen-distill-q4_K_M
echo.
echo Готово. В config.py поставь: LLM_MODEL = "deepseek-r1:7b-qwen-distill-q4_K_M"
pause
