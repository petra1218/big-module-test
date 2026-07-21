import time

import logger_conf as logger

log = logger.log

# ID -> 记录；进程存活期间保留，跨多次验证运行不丢失
items = {}
running = False
last_error = None

def reset():
    global items, running, last_error
    items = {}
    running = False
    last_error = None
    log.info("结果存储已重置")

def register(id, filename, minio_url):
    items[id] = {
        "id": id,
        "filename": filename,
        "minio_url": minio_url,
        "status": "已发送",
        "sent_at": time.time(),
        "stream": [],
        "alarms": [],
        "last_update": time.time(),
    }

def ingest(kind, key, data):
    rec = items.get(key)
    if rec is None:
        rec = {
            "id": key,
            "filename": None,
            "minio_url": None,
            "status": "已发送",
            "sent_at": time.time(),
            "stream": [],
            "alarms": [],
            "last_update": time.time(),
        }
        items[key] = rec
        log.warning("收到未登记ID的%s消息 key=%s (可能ID未回显)", kind, key)
    rec["last_update"] = time.time()
    if kind == "stream":
        rec["stream"].append(data)
        if rec["status"] == "已发送":
            rec["status"] = "已完成"
        log.debug("流水消息 key=%s themeLabel=%s", key, data.get("themeLabel"))
    elif kind == "alarm":
        rec["alarms"].append(data)
        rec["status"] = "有预警"
        log.debug("预警消息 key=%s themeLabel=%s level=%s", key, data.get("themeLabel"), data.get("alarmLevel"))

def snapshot(timeout_seconds):
    now = time.time()
    out = []
    for rec in items.values():
        r = dict(rec)
        if r["status"] == "已发送" and (now - r["sent_at"]) > timeout_seconds:
            r["status"] = "超时"
            log.warning("图片超时未回结果 id=%s file=%s", r["id"], r["filename"])
        r["stream_count"] = len(r["stream"])
        r["alarm_count"] = len(r["alarms"])
        out.append(r)
    return out
