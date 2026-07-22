import os
import yaml

import logger_conf as logger

log = logger.log

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

DEFAULTS = {
    "host": "0.0.0.0",
    "port": 10086,
    "kafka_bootstrap_servers": "127.0.0.1:9092",
    "topic_receive_image": "Q_VEHICLE_FRONT_FACE_SHARE_TO_XQ",
    "device_id": "verify-device-001",
    "device_name": "验证设备",
    "concurrency": 5,
    "submit_mode": "concurrent",
    "seq_interval_seconds": 1,
    "timeout_seconds": 300,
    "token_refresh_interval": 1800,
}

def load_defaults():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        DEFAULTS.update(data)
        log.info("已加载 config.yaml 默认值")
    except FileNotFoundError:
        log.info("未找到 config.yaml, 使用内置默认值")
    except Exception as e:
        log.warning("读取 config.yaml 失败: %s", e)

load_defaults()

# 运行期由前端提交、驻留内存（进程存活期间不重复填写）
runtime_config = {}

def set_runtime(cfg):
    global runtime_config
    runtime_config = dict(cfg or {})
    log.info("已更新运行期配置 字段数=%d", len(runtime_config))

def current_cfg():
    return {**DEFAULTS, **runtime_config}
