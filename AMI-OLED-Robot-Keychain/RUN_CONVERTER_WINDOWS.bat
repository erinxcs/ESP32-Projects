@echo off
setlocal EnableExtensions
cd /d "%~dp0tools\mp4_to_oled"
if errorlevel 1 (echo Cannot find tools\mp4_to_oled & pause & exit /b 1)
set "PY=python"
python --version >nul 2>&1
if errorlevel 1 (
  py -3 --version >nul 2>&1
  if errorlevel 1 (echo Python 3.10 or newer is required. & pause & exit /b 1)
  set "PY=py -3"
)
%PY% -c "import cv2, PIL, numpy" >nul 2>&1
if errorlevel 1 (
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (echo Dependency installation failed. & pause & exit /b 1)
)
%PY% converter.py
if errorlevel 1 (echo Converter exited with an error. & pause & exit /b 1)
endlocal
