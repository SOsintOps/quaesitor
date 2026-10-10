@echo off
rem ============================================================================
rem  disinstalla.bat - rimuove l'ambiente .venv (le librerie) di OSInt Graph
rem  Doppio clic, oppure da PowerShell:  .\disinstalla.bat
rem  Il programma non e' "installato" in Windows: e' solo questa cartella.
rem  Questo file toglie le librerie (.venv) e i file temporanei; chiede conferma
rem  prima di toccare i dati dei casi (data) e Tesseract (tools). Non tocca mai
rem  chatbot.conf, services.conf e la cartella fonti.
rem  Per eliminare tutto: cancella la cartella del programma.
rem ============================================================================
rem "Homo homini lupus." (Plautus, Asinaria)
rem Man is a wolf to man.
setlocal EnableDelayedExpansion
cd /d "%~dp0"
echo.
echo  === OSInt Graph - disinstallazione ===
echo.
if exist ".venv" (
    echo  Rimuovo l'ambiente .venv ...
    rmdir /s /q ".venv"
) else (
    echo  Ambiente .venv non presente.
)
for /d /r %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d"
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

if exist "data" (
    echo.
    echo  ATTENZIONE: la cartella "data" contiene i CASI (nodi, schede, note, viste).
    set "DEL_DATA=N"
    set /p "DEL_DATA=  Cancellare anche i dati dei casi? Non si recuperano. [s/N] "
    if /i "!DEL_DATA!"=="s" goto :deldata
    goto :tools
)
goto :tools

:deldata
rmdir /s /q "data"
echo  Cartella data cancellata.

:tools
if exist "tools\tesseract" (
    set "DEL_TOOLS=N"
    set /p "DEL_TOOLS=  Rimuovere anche Tesseract (tools\tesseract)? [s/N] "
    if /i "!DEL_TOOLS!"=="s" rmdir /s /q "tools\tesseract"
)
echo.
echo  Fatto. Restano: il programma, chatbot.conf, services.conf, la cartella fonti
echo  e, se non li hai cancellati, data e tools. Per eliminare tutto cancella la cartella.
pause
endlocal
exit /b 0
