@echo off
title Invoice Generator
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo The virtual environment was not found.
    echo Follow the Installation steps in README.md first.
    pause
    exit /b 1
)

call venv\Scripts\activate

rem Bring the database up to date and make the first login if it does not exist yet.
python manage.py migrate --noinput
python manage.py create_default_user

echo.
echo Invoice Generator is starting.
echo Open http://127.0.0.1:8000 in your browser.
echo Close this window or press Ctrl+C to stop it.
echo.
python manage.py runserver 127.0.0.1:8000
pause
