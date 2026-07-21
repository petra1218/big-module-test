#!/usr/bin/env bash
set -e

PY=python3.13
$PY --version

# 自动检测：缺库则安装
$PY -c "import fastapi, uvicorn, kafka, websockets, minio, httpx, yaml" 2>/dev/null \
  || $PY -m pip install -r requirements.txt

# 调试启动，监听 0.0.0.0:10086
exec $PY -m uvicorn main:app --reload --host 0.0.0.0 --port 10086
