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
        "status": "待发送",
        "sent_at": time.time(),
        "send_time": None,
        "stream_time": None,
        "stream": [],
        "alarms": [],
        "last_update": time.time(),
    }

def mark_sent(id):
    """Kafka 发送成功后标记发送时间，状态由待发送->已发送。"""
    rec = items.get(id)
    if rec is None:
        return
    rec["send_time"] = time.time()
    if rec["status"] == "待发送":
        rec["status"] = "已发送"
    log.debug("已记录发送时间 id=%s", id)

def ingest(kind, key, data):
    rec = items.get(key)
    if rec is None:
        rec = {
            "id": key,
            "filename": None,
            "minio_url": None,
            "status": "待发送",
            "sent_at": time.time(),
            "send_time": None,
            "stream_time": None,
            "stream": [],
            "alarms": [],
            "last_update": time.time(),
        }
        items[key] = rec
        log.warning("收到未登记ID的%s消息 key=%s (可能ID未回显)", kind, key)
    rec["last_update"] = time.time()
    if kind == "stream":
        rec["stream"].append(data)
        if rec.get("stream_time") is None:
            rec["stream_time"] = time.time()
        if rec["status"] in ("待发送", "已发送"):
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
        # 识别耗时 = 收到流水时间 - 实际发送时间（无发送时间则用登记时间兜底）
        if r.get("stream_time") and (r.get("send_time") or r.get("sent_at")):
            base = r.get("send_time") or r["sent_at"]
            r["cost_ms"] = round((r["stream_time"] - base) * 1000)
        else:
            r["cost_ms"] = None
        r["cost_text"] = f'{r["cost_ms"]} ms' if r.get("cost_ms") is not None else "-"
        out.append(r)
    return out
