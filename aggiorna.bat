@echo off
rem ============================================================================
rem  aggiorna.bat - aggiorna OSInt Graph dal repository e le librerie
rem  Doppio clic, oppure da PowerShell:  .\aggiorna.bat
rem  Richiede git (https://git-scm.com). Non tocca dati e configurazioni.
rem ============================================================================
rem "Aliena vitia in oculis habemus, a tergo nostra sunt." (Seneca, De Ira)
rem Other people's faults are before our eyes; our own are behind our backs.
setlocal
cd /d "%~dp0"
echo.
echo  === OSInt Graph - aggiornamento ===
echo.
where git >nul 2>&1
if errorlevel 1 (
    echo  git non trovato: scarica l'aggiornamento a mano da GitHub e sostituisci
    echo  i file del programma, poi rilancia installa.bat.
    pause
    exit /b 1
)
git pull
if errorlevel 1 (
    echo  ERRORE: git pull fallito. Vedi i messaggi qui sopra.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo  Ambiente .venv non trovato: esegui installa.bat
    pause
    exit /b 1
)
echo  Aggiorno le librerie ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 (
    echo  ERRORE: aggiornamento delle librerie fallito.
    pause
    exit /b 1
)
echo.
echo  Aggiornamento completato. Se il programma era in esecuzione, riavvialo con avvia.bat.
pause
endlocal
exit /b 0
