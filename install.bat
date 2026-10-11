@echo off
rem ============================================================================
rem  install.bat - installs (or reinstalls) Quaesitor on Windows
rem  Double-click it, or from PowerShell:  .\install.bat
rem  What it does: finds Python 3.10+, creates the .venv environment next to
rem  the program, installs the libraries, prepares chatbot.conf and
rem  services.conf from the example copies, creates the "fonti" folder for the
rem  document sources, asks whether to download Tesseract (OCR).
rem  It can be run again as often as needed: it never overwrites the settings
rem  files or the data (the "data" folder).
rem ============================================================================
rem "Noscitur ex socio, qui non cognoscitur ex se." (medieval proverb)
rem He who is not known by himself is known by his company.
setlocal
cd /d "%~dp0"
echo.
echo  === Quaesitor - install ===
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
    echo  ERROR: Python 3.10 or newer is required and was not found.
    echo  Download it from https://www.python.org/downloads/windows/ and tick
    echo  "Add python.exe to PATH" during the installation. Then run this file again.
    echo.
    pause
    exit /b 1
)
for /f "delims=" %%v in ('%PY% -c "import sys; print(sys.version.split()[0])"') do set "PYVER=%%v"
echo  Python found: %PYVER%  (%PY%)

rem --- 2) virtual environment .venv --------------------------------------------
if exist ".venv\Scripts\python.exe" (
    echo  The .venv environment already exists: reusing it.
) else (
    echo  Creating the .venv environment ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo  ERROR: could not create .venv.
        pause
        exit /b 1
    )
)
set "VPY=.venv\Scripts\python.exe"

rem --- 3) libraries ------------------------------------------------------------
echo  Updating pip ...
"%VPY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
echo  Installing the libraries (requirements.txt) ...
"%VPY%" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  ERROR: the libraries could not be installed. Check the connection and
    echo  the messages above, then run install.bat again.
    pause
    exit /b 1
)

rem --- 4) settings files (never overwritten) ------------------------------------
if not exist "chatbot.conf" (
    copy /y "chatbot.conf.example" "chatbot.conf" >nul
    echo  Created chatbot.conf  (AI: off until you configure it from the program)
)
if not exist "services.conf" (
    copy /y "services.conf.example" "services.conf" >nul
    echo  Created services.conf (OpenSanctions and Epieos: off until you configure them)
)
if not exist "fonti" (
    mkdir "fonti"
    echo  Created the "fonti" folder for the documents to index
)

rem --- 5) Tesseract (OCR), optional --------------------------------------------
echo.
set "OCR=N"
set /p "OCR=  Download Tesseract to read the text in images (OCR)? [y/N] "
if /i "%OCR%"=="y" (
    "%VPY%" setup_tesseract.py
    if errorlevel 1 echo  Tesseract not installed: you can retry from the program, Sources panel.
)

rem --- done ---------------------------------------------------------------------
echo.
echo  Installation complete.
echo  - To start the program:  start.bat
echo  - To update it:          update.bat
echo  - The cases are kept in: %~dp0data
echo.
pause
endlocal
exit /b 0
