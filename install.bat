@echo off
cd /d "%~dp0"
echo Устанавливаю все зависимости...
python -m pip install -r requirements.txt
echo.
echo Готово. Дальше: python neural/train.py  (один раз), потом: python gui_app.py  или  python main.py
pause
