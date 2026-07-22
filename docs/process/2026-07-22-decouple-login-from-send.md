# 2026-07-22 解耦登录与发送：发图片仅依赖 Kafka，登录仅用于 WS 取结果

## 背景
用户指出对接逻辑：发送图片到大模型只需 Kafka，不需要登录；登录（AK/SK）仅用于 WebSocket 带 token 取回结果。原代码将 `app_key/app_secret/api_base` 归入「大模型服务」组，并在 `/api/start` 发送前强制登录（失败即终止整轮），概念与流程均有误。

## 改动

### 后端 (main.py)
- `/api/start` 必填校验去掉 `app_key/app_secret/api_base/ws_base`，仅保留发送图片所需的 `kafka_bootstrap_servers` 与 MinIO 源参数。
- 去掉发送前的强制登录；改为：遍历 MinIO → 生成 ID 并登记 → 若配置了 `ws_base + app_key + app_secret + api_base` 则登录取 token 并启动 WS 接收协程（登录失败仅告警，不阻断发送）→ 再经 Kafka 发送图片。
- 删除独立的 `POST /api/test/llm`（登录测试），由 `POST /api/test/ws`（登录 + 连接）覆盖。

### 前端 (static/app.js)
- 重新分组：
  - **Kafka（发送图片到大模型）**：`kafka_bootstrap_servers`、`topic_receive_image`（测试：kafka）
  - **MinIO（图片源）**：minio 全部字段（测试：minio）
  - **结果接收（WebSocket，需登录鉴权）**：`ws_base`、`app_key`、`app_secret`、`api_base`（测试：ws）
  - **其他**：`submit_mode`、`concurrency`、`seq_interval_seconds`、`device_id`、`device_name`、`timeout_seconds`
- 移除原「大模型服务」组与 `llm` 测试。

### 文档
- README 配置分组与使用流程同步更新：明确「发图片只需 Kafka、登录仅用于 WS」。

## 验证
- `python -m py_compile main.py` 通过；`node -c static/app.js` 通过；无 lint 错误。
