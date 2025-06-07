@echo off
echo Starting all services...

REM Navigate to the project root directory (where this script is located)
cd /d "%~dp0"

REM Define path to venv activation script (adjust if your venv is named differently or elsewhere)
SET VENV_ACTIVATE_SCRIPT=.venv\Scripts\activate.bat

REM Start Backend API
echo Starting Backend API (python run.py)...
START "Backend API" cmd /k "cd chatbot-backend && call %~dp0%VENV_ACTIVATE_SCRIPT% && python run.py"

REM Start Celery Worker
echo Starting Celery Worker...
START "Celery Worker" cmd /k "cd chatbot-backend && call %~dp0%VENV_ACTIVATE_SCRIPT% && celery -A celery_worker.celery_app worker --loglevel=info -P gevent -c 12"

REM Start Widget Server
echo Starting Widget Server (python -m http.server 8000)...
START "Widget Server" cmd /k "cd chatbot-widget && python -m http.server 8000"

REM Start Frontend Dev Server
echo Starting Frontend Dev Server (npm run dev)...
START "Frontend Dev Server" cmd /k "cd chatbot-frontend && npm run dev"

echo All services are being started in separate windows.
