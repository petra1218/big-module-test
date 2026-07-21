import asyncio
import base64
import json

import websockets

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
                while store.running:
                    raw = await ws.recv()
                    data = decode_payload(raw)
                    if not data:
                        continue
                    key = extract_key(data)
                    if key:
                        store.ingest(kind, key, data)
        except asyncio.CancelledError:
            raise
        except Exception:
            if store.running:
                await asyncio.sleep(3)
