@echo off
rem ============================================================================
rem  avvia.bat - avvia OSInt Graph e apre il browser su http://127.0.0.1:5000
rem  Doppio clic, oppure da PowerShell:  .\avvia.bat
rem  Il server resta in questa finestra: chiuderla (o Ctrl+C) ferma il programma.
rem  Porta diversa: impostare la variabile PORT prima di lanciare (es. set PORT=5050).
rem  Nota: in modalita' sviluppo Werkzeug avvia un secondo processo (reloader):
rem  e' normale vedere i messaggi di avvio due volte.
rem ============================================================================
rem "Trahit sua quemque voluptas." (Virgil, Eclogues)
rem Each is drawn by his own desire.
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo  Ambiente .venv non trovato: esegui prima installa.bat
    pause
    exit /b 1
)
if not defined PORT set "PORT=5000"
echo  OSInt Graph su http://127.0.0.1:%PORT%  (chiudi questa finestra per fermarlo)
rem apre il browser dopo 3 secondi, in un processo a parte, senza finestra
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:%PORT%"
".venv\Scripts\python.exe" app.py
endlocal
