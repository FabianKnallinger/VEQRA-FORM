@echo off
rem Startet die VEQRA Bridge unter Windows (Quellcode-Variante).
rem Voraussetzung: Python 3.11+ von https://www.python.org/downloads/windows/
setlocal

cd /d "%~dp0"

rem ---- Python suchen: erst der py-Launcher, dann python im PATH ----
set "PYTHON_CMD="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo.
    echo FEHLER: Python wurde auf diesem Rechner nicht gefunden.
    echo.
    echo So behebst du das:
    echo   1. Python installieren: https://www.python.org/downloads/windows/
    echo      WICHTIG: im Installer unten "Add python.exe to PATH" anhaken.
    echo   2. Dieses Fenster schliessen und run_windows.bat erneut starten.
    echo.
    echo Falls die Microsoft-Store-Meldung weiterhin erscheint:
    echo   Einstellungen ^> Apps ^> Erweiterte App-Einstellungen ^>
    echo   Aliase fuer App-Ausfuehrung: "python.exe" und "python3.exe" ausschalten.
    echo.
    pause
    exit /b 1
)

echo Verwende Python: %PYTHON_CMD%

rem ---- Virtuelle Umgebung einrichten (nur beim ersten Start) ----
if not exist ".venv-bridge\Scripts\python.exe" (
    echo Richte die Python-Umgebung ein, das dauert beim ersten Mal 1-2 Minuten...
    %PYTHON_CMD% -m venv .venv-bridge
    if errorlevel 1 goto :fehler
    ".venv-bridge\Scripts\python" -m pip install --upgrade pip
    if errorlevel 1 goto :fehler
    ".venv-bridge\Scripts\python" -m pip install -r requirements.txt
    if errorlevel 1 goto :fehler
)

echo.
echo VEQRA Bridge startet auf http://127.0.0.1:8899 (Beenden mit Strg+C)
echo Der Pairing-Token liegt in: %USERPROFILE%\.veqra-form\pairing-token.txt
echo.
".venv-bridge\Scripts\python" run_bridge.py
pause
exit /b 0

:fehler
echo.
echo FEHLER: Die Einrichtung ist fehlgeschlagen (Meldung siehe oben).
echo Tipp: Ordner .venv-bridge loeschen und run_windows.bat erneut starten.
pause
exit /b 1
