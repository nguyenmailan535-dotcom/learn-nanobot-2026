# 02 — Nanobot 2026 Current Overview

## 不再使用旧的“4000 行框架”标签

不要把固定代码量当成 Nanobot 的卖点。current-source 已经包含 WebUI、Gateway、TUI、API、Plugins、MCP、Channels、Automations、Dream、Subagents、安全边界等大量实现，源码规模早已不是旧教程时期的口径。

更适合面试的定位：

> Nanobot 是一个可读性较高、功能完整的 self-hosted agent runtime，适合用来研究一个真实 Agent 产品如何把 provider、tools、memory、channels、workspace、automation 和 security 组织在一起。

## Runtime surfaces

```text
nanobot agent -m "..."   one-shot
nanobot agent             terminal interaction
nanobot webui             browser workbench
nanobot gateway           long-running channels + automation host
nanobot serve             OpenAI-compatible HTTP API
Python SDK                in-process embedding
```

不要把它们理解成五套 Agent。它们最终复用同一套 runtime 核心。

## 核心组件地图

| 组件 | 责任 |
|---|---|
| MessageBus | transport 与 core 解耦 |
| AgentLoop | session/workspace/context + turn orchestration |
| AgentRunner | provider/tool execution loop |
| Provider | 模型后端 |
| ToolRegistry | 工具发现、schema、执行入口 |
| SessionManager | session 持久化/上下文相关状态 |
| Consolidator / AutoCompact | 控制长期 session context 成本 |
| MemoryStore / Dream | durable memory |
| Gateway | channels + WebUI + background jobs |
| Agent Plugins | skills/MCP 的安装与启用边界 |

## 本章源文件

优先看：

```text
docs/concepts.md
docs/architecture.md
AGENTS.md
```

不要上来读 `runner.py` 1600 行。

## 最小实验

1. `nanobot status`
2. `nanobot agent -m "Reply only with runtime-ok"`
3. `nanobot webui`
4. 观察同一个 workspace 下 session 是否可继续。

## 面试自测

- 为什么 Gateway 不是 AgentLoop？
- 为什么 CLI / WebUI / chat app 不应该各自实现一套 Agent？
- 为什么框架需要 MessageBus？
- current-source 相比早期教程增加了哪些“产品级”能力？
