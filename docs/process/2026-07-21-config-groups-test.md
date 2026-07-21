# 2026-07-21 配置参数分组 + 各组测试连接按钮

## 背景
原左侧配置为扁平长表单，对接时难以快速定位某一系统（大模型服务 / WebSocket / Kafka / MinIO）的参数是否填写正确、服务是否可达。用户要求：按系统分组填写，并为每组提供「测试连接」按钮。

## 改动

### 前端 (static/app.js, static/index.html)
- 将扁平 `FIELDS` 重构为 `GROUPS` 分组结构：大模型服务、WebSocket、Kafka、MinIO、其他。
- `buildForm` 改为按分组渲染卡片（标题 + 右侧「测试连接」按钮 + 该组字段）。
- 新增 `testConn(type)`：收集当前表单 → `POST /api/test/<type>` → 在状态栏以绿/红字显示通过/失败及后端返回的 message/error。
- `loadServerConfig` / `collectForm` 改用 `ALL_FIELDS`（由 GROUPS 扁平化得到），保持与后端字段一致。
- `index.html` 新增 `.group / .group-head / .btn-test` 样式。

### 后端 (main.py)
新增 4 个分组测试接口，复用现有模块逻辑：
- `POST /api/test/llm`：调用 `auth.login` 验证 AK/SK 与登录接口可达（15s 超时）。
- `POST /api/test/minio`：调用 `minio_client.list_directory` 验证凭证与目录，返回文件数或空目录提示。
- `POST /api/test/kafka`：通过 `kafka_sender.get_producer` 后调用 `producer.bootstrap_connected()` 验证 broker 连通。
- `POST /api/test/ws`：先 `auth.login` 取 token，再 `websockets.connect` 连接 `ws_base/apiWs/stream/data`（8s 超时）验证 WS 通道。
- 统一先用 `set_runtime` 写入运行期配置，便于后续「开始验证」直接复用已测试的参数；失败信息记录日志。

## 验证
- `python -m py_compile main.py` 通过；`node -c static/app.js` 通过。
- 无遗留 `FIELDS` 裸常量引用。

## 回溯
- 提交后由 `start.bat` / `start.sh`（venv）启动，`http://<IP>:10086/`，在对应分组点「测试连接」即可单独排错。
