@echo off
:: install_deps.bat — appelé par l'installeur Inno Setup
:: Installe les dépendances Python pour Division 2 DPS Tracker
:: Ce script tourne en SILENT pendant l'installation

set PYEXE=%1
if "%PYEXE%"=="" set PYEXE=python

echo Mise a jour de pip...
"%PYEXE%" -m pip install --upgrade pip --quiet --no-warn-script-location

echo Installation des dependances...
"%PYEXE%" -m pip install flask pillow pytesseract numpy opencv-python mss --quiet --no-warn-script-location

echo Dependances installes avec succes.
exit /b 0
