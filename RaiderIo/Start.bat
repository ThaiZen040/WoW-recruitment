@echo off
rem ======================================================================
rem Start.bat - startet den Rekrutierungs-Scraper per Doppelklick.
rem Beim ersten Start wird alles Noetige automatisch installiert.
rem Voraussetzung: Python ist auf dem PC installiert.
rem ======================================================================

rem In den Ordner wechseln, in dem diese Datei liegt.
cd /d "%~dp0"
title Rekrutierungs-Scraper
rem Sonderzeichen in Namen (z. B. kyrillisch) sicher ausgeben.
set "PYTHONUTF8=1"

rem --- 1. Python suchen -------------------------------------------------
set "PY="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python --version >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo.
    echo Python wurde nicht gefunden.
    echo Bitte installieren: https://www.python.org/downloads/
    echo WICHTIG: Beim Installieren den Haken bei "Add python.exe to PATH" setzen.
    echo Danach diese Datei nochmal starten.
    echo.
    pause
    exit /b 1
)

rem --- 2. Python-Version pruefen: mindestens 3.8 ------------------------
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
if errorlevel 1 (
    echo.
    echo Dein Python ist zu alt. Bitte Python 3.8 oder neuer installieren:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

rem --- 3. Eigene Python-Umgebung anlegen, nur beim ersten Mal -----------
set "VENV=%~dp0_python_umgebung"
set "VPY=%VENV%\Scripts\python.exe"
if not exist "%VPY%" (
    echo Lege Python-Umgebung an ...
    %PY% -m venv "%VENV%"
    if errorlevel 1 goto :fehler
)

rem --- 4. Bibliotheken und Browser installieren, nur beim ersten Mal ----
if not exist "%VENV%\installiert.txt" (
    echo Installiere Bibliotheken. Das passiert nur einmal und dauert ein paar Minuten ...
    "%VPY%" -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 goto :fehler
    "%VPY%" -m playwright install chromium
    if errorlevel 1 goto :fehler
    echo ok> "%VENV%\installiert.txt"
)

rem --- 5. Auswahl ------------------------------------------------------
echo.
echo   1 = nur Raider.IO
echo   2 = Raider.IO + WoWProgress  [erweiterte Version]
echo.
choice /c 12 /n /m "Auswahl 1 oder 2: "
if errorlevel 2 (set "ARGS=--wowprogress") else (set "ARGS=")

rem --- 6. Skript starten -----------------------------------------------
echo.
"%VPY%" raiderio_recruitment_scraper.py %ARGS%
echo.
echo Fertig. Die CSV-Dateien liegen in diesem Ordner.
pause
exit /b 0

:fehler
echo.
echo Installation fehlgeschlagen. Bitte Internetverbindung pruefen und
echo diese Datei nochmal starten.
pause
exit /b 1
