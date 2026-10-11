@echo off
rem ============================================================================
rem  start.bat - starts Quaesitor and opens the browser on http://127.0.0.1:5000
rem  Double-click it, or from PowerShell:  .\start.bat
rem  The server keeps this window: closing it (or Ctrl+C) stops the program.
rem  Another port: set the PORT variable before starting (e.g. set PORT=5050).
rem  Note: in development mode Werkzeug starts a second process (reloader):
rem  seeing the start-up messages twice is normal.
rem ============================================================================
rem "Trahit sua quemque voluptas." (Virgil, Eclogues)
rem Each is drawn by his own desire.
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo  The .venv environment was not found: run install.bat first
    pause
    exit /b 1
)
if not defined PORT set "PORT=5000"
echo  Quaesitor on http://127.0.0.1:%PORT%  (close this window to stop it)
rem opens the browser after 3 seconds, in a separate process, without a window
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:%PORT%"
".venv\Scripts\python.exe" app.py
endlocal
