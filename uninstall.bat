@echo off
rem ============================================================================
rem  uninstall.bat - removes the .venv environment (the libraries) of Quaesitor
rem  Double-click it, or from PowerShell:  .\uninstall.bat
rem  The program is not "installed" in Windows: it is only this folder.
rem  This file removes the libraries (.venv) and the temporary files; it asks
rem  before touching the cases (data) and Tesseract (tools). It never touches
rem  chatbot.conf, services.conf and the "sources" folder.
rem  To remove everything: delete the program folder.
rem ============================================================================
rem "Homo homini lupus." (Plautus, Asinaria)
rem Man is a wolf to man.
setlocal EnableDelayedExpansion
cd /d "%~dp0"
echo.
echo  === Quaesitor - uninstall ===
echo.
if exist ".venv" (
    echo  Removing the .venv environment ...
    rmdir /s /q ".venv"
) else (
    echo  No .venv environment present.
)
for /d /r %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d"
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

if exist "data" (
    echo.
    echo  WARNING: the "data" folder contains the CASES (nodes, cards, notes, views).
    set "DEL_DATA=N"
    set /p "DEL_DATA=  Delete the cases as well? They cannot be recovered. [y/N] "
    if /i "!DEL_DATA!"=="y" goto :deldata
    goto :tools
)
goto :tools

:deldata
rmdir /s /q "data"
echo  The data folder has been deleted.

:tools
if exist "tools\tesseract" (
    set "DEL_TOOLS=N"
    set /p "DEL_TOOLS=  Remove Tesseract as well (tools\tesseract)? [y/N] "
    if /i "!DEL_TOOLS!"=="y" rmdir /s /q "tools\tesseract"
)
echo.
echo  Done. Left in place: the program, chatbot.conf, services.conf, the "sources" folder
echo  and, unless you deleted them, data and tools. To remove everything, delete the folder.
pause
endlocal
exit /b 0
