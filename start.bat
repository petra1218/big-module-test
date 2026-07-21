@echo off
setlocal
cd /d "%~dp0"

rem Use a virtual environment (venv); dependencies are installed only into .venv
set VENV_DIR=.venv
if not exist "%VENV_DIR%\Scripts\activate.bat" (
  echo Creating virtual environment (.venv) ...
  python -m venv %VENV_DIR%
)
call "%VENV_DIR%\Scripts\activate.bat"

echo Installing dependencies into venv ...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Starting service at http://0.0.0.0:10086 ...
python -m uvicorn main:app --reload --host 0.0.0.0 --port 10086
