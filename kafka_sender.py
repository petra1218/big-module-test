import json

from kafka import KafkaProducer

import logger_conf as logger

log = logger.log

_producers = {}

def get_producer(bootstrap_servers):
    if bootstrap_servers not in _producers:
        log.info("创建 KafkaProducer bootstrap_servers=%s", bootstrap_servers)
        _producers[bootstrap_servers] = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        )
    return _producers[bootstrap_servers]

def send_message(bootstrap_servers, topic, msg):
    producer = get_producer(bootstrap_servers)
    producer.send(topic, msg)
    producer.flush()
    log.info("已发送接图请求 topic=%s ID=%s url=%s", topic, msg.get("ID"), msg.get("SceneImageUrl"))
