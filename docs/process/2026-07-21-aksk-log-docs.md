# 2026-07-21 修改记录：AK/SK 界面输入 / 调试日志 / docs 追溯

## 背景
对接"四川警察学院大模型服务"时，用户提出三点改进：让登录大模型服务使用的 AK/SK 在界面上输入；增加输出日志便于对接调试判断错误；建立 `docs` 目录，把每次修改同步输出为 md 文件做追溯。

## 1. 大模型服务登录 AK/SK 在界面输入
- 平台登录使用的 AppKey / AppSecret 即为登录大模型服务的 AK/SK，原本已在左侧配置区，本次将字段标签明确为「大模型服务 AppKey (AK)」「大模型服务 AppSecret (SK)」，强调其用途。
- 字段名 `app_key` / `app_secret` 不变，后端 `auth.login(app_key, app_secret, api_base)` 流程不变。
- 登录日志会脱敏打印当前使用的 AK（前 4 后 4），便于对接时核对身份。

## 2. 增加调试输出日志
- 新增 `logger_conf.py`：统一日志，输出到控制台 + `service.log` 文件（已被 `.gitignore` 忽略）+ 内存环形缓冲（最近 2000 条）。
- 在登录、MinIO 遍历、Kafka 发送、WebSocket 连接/接收/重连、结果入库/超时等关键节点补充日志；对 `app_secret` / `minio_secret_key` / `app_key` / token 做脱敏（仅保留前后几位）。
- 新增接口 `GET /api/logs?limit=200`，前端「调试日志」按钮打开底部面板，每 2 秒自动刷新展示实时日志。

## 3. 新增 docs 目录追溯每次修改
- 新建 `docs/process/INDEX.md` 作为修改追踪索引。
- 本文件即本次修改记录，纳入版本控制；后续每次修改同步追加并更新索引。

## 涉及文件
- 新增：`logger_conf.py`、`docs/process/INDEX.md`、`docs/process/2026-07-21-aksk-log-docs.md`
- 修改：`config.py`、`auth.py`、`minio_client.py`、`kafka_sender.py`、`ws_receiver.py`、`store.py`、`main.py`（重建，原提交内容为空）、`static/index.html`、`static/app.js`、`README.md`

## 验证
- 后端 `python -m py_compile` 各模块通过。
- 启动后访问 `/api/logs` 可见启动与配置日志；点击「调试日志」面板可查看实时日志与错误堆栈。
