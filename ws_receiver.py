import asyncio
import base64
import json

import websockets

import logger_conf as logger

log = logger.log

import auth
import store

def decode_payload(raw):
    """WS 推送可能是 Base64(JSON) 或纯 JSON，两种都兼容。"""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        decoded = base64.b64decode(raw, validate=True)
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        try:
            return json.loads(raw)
        except Exception:
            return None

def extract_key(msg):
    if not isinstance(msg, dict):
        return None
    return msg.get("kafkaReceiveImageId") or msg.get("kafkaReceiveExpand")

async def ws_loop(uri, kind):
    """持续接收指定通道；token 过期/断线时按当前 token 重连。"""
    log.info("WS 接收协程启动 kind=%s uri=%s", kind, uri)
    while store.running:
        token = auth.get_token()
        if not token:
            await asyncio.sleep(2)
            continue
        try:
            async with websockets.connect(
                uri,
                additional_headers={"Sec-WebSocket-Protocol": f"Bearer {token}"},
            ) as ws:
                log.info("WS 已连接 kind=%s", kind)
                while store.running:
                    raw = await ws.recv()
                    data = decode_payload(raw)
                    if not data:
                        log.warning("WS 收到无法解析的消息 kind=%s", kind)
                        continue
                    key = extract_key(data)
                    if key:
                        store.ingest(kind, key, data)
                    else:
                        log.warning("WS 消息缺少关联字段已忽略 kind=%s", kind)
        except asyncio.CancelledError:
            log.info("WS 协程被取消 kind=%s", kind)
            raise
        except Exception as e:
            if store.running:
                log.warning("WS 断开 kind=%s 原因=%s 3秒后重连", kind, e)
                await asyncio.sleep(3)
    log.info("WS 接收协程退出 kind=%s", kind)
