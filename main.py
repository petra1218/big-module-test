import asyncio
import json
import uuid
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

import logger_conf as logger
from config import current_cfg, set_runtime, DEFAULTS
import auth
import minio_client
import kafka_sender
import ws_receiver
import store

log = logger.log

app = FastAPI(title="模型识别验证服务")
app.mount("/static", StaticFiles(directory="static"), name="static")

_ws_tasks = []

def _to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "y")

def _mask_cfg(cfg):
    m = dict(cfg)
    for k in ("app_secret", "minio_secret_key"):
        if m.get(k):
            m[k] = logger.mask(m[k])
    if m.get("app_key"):
        m["app_key"] = logger.mask(m["app_key"])
    return m

@app.get("/")
async def index():
    return FileResponse("static/index.html")

@app.get("/api/config")
async def get_config():
    return current_cfg()

@app.post("/api/start")
async def start_verify(req: dict):
    set_runtime(req)
    cfg = current_cfg()
    log.info("收到开始验证请求 配置(已脱敏)=%s", _mask_cfg(cfg))

    required = [
        "app_key", "app_secret", "api_base", "ws_base",
        "minio_endpoint", "minio_access_key", "minio_secret_key",
        "minio_bucket", "minio_public_base_url", "directory",
        "kafka_bootstrap_servers",
    ]
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        msg = "缺少必填配置: " + ", ".join(missing)
        log.error(msg)
        return JSONResponse({"ok": False, "error": msg})

    # 1) 登录大模型服务平台
    try:
        await auth.login(cfg["app_key"], cfg["app_secret"], cfg["api_base"])
    except Exception as e:
        log.error("登录失败, 终止启动: %s", e)
        return JSONResponse({"ok": False, "error": f"登录失败: {e}"})

    # 2) 遍历 MinIO 目录
    try:
        names = minio_client.list_directory(
            cfg["minio_endpoint"], cfg["minio_access_key"], cfg["minio_secret_key"],
            cfg["minio_bucket"], _to_bool(cfg.get("minio_secure")), cfg["directory"])
    except Exception as e:
        log.error("MinIO 遍历失败, 终止启动: %s", e)
        return JSONResponse({"ok": False, "error": f"MinIO 遍历失败: {e}"})

    if not names:
        log.warning("目录 %s 下未列出任何文件", cfg["directory"])
        return JSONResponse({"ok": False, "error": f"目录 {cfg['directory']} 下未找到文件"})

    # 3) 生成关联 ID 与 MinIO 公网 URL
    base = cfg["minio_public_base_url"].rstrip("/")
    directory = cfg["directory"].strip("/")
    topic = cfg.get("topic_receive_image") or DEFAULTS["topic_receive_image"]
    bs = cfg["kafka_bootstrap_servers"]
    concurrency = int(cfg.get("concurrency") or DEFAULTS["concurrency"])
    device_id = cfg.get("device_id") or DEFAULTS["device_id"]
    device_name = cfg.get("device_name") or DEFAULTS["device_name"]

    store.reset()
    store.running = True
    for name in names:
        rid = uuid.uuid4().hex
        url = f"{base}/{directory}/{name}"
        store.register(rid, name, url)

    # 4) 并发发送接图请求
    sem = asyncio.Semaphore(max(1, concurrency))

    async def send_one(rid, name, url):
        async with sem:
            msg = {
                "ID": rid,
                "DeviceID": device_id,
                "DeviceName": device_name,
                "SceneImageUrl": url,
                "CatTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Expand": json.dumps({"filename": name}, ensure_ascii=False),
            }
            try:
                await asyncio.to_thread(kafka_sender.send_message, bs, topic, msg)
            except Exception as e:
                log.error("接图请求发送失败 id=%s file=%s: %s", rid, name, e)

    send_tasks = [
        asyncio.create_task(send_one(r["id"], r["filename"], r["minio_url"]))
        for r in store.items.values()
    ]
    log.info("已并发发起 %d 张图片的接图请求 (并发上限=%d, topic=%s)",
             len(send_tasks), concurrency, topic)

    # 5) 启动 WS 接收协程（流水 + 预警）
    ws_base = cfg["ws_base"].rstrip("/")
    stream_uri = f"{ws_base}/apiWs/stream/data"
    alarm_uri = f"{ws_base}/apiWs/alarm/data"
    for t in _ws_tasks:
        t.cancel()
    _ws_tasks.clear()
    _ws_tasks.append(asyncio.create_task(ws_receiver.ws_loop(stream_uri, "stream")))
    _ws_tasks.append(asyncio.create_task(ws_receiver.ws_loop(alarm_uri, "alarm")))
    log.info("WS 接收协程已启动")

    async def _await_send():
        await asyncio.gather(*send_tasks, return_exceptions=True)
        log.info("全部接图请求已发送完毕")

    asyncio.create_task(_await_send())

    return {"ok": True, "count": len(send_tasks)}

@app.post("/api/stop")
async def stop_verify():
    log.info("收到停止请求")
    store.running = False
    for t in _ws_tasks:
        t.cancel()
    _ws_tasks.clear()
    try:
        await auth.logout()
    except Exception as e:
        log.warning("退出登录异常: %s", e)
    return {"ok": True}

@app.get("/api/results")
async def results():
    timeout = int(current_cfg().get("timeout_seconds") or DEFAULTS["timeout_seconds"])
    return {"items": store.snapshot(timeout)}

@app.get("/api/logs")
async def logs(limit: int = 200):
    """返回最近日志，便于对接调试时在前端判断错误。"""
    return {"logs": logger.recent_logs(limit)}

if __name__ == "__main__":
    uvicorn.run(app, host=DEFAULTS["host"], port=int(DEFAULTS["port"]))
