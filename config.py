import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

DEFAULTS = {
    "host": "0.0.0.0",
    "port": 10086,
    "kafka_bootstrap_servers": "127.0.0.1:9092",
    "topic_receive_image": "Q_VEHICLE_FRONT_FACE_SHARE_TO_XQ",
    "device_id": "verify-device-001",
    "device_name": "验证设备",
    "concurrency": 5,
    "timeout_seconds": 300,
    "token_refresh_interval": 1800,
}

def load_defaults():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        DEFAULTS.update(data)
    except FileNotFoundError:
        pass

load_defaults()

# 运行期由前端提交、驻留内存（进程存活期间不重复填写）
runtime_config = {}

def current_cfg():
    return {**DEFAULTS, **runtime_config}
