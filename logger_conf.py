"""统一日志：控制台 + service.log 文件 + 内存环形缓冲(供 /api/logs 读取)。

对接调试时，所有关键节点（登录 / MinIO 遍历 / Kafka 发送 / WS 连接接收 / 结果入库 / 超时）
都会打印带时间戳的日志；密钥与 token 已脱敏，仅保留前后几位用于核对身份。
"""
import collections
import logging

LOG_FILE = "service.log"
MAX_IN_MEMORY = 2000

log = logging.getLogger("verify")
log.setLevel(logging.DEBUG)
if not log.handlers:
    _fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    _ch = logging.StreamHandler()
    _ch.setFormatter(_fmt)
    log.addHandler(_ch)

    _fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _fh.setFormatter(_fmt)
    log.addHandler(_fh)

    _buffer = collections.deque(maxlen=MAX_IN_MEMORY)

    class _MemHandler(logging.Handler):
        def emit(self, record):
            try:
                _buffer.append(self.format(record))
            except Exception:
                pass

    _mem = _MemHandler()
    _mem.setFormatter(_fmt)
    log.addHandler(_mem)
    log._buffer = _buffer


def recent_logs(limit=200):
    buf = getattr(log, "_buffer", None)
    if buf is None:
        return []
    return list(buf)[-limit:]


def mask(s, show=4):
    """脱敏：仅保留前后 show 位，中间以 *** 替代。"""
    s = "" if s is None else str(s)
    if not s:
        return ""
    if len(s) <= show:
        return "***"
    if len(s) <= show * 2:
        return s[:show] + "***"
    return s[:show] + "***" + s[-show:]
