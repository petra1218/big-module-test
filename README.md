# 模型识别验证服务

用来验证"四川警察学院大模型服务"识别能力的内部工具型服务。把一批图片送进模型、拿回识别结果（流水 + 预警），在原图上画检测框并并列展示，由人工判断模型靠不靠谱。

## 运行环境

- Ubuntu + Python 3.13.5
- FastAPI 服务，监听 `0.0.0.0:10086`

## 启动

```bash
chmod +x start.sh
./start.sh
```

脚本会自动检测并安装 `requirements.txt` 中的依赖，并以 `--reload` 调试模式启动。

## 使用流程

1. 浏览器打开 `http://<本机IP>:10086/`。
2. 在左侧配置区填写（运行期内驻留内存，刷新不丢；也记忆在浏览器 localStorage）：
   - 大模型服务登录（AK/SK）：`app_key` / `app_secret`（即登录大模型服务使用的 AK/SK）
   - 平台地址：`api_base`（如 `http://ip:port`）、`ws_base`（如 `ws://ip:port`）
   - MinIO：`endpoint` / `access_key` / `secret_key` / `bucket` / `secure`（用于遍历目录）
   - MinIO 公开基址：`minio_public_base_url`（模型可直连，拼成 `SceneImageUrl`）
   - 目录名：`directory`
   - `kafka_bootstrap_servers`、`concurrency`、`timeout_seconds`
3. 点击「开始验证」：服务登录拿 token → 遍历 MinIO 目录 → 为每张图生成 32 位关联 ID → 通过 Kafka 发送到接图 topic（并发上限内）→ 两条 WebSocket（流水 / 预警）持续接收结果。
4. 右侧结果区：左图为原图，右图按预警 `alarmBoxs` 绝对像素坐标画框并标注 `tag/conf`；下方分两栏展示流水信息与预警信息。左侧图片列表可点击切换，状态徽标：已发送 / 已完成 / 有预警 / 超时。

## 数据流

Kafka 发（`Q_VEHICLE_FRONT_FACE_SHARE_TO_XQ`，无需 SASL）→ WebSocket 收（`/apiWs/stream/data` 流水、`/apiWs/alarm/data` 预警，Bearer 鉴权）。关联键：请求里的 `ID` 回显到 `kafkaReceiveImageId`，`Expand` 兜底回显到 `kafkaReceiveExpand`，双字段 join。

## 调试日志

为方便对接调试时判断错误，服务输出统一日志：

- 控制台实时打印，同时写入 `service.log`（已被 `.gitignore` 忽略）。
- 关键节点（登录 / MinIO 遍历 / Kafka 发送 / WebSocket 连接接收重连 / 结果入库超时）均有记录，`app_secret` / `minio_secret_key` / `app_key` / token 已脱敏（仅保留前后几位）。
- 前端右上角「调试日志」按钮打开底部面板，实时展示最近 200 条日志（每 2 秒自动刷新），也可直接访问 `GET /api/logs?limit=200`。

## 修改追溯

每次代码修改的执行内容与结果记录在 `docs/process/` 目录，并在 `docs/process/INDEX.md` 汇总索引，便于追溯。

## 说明

- 不做自动准确率统计（无真值），仅可视化辅助人工判断。
- 内部系统：凭证由前端填写并驻留内存，密钥不上配置文件。
- 后端不转发图片，浏览器直连 MinIO 公开地址。
- WS 推送兼容 Base64(JSON) 与纯 JSON 两种格式。
