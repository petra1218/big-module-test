#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# 使用虚拟环境 (venv)，依赖仅安装在 .venv 中，不污染系统环境
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment (.venv) ..."
  python3 -m venv "$VENV_DIR"
fi
PY="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo "Installing dependencies into venv ..."
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt

echo "Starting service at http://0.0.0.0:10086 ..."
exec "$PY" -m uvicorn main:app --reload --host 0.0.0.0 --port 10086
