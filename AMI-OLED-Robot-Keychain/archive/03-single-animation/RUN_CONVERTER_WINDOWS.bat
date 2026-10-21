@echo off
setlocal EnableExtensions
cd /d "%~dp0converter"
if errorlevel 1 (
  echo ERROR: Could not locate the converter folder.
  pause
  exit /b 1
)

REM Prefer 'python' as many Windows installations do not include the 'py' launcher.
set "PY_CMD=python"
python -c "import sys; print(sys.version.split()[0])" >nul 2>&1
if not errorlevel 1 goto :found_python

REM Fallback: systems with the Windows Python launcher instead of python on PATH.
set "PY_CMD=py -3"
py -3 -c "import sys; print(sys.version.split()[0])" >nul 2>&1
if not errorlevel 1 goto :found_python

echo.
echo ERROR: Python was not found with either 'python' or 'py -3'.
echo Open PowerShell and try: python --version
echo If Python is installed, add it to PATH and reopen this window.
pause
exit /b 1

:found_python
echo Using Python command: %PY_CMD%
echo.
%PY_CMD% -c "import cv2, PIL, numpy" >nul 2>&1
if not errorlevel 1 goto :run_converter

echo Installing Python dependencies (only if needed)...
%PY_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERROR: Dependency installation failed.
  echo Try manually: %PY_CMD% -m pip install -r requirements.txt
  echo If pip is missing, try: %PY_CMD% -m ensurepip --upgrade
  pause
  exit /b 1
)

:run_converter
echo Starting ERINX MP4-to-OLED Converter...
%PY_CMD% converter.py
if errorlevel 1 (
  echo.
  echo The converter exited with an error.
  pause
  exit /b 1
)
endlocal
