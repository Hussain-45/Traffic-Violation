@echo off
echo =====================================================================
echo 🚦 Starting AI-Powered Smart Traffic Violation Detection System...
echo =====================================================================

:: Check if backend virtualenv or requirements need install
echo [System] Booting FastAPI Backend...
start cmd /k "echo Starting Backend Service... & python -m uvicorn backend.app.main:app --reload --port 8000"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak > nul

:: Check if frontend npm modules are installed and start dev server
echo [System] Booting Vite React Frontend...
start cmd /k "echo Starting Frontend Service... & cd frontend & npm run dev"

echo =====================================================================
echo Services dispatched!
echo 💻 Front-end local server: http://localhost:5173
echo ⚙️ Back-end API docs: http://localhost:8000/docs
echo =====================================================================
pause
