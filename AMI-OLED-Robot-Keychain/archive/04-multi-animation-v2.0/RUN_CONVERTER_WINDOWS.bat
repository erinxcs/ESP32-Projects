@echo off
setlocal EnableExtensions
cd /d "%~dp0converter"
if errorlevel 1 (
  echo ERROR: Cannot locate converter folder.
  pause
  exit /b 1
)
set "PY_CMD=python"
python -c "import sys; print(sys.version.split()[0])" >nul 2>&1
if not errorlevel 1 goto :python_found
set "PY_CMD=py -3"
py -3 -c "import sys; print(sys.version.split()[0])" >nul 2>&1
if not errorlevel 1 goto :python_found
echo ERROR: Python missing. Try "python --version" in PowerShell.
pause
exit /b 1
:python_found
echo Using %PY_CMD%
%PY_CMD% -c "import cv2, PIL, numpy, tkinter" >nul 2>&1
if not errorlevel 1 goto :launch
echo Installing converter dependencies ...
%PY_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Use PowerShell in converter folder:
  echo python -m pip install -r requirements.txt
  pause
  exit /b 1
)
:launch
%PY_CMD% converter.py
if errorlevel 1 (
  echo Converter exited with error.
  pause
  exit /b 1
)
endlocal
