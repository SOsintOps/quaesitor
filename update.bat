@echo off
rem ============================================================================
rem  update.bat - updates Quaesitor from the repository, and the libraries
rem  Double-click it, or from PowerShell:  .\update.bat
rem  Requires git (https://git-scm.com). Data and settings are not touched.
rem ============================================================================
rem "Aliena vitia in oculis habemus, a tergo nostra sunt." (Seneca, De Ira)
rem Other people's faults are before our eyes; our own are behind our backs.
setlocal
cd /d "%~dp0"
echo.
echo  === Quaesitor - update ===
echo.
where git >nul 2>&1
if errorlevel 1 (
    echo  git not found: download the update by hand from GitHub, replace the
    echo  program files, then run install.bat again.
    pause
    exit /b 1
)
git pull
if errorlevel 1 (
    echo  ERROR: git pull failed. See the messages above.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo  The .venv environment was not found: run install.bat
    pause
    exit /b 1
)
echo  Updating the libraries ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 (
    echo  ERROR: the libraries could not be updated.
    pause
    exit /b 1
)
rem the video transcription is updated only where it was installed
".venv\Scripts\python.exe" -c "import faster_whisper" >nul 2>&1
if not errorlevel 1 (
    echo  Updating the video transcription libraries ...
    ".venv\Scripts\python.exe" -m pip install -r requirements-audio.txt --disable-pip-version-check
)
echo.
echo  Update complete. If the program was running, restart it with start.bat.
pause
endlocal
exit /b 0
