# 03 — Runtime Architecture Deep Dive

## 一条最重要的线

```text
InboundMessage
→ AgentLoop
→ AgentRunner
→ Provider / Tools
→ AgentRunner
→ AgentLoop
→ OutboundMessage
```

## AgentLoop vs AgentRunner

### AgentLoop

面向“一次用户 turn”的产品层责任：

- 接收 inbound message；
- 解析 session key；
- 确定 agent workspace / effective project workspace；
- restore session；
- build context；
- 绑定 hooks / progress / metadata；
- 调 `AgentRunner`；
- 保存状态；
- publish outbound。

### AgentRunner

面向“一次 tool-capable LLM execution”的模型层责任：

- 接受 `AgentRunSpec`；
- 调 provider；
- 处理 streaming / reasoning blocks / tool-call deltas；
- 调 `ToolRegistry` 执行工具；
- 把 tool result 回填 messages；
- 重复直到 final answer / runtime limit / error。

这层划分是 current-source 面试里最应该讲清楚的点之一。

## Workspace 的两个概念

不要混淆：

```text
configured agent workspace
vs
effective project workspace
```

Agent workspace 拥有：identity、durable memory、custom skills、cron 等。

WebUI 选中其他 project 后：project `AGENTS.md`、相对文件路径和 shell working directory 可以切到 project workspace，但不会把 agent 的 identity/memory 搬过去。

## Session isolation

默认 channel/chat 映射到各自 session。`unifiedSession` 可以主动共享跨 channel conversation，但单用户方便 ≠ 多用户安全。

## Concurrency

全局 inbound turn 并发目前由环境变量：

```text
NANOBOT_MAX_CONCURRENT_REQUESTS
```

控制；未设置或 <=0 表示 unlimited。

Subagent 有独立并发上限：

```text
agents.defaults.maxConcurrentSubagents
```

当前默认 4。

不要再背旧的固定 semaphore=3。

## 源码阅读顺序

```text
bus/events.py
→ bus/queue.py
→ agent/loop.py
→ agent/context.py
→ agent/runner.py
→ agent/tools/registry.py
→ providers/
```

只追一条 turn，不要同时展开 memory / cron / channel internals。

## 验收问题

1. 为什么 `AgentRunner` 可以被 Subagent 复用？
2. 为什么 MCP connection lifecycle 不应该放进 AgentLoop？
3. Session lock 和全局 request concurrency 是一回事吗？
4. project workspace 切换后哪些状态不跟着切？
