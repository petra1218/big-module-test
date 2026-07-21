import time

# ID -> 记录；进程存活期间保留，跨多次验证运行不丢失
items = {}
running = False
last_error = None

def reset():
    global items, running, last_error
    items = {}
    running = False
    last_error = None

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
    rec["last_update"] = time.time()
    if kind == "stream":
        rec["stream"].append(data)
        if rec["status"] == "已发送":
            rec["status"] = "已完成"
    elif kind == "alarm":
        rec["alarms"].append(data)
        rec["status"] = "有预警"

def snapshot(timeout_seconds):
    now = time.time()
    out = []
    for rec in items.values():
        r = dict(rec)
        if r["status"] == "已发送" and (now - r["sent_at"]) > timeout_seconds:
            r["status"] = "超时"
        r["stream_count"] = len(r["stream"])
        r["alarm_count"] = len(r["alarms"])
        out.append(r)
    return out
