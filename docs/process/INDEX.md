# 修改追溯索引 (docs/process)

> 本目录记录每次代码修改的执行内容与结果，便于对接与排错时追溯。
> 每次改动提交到 `main` 时，同步追加一条记录并更新本索引。

## 索引

| 日期 | 记录文件 | 说明 |
|------|----------|------|
| 2026-07-21 | [2026-07-21-aksk-log-docs.md](2026-07-21-aksk-log-docs.md) | 大模型服务 AK/SK 界面输入、增加调试日志、建立 docs 追溯 |
| 2026-07-21 | [2026-07-21-venv-startup.md](2026-07-21-venv-startup.md) | 新增 Windows 启动脚本、Linux/Windows 均改用 venv |
| 2026-07-21 | [2026-07-21-config-groups-test.md](2026-07-21-config-groups-test.md) | 配置按系统分组，每组增加测试连接按钮 + 4 个测试接口 |
| 2026-07-21 | [2026-07-21-layout-no-scroll.md](2026-07-21-layout-no-scroll.md) | 页面三栏各自内部滚动，去掉总体滚动条 |
| 2026-07-22 | [2026-07-22-submit-mode-cost.md](2026-07-22-submit-mode-cost.md) | 并发/顺序可切换提交、并发数与间隔设置、识别耗时展示 |
| 2026-07-22 | [2026-07-22-decouple-login-from-send.md](2026-07-22-decouple-login-from-send.md) | 解耦登录与发送：发图片仅依赖 Kafka，登录仅用于 WS 取结果 |
