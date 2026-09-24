# 10 — Channels / Subagents / Automations

## Gateway 是这一章的中心

只要你需要：

- WebUI 长期在线；
- Feishu / WeChat 等 channel；
- cron；
- local trigger；
- heartbeat；
- Dream background job；

就应该先理解 `nanobot gateway`。

## Channel

current-source 支持多种 chat app。对你最有价值的实验优先：

### Feishu

current Feishu 使用 WebSocket long connection，可通过 QR login；不再默认要求旧教程里的“公网 Webhook + ngrok”。

```powershell
nanobot plugins enable feishu
nanobot channels login feishu
nanobot gateway
```

### WeChat

current `weixin` channel 使用 QR login + HTTP long-poll：

```powershell
nanobot plugins enable weixin
nanobot channels login weixin
```

## Pairing / allowFrom

不要为了方便直接：

```json
"allowFrom": ["*"]
```

对 DM-capable channel 优先学习 pairing。

## Subagent

Subagent 不是“另一个 HTTP 服务”，而是复用 `AgentRunner` 思路的后台 agent execution。

current 默认：

```text
agents.defaults.maxConcurrentSubagents = 4
```

超过 capacity 后等待。

实验：主 Agent 同时派两个 subagent：

```text
A：读论文方法
B：读论文实验
主 Agent：综合并引用
```

## Automations

### Scheduled

用户在目标 topic 里请求 schedule，Agent 用 cron tool 创建。

### Local trigger

```text
/trigger paper-index-updated
nanobot trigger <id> "New PDFs indexed; summarize changes"
```

适合 CI / 本地脚本 / webhook adapter。

### Heartbeat

编辑：

```text
<workspace>/HEARTBEAT.md
```

做“定期检查，但没有重要结果时保持安静”的任务。

## 本章验收

你必须能解释：

- Cron vs Trigger vs Heartbeat；
- Subagent concurrency vs inbound concurrency；
- Channel access control；
- 为什么 automation delivery 要绑定 session/topic。
