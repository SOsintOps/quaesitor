@echo off
rem ============================================================================
rem  installa.bat - installazione (o reinstallazione) di OSInt Graph su Windows
rem  Doppio clic, oppure da PowerShell:  .\installa.bat
rem  Cosa fa: trova Python 3.10+, crea l'ambiente .venv accanto al programma,
rem  installa le librerie, prepara chatbot.conf e services.conf dalle copie
rem  di esempio, crea la cartella "fonti", chiede se scaricare Tesseract (OCR).
rem  Si puo' rilanciare quante volte si vuole: non sovrascrive mai i file di
rem  configurazione ne' i dati (cartella data).
rem ============================================================================
rem "Noscitur ex socio, qui non cognoscitur ex se." (medieval proverb)
rem He who is not known by himself is known by his company.
setlocal
cd /d "%~dp0"
echo.
echo  === OSInt Graph - installazione ===
echo.

rem --- 1) Python -------------------------------------------------------------
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo  ERRORE: serve Python 3.10 o piu' recente e non e' stato trovato.
    echo  Scaricalo da https://www.python.org/downloads/windows/ e durante
    echo  l'installazione spunta "Add python.exe to PATH". Poi rilancia questo file.
    echo.
    pause
    exit /b 1
)
for /f "delims=" %%v in ('%PY% -c "import sys; print(sys.version.split()[0])"') do set "PYVER=%%v"
echo  Python trovato: %PYVER%  (%PY%)

rem --- 2) ambiente virtuale .venv ---------------------------------------------
if exist ".venv\Scripts\python.exe" (
    echo  Ambiente .venv gia' presente: lo riuso.
) else (
    echo  Creo l'ambiente .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo  ERRORE: creazione di .venv fallita.
        pause
        exit /b 1
    )
)
set "VPY=.venv\Scripts\python.exe"

rem --- 3) librerie -------------------------------------------------------------
echo  Aggiorno pip ...
"%VPY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
echo  Installo le librerie (requirements.txt) ...
"%VPY%" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  ERRORE: installazione delle librerie fallita. Controlla la connessione
    echo  e i messaggi qui sopra, poi rilancia installa.bat.
    pause
    exit /b 1
)

rem --- 4) file di configurazione (mai sovrascritti) ---------------------------
if not exist "chatbot.conf" (
    copy /y "chatbot.conf.example" "chatbot.conf" >nul
    echo  Creato chatbot.conf  (AI: spenta finche' non la configuri dal programma)
)
if not exist "services.conf" (
    copy /y "services.conf.example" "services.conf" >nul
    echo  Creato services.conf (OpenSanctions: spento finche' non lo configuri)
)
if not exist "fonti" (
    mkdir "fonti"
    echo  Creata la cartella "fonti" per i documenti da indicizzare
)

rem --- 5) Tesseract (OCR), facoltativo ----------------------------------------
echo.
set "OCR=N"
set /p "OCR=  Scaricare Tesseract per leggere il testo nelle immagini (OCR)? [s/N] "
if /i "%OCR%"=="s" (
    "%VPY%" setup_tesseract.py
    if errorlevel 1 echo  Tesseract non installato: si puo' riprovare dal programma, pannello Fonti.
)

rem --- fine ---------------------------------------------------------------------
echo.
echo  Installazione completata.
echo  - Per avviare il programma:  avvia.bat
echo  - Per aggiornarlo:           aggiorna.bat
echo  - I dati dei casi stanno in: %~dp0data
echo.
pause
endlocal
exit /b 0
