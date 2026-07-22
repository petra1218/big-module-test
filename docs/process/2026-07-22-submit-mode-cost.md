# 2026-07-22 并发/顺序可切换提交 + 识别耗时展示

## 背景
用户要求：(1) 提交图片验证支持「并发」与「顺序提交」两种可切换方式；(2) 分别支持设置并发数和顺序提交间隔（秒）；(3) 每张图片记录发送时间与收到流水的时间，在识别结果区展示识别耗时。

## 改动

### 配置 (config.py)
- `DEFAULTS` 新增 `submit_mode="concurrent"`、`seq_interval_seconds=1`。

### 后端 (main.py)
- `/api/start` 读取 `submit_mode` / `concurrency` / `seq_interval_seconds`：
  - 并发模式：`asyncio.Semaphore(concurrency)` 并发发送，逻辑同前。
  - 顺序模式：逐张 `await send_one` 后 `await asyncio.sleep(seq_interval_seconds)`。
- `send_one` 发送成功后调用 `store.mark_sent(rid)` 记录实际发送时间。

### 数据层 (store.py)
- `register`：初始状态改为「待发送」，新增 `send_time` / `stream_time` 字段。
- 新增 `mark_sent(id)`：发送成功时写入 `send_time`，状态 待发送→已发送。
- `ingest`：流水首次到达时写入 `stream_time`。
- `snapshot`：计算 `cost_ms = (stream_time - (send_time 或 sent_at)) * 1000`，并给出 `cost_text`（如 `1234 ms`）；超时判定仅在状态为「已发送」且超过 `timeout_seconds` 时触发（避免顺序提交尚未轮到的图片被误判超时）。

### 前端 (static/app.js, static/index.html)
- 「其他」分组新增字段：`submit_mode`（下拉：并发 / 顺序提交）、`concurrency`（并发数）、`seq_interval_seconds`（顺序提交间隔秒）。
- `buildForm` 支持 `select` 类型（第四个元素为选项数组）。
- 图片列表项与识别结果详情均展示「识别耗时」；状态徽标新增「待发送」。
- `index.html` 增加 `.b-pending`、`.cost` 样式。

## 验证
- `python -m py_compile main.py store.py config.py` 通过；`node -c static/app.js` 通过；无 lint 错误。
