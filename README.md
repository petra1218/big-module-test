# 模型识别验证服务

用来验证"四川警察学院大模型服务"识别能力的内部工具型服务。把一批图片送进模型、拿回识别结果（流水 + 预警），在原图上画检测框并并列展示，由人工判断模型靠不靠谱。

## 运行环境

- Ubuntu + Python 3.13.5
- FastAPI 服务，监听 `0.0.0.0:10086`

## 启动

启动脚本会在首次运行时自动创建隔离的 Python 虚拟环境（`.venv`，已被 `.gitignore` 忽略），并在其中安装 `requirements.txt` 中的依赖，再以 `--reload` 调试模式启动服务。两个系统下的启动与依赖安装均使用 venv，不污染系统环境。

- Linux / Ubuntu：
  ```bash
  chmod +x start.sh
  ./start.sh
  ```
- Windows：在资源管理器双击 `start.bat`，或在 cmd / PowerShell 中执行：
  ```bat
  start.bat
  ```

启动后浏览器打开 `http://<本机IP>:10086/`。

## 使用流程

1. 浏览器打开 `http://<本机IP>:10086/`。
2. 在左侧配置区按系统分组填写（运行期内驻留内存，刷新不丢；也记忆在浏览器 localStorage）：
   - **Kafka（发送图片到大模型）**：`kafka_bootstrap_servers`、`topic_receive_image`。发送图片只需 Kafka，无需登录。
   - **MinIO（图片源）**：`endpoint` / `access_key` / `secret_key` / `bucket` / `secure` / `minio_public_base_url` / `directory`
   - **结果接收（WebSocket，需登录鉴权）**：`ws_base`、`app_key` / `app_secret`（AK/SK）、`api_base`（取 token 的鉴权地址）。登录仅用于 WebSocket 带 token 取回结果，与图片发送无关。
   - **其他**：`submit_mode`（并发 / 顺序提交，可切换）、`concurrency`（并发数，仅并发方式生效）、`seq_interval_seconds`（顺序提交间隔，单位秒）、`device_id` / `device_name` / `timeout_seconds`
   - 每组（Kafka / MinIO / 结果接收）右侧均有「测试连接」按钮，可单独验证该系统可达性与凭证是否正确，再正式「开始验证」。
3. 点击「开始验证」：遍历 MinIO 目录 → 为每张图生成 32 位关联 ID → 若配置了登录/WS 则先登录取 token 并启动两条 WebSocket（流水 / 预警）接收结果 → 通过 Kafka 发送接图请求（并发上限内 / 或顺序间隔）到接图 topic。登录失败仅导致收不到结果，不影响图片经 Kafka 发送。
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
