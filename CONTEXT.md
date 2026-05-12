# 项目交接上下文 — 粘贴到 Claude Code 对话开头

---

## 项目是什么

这是一个**飞书报警推送服务**，运行在 Windows 机器上。

数据流向：
```
车间 VBS 脚本（SCADA 触发）
    ↓  HTTP POST /receive_data (5000端口)
alarm_service.py (Flask + 飞书 WebSocket)
    ↓  去重 / 屏蔽 / 连续报警判断
飞书群 (推送交互卡片)
    ↓  用户点击卡片按钮
alarm_service.py (飞书 WebSocket 长连接接收回调)
    ↓
飞书多维表格 (记录处理结果)
```

**运行入口**：`alarm_service.py`（双击 `run.bat` 启动，或在 PyCharm 里直接运行）

---

## 代码里的关键配置（alarm_service.py 顶部）

| 变量 | 说明 |
|------|------|
| `APP_ID` / `APP_SECRET` | 飞书应用凭证 |
| `VERIFICATION_TOKEN` | 飞书事件订阅验证 Token |
| `RECEIVE_ID` | 接收报警卡片的群 chat_id |
| `SUPPRESS_RECEIVE_ID` | 接收屏蔽提示卡片的群 chat_id（有领导的群）|
| `BITABLE_APP_TOKEN` | 飞书多维表格 App Token |
| `ALARM_TABLE_ID` | 故障报警记录表 Table ID |
| `SUPPRESS_TABLE_ID` | 屏蔽记录表 Table ID |
| `DUPLICATE_THRESHOLD` | 防重复时间窗口（秒），默认 600 秒 |
| `SUPPRESS_TIMEOUT_MINUTES` | 屏蔽提示超时分钟数，默认 10 分钟 |

---

## 核心功能说明

### 1. 防重复推送
同一设备同一故障在 `DUPLICATE_THRESHOLD` 秒内只推送一次，超出后自动重置。

### 2. 屏蔽功能
用户点击"屏蔽 24 小时"后，该故障 24 小时内不再推送。屏蔽记录存入 `suppression.json` 和飞书多维表格。

### 3. 连续报警提示
同一故障当日超过阈值次数时，推送屏蔽提示卡片，由人工决定是否屏蔽。

### 4. 故障闭环卡片
用户点击报警卡片填写处理记录（处理人/状态/原因/措施），提交后写入多维表格并更新卡片为"已记录"。

### 5. 每日日报
每天 08:30 自动推送前日故障汇总报告。

---

## 常见问题排查

### 报警收到但卡片发不出去

在本机 cmd 执行：
```cmd
curl -X POST http://localhost:5000/receive_data -H "Content-Type: application/json" -d "{\"LinearBody\":\"P1\",\"Device\":\"压机\",\"Problem\":\"测试\",\"alarm_time\":\"2026-01-01 10:00:00\"}"
```

查看 `alarm_service.log` 里的错误码：

| 错误码 | 原因 | 解决方法 |
|--------|------|---------|
| `99991663` | 模板 ID 不存在或版本号错误 | 确认 `TEMPLATE_ID` 和 `TEMPLATE_VERSION` |
| `99991400` | 机器人没有群权限 | 飞书后台把机器人加入目标群 |
| `99991461` | chat_id 无效 | 重新获取群 chat_id |
| `91403` | Bitable app token 错误 | 核对 `BITABLE_APP_TOKEN` |

### VBS 发送失败

1. 确认 VBS 里的 URL 是 `http://{本机IP}:5000/receive_data`，用真实 IP 而非 `127.0.0.1`（跨机器时）
2. 确认防火墙放行了 5000 端口：
```cmd
netsh advfirewall firewall add rule name="Flask-5000" dir=in action=allow protocol=TCP localport=5000
```
3. 从 VBS 那台机器验证网络：
```powershell
Test-NetConnection {本机IP} -Port 5000
```

### 屏蔽按钮点击无响应

屏蔽功能使用内存 cache 存储元数据（key: 8位UUID），服务重启后 cache 清空，已推送的屏蔽提示卡片会失效，点击会提示"操作已失效"，属正常现象，重新触发报警即可。

---

## 注意事项

- **同一 APP_ID 只能一台机器运行**，旧机器服务必须停掉，否则 WebSocket 事件随机分发
- `lark-oapi` 必须使用 **1.5.3 版本**，不能升级
- 日志写入 `alarm_service.log`，按天轮转，保留 30 天
- `suppression.json` 存屏蔽记录，`statistics.json` 存推送统计，重启后自动恢复

---

## 文件清单

```
alarm_service.py        主程序
main.py                 飞书卡片交互处理（complete_alarm 分支）
test_suppression.py     屏蔽功能测试脚本（需与 alarm_service.py 同机运行）
requirements.txt        依赖清单
run.bat                 双击启动服务
CONTEXT.md              本文件
部署注意事项.md          环境部署说明
需求文档_v2_snap7.md    下一阶段开发需求文档
```

---

## 环境安装

```
pip install -r requirements.txt
```
