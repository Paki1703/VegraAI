@echo off
cd /d "%~dp0"

git status
echo.
echo Сейчас: add, commit, push. Репозиторий на GitHub/GitLab должен быть уже создан.
echo.
pause

git add .
git status
echo.
set /p MSG="Текст коммита (Enter = VegraAI update): "
if "%MSG%"=="" set "MSG=VegraAI update"
git commit -m "%MSG%"

echo.
echo Пуш в origin main...
git push -u origin main
if errorlevel 1 (
  echo Не удалось. Попробуй: git push -u origin master
  git push -u origin master
)
echo.
pause
