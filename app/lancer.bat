@echo off
title Division 2 — DPS Tracker
echo.
echo  Division 2 DPS Tracker
echo  ========================
echo.

:: ── Rechercher Python (systeme) ───────────────────────────────────────────
set APP_DIR=%~dp0
set PYEXE=

:: 1) Python dans le PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYEXE=python
    goto py_ok
)

:: 2) Emplacements courants
for %%P in (
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%LocalAppData%\Programs\Python\Python39\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
) do (
    if exist %%P (
        set PYEXE=%%~P
        goto py_ok
    )
)

echo [ERREUR] Python est introuvable.
echo Veuillez reinstaller Division 2 DPS Tracker.
pause
exit /b 1

:py_ok
echo  Python : %PYEXE%

:: ── Localiser Tesseract ──────────────────────────────────────────────────
set TESS_EXE=

tesseract --version >nul 2>&1
if not errorlevel 1 (
    set TESS_EXE=tesseract
    goto tess_ok
)

for %%P in (
    "%ProgramFiles%\Tesseract-OCR\tesseract.exe"
    "%ProgramFiles(x86)%\Tesseract-OCR\tesseract.exe"
    "%LocalAppData%\Programs\Tesseract-OCR\tesseract.exe"
    "%LocalAppData%\Tesseract-OCR\tesseract.exe"
    "C:\Tesseract-OCR\tesseract.exe"
) do (
    if exist %%P (
        set TESS_EXE=%%~P
        goto tess_found
    )
)

for /f "tokens=2*" %%A in (
    'reg query "HKLM\SOFTWARE\Tesseract-OCR" /v "InstallDir" 2^>nul'
) do (
    if exist "%%B\tesseract.exe" (
        set TESS_EXE=%%B\tesseract.exe
        goto tess_found
    )
)
for /f "tokens=2*" %%A in (
    'reg query "HKCU\SOFTWARE\Tesseract-OCR" /v "InstallDir" 2^>nul'
) do (
    if exist "%%B\tesseract.exe" (
        set TESS_EXE=%%B\tesseract.exe
        goto tess_found
    )
)

echo.
echo [ATTENTION] Tesseract OCR n'est pas detecte.
echo  Relancez l'installeur Division 2 DPS Tracker.
echo.
pause
exit /b 1

:tess_found
for %%F in ("%TESS_EXE%") do set PATH=%%~dpF;%PATH%
echo  Tesseract : %TESS_EXE%

:tess_ok
set TESSERACT_CMD=%TESS_EXE%

echo.
echo  Lancement du tracker...
echo  Ouverture dans votre navigateur : http://localhost:7842
echo  (Fermez cette fenetre pour arreter le tracker)
echo.

cd /d "%APP_DIR%"
"%PYEXE%" server.py
pause
