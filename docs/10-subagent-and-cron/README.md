# 10 - 子Agent与定时任务

> **阅读时间**：约 1.5 小时  
> **前置知识**：[09 - 多平台接入](../09-multi-platform/README.md)  
> **学习目标**：理解 SubAgent 后台任务机制、Cron 定时调度系统、Heartbeat 心跳服务，掌握并发任务设计

---

## 目录

- [10.1 为什么需要子Agent和定时任务](#101-为什么需要子agent和定时任务)
- [10.2 子Agent（SubAgent）系统](#102-子agentsubagent系统)
- [10.3 定时任务（Cron）系统](#103-定时任务cron系统)
- [10.4 Heartbeat 心跳服务](#104-heartbeat-心跳服务)
- [10.5 三者的协作关系](#105-三者的协作关系)
- [10.6 实战练习](#106-实战练习)
- [10.7 面试高频题](#107-面试高频题)
- [10.8 本章小结](#108-本章小结)

---

## 10.1 为什么需要子Agent和定时任务

### 10.1.1 主Agent的局限

主Agent是同步的——用户发消息，Agent处理，返回结果。但有些场景需要：

```
场景 1：用户说"帮我调研一下 Rust 和 Go 的对比，要详细的"
→ 这可能需要 10 分钟搜索和整理
→ 用户不想等 10 分钟什么都做不了

场景 2：用户说"每天早上 8 点给我发一份新闻摘要"
→ 需要定时执行，不是一次性对话

场景 3：用户同时提出多个独立任务
→ "帮我查天气，同时分析一下这个代码文件"
→ 两个任务可以并行处理
```

### 10.1.2 解决方案

| 场景 | 解决方案 |
|------|---------|
| 耗时后台任务 | **SubAgent**（子代理后台执行） |
| 定时触发任务 | **Cron**（定时调度） |
| 周期性唤醒 | **Heartbeat**（心跳服务） |

---

## 10.2 子Agent（SubAgent）系统

### 10.2.1 SpawnTool

主 Agent 可以通过 Spawn Tool 委托明确子任务。

### 10.2.2 SubagentManager

current：

```
nanobot/agent/subagent.py
```

SubagentManager 支持：

- background `spawn()`
- synchronous `run_inline()`
- task status
- per-session task tracking
- result injection
- scoped Tool Registry / Workspace

### 10.2.3 复用 AgentRunner

current Subagent 不是再启动一个完整 Channel AgentLoop，而是构造 focused prompt/runtime/tools，并复用：

```
AgentRunner
+
AgentRunSpec
```

这正是 AgentLoop/AgentRunner 分层的实际收益。

### 10.2.4 工具权限

Subagent 使用 scope-specific ToolLoader。需要避免递归/危险 Capability 时，应该从 Tool Registry/Scope 层限制，而不是只靠 Prompt。

### 10.2.5 Iteration 与并发

旧版“主 Agent 40 次、SubAgent 固定 15 次”已经不符合 current-source。

current SubagentManager 接收 `max_iterations`，AgentLoop 会同步 runtime limits；并发由：

```
agents.defaults.maxConcurrentSubagents
```

控制，current default 为 **4**。超出容量的任务等待。

### 10.2.6 结果回报

Subagent 完成后结果可以作为内部 follow-up 注入主 Session。current AgentLoop 还有 terminal wait/injection 逻辑，避免主 Turn 在仍有同 Session 子任务时过早结束。

## 10.3 定时任务（Cron）系统

### 10.3.1 current CronService

current：

```
nanobot/cron/service.py
```

不再基于旧教程的 APScheduler 示例。current CronService 自己维护 Job Store/Timer，并使用 `croniter` 计算 cron expression 的下一次运行时间。

支持三类 schedule：

```
at
every
cron
```

### 10.3.2 持久化

默认 Store：

```
<workspace>/cron/jobs.json
```

还会记录 action/run state，并对损坏 Store 做保守处理，避免解析失败后错误覆盖全部任务。

### 10.3.3 Session-bound Automation

current user-created Agent Cron Job 绑定具体 Session Delivery Context。旧 legacy payload 会迁移；缺少可路由 Session 的 malformed/unbound job 会被禁用，而不是盲目执行。

### 10.3.4 Cron Tool

`nanobot/agent/tools/cron.py` 通过 ToolContext 接入 CronService，让 Agent 创建/管理 Reminder 和 Recurring Task。

### 10.3.5 Local Trigger

current Automations 还包含 Local Trigger：

```
nanobot trigger ...
```

适合 CI、Shell Script、本地事件把工作送入一个已绑定 Topic/Session。它和 Cron 都走 Automation Turn Coordinator，但触发来源不同。

## 10.4 Heartbeat 心跳服务

### 10.4.1 current Heartbeat

current-source 已移除旧的独立 Heartbeat Service。

现在 Gateway 启动时会注册一个**受保护的 Heartbeat Cron Job**，周期读取：

```
<workspace>/HEARTBEAT.md
```

默认语义是：

- 定期检查 Active Tasks
- 没有有用结果时静默
- 有值得通知的结果才发送到最近活跃 Chat

### 10.4.2 HEARTBEAT.md

current template：

```
nanobot/templates/HEARTBEAT.md
```

这是适合“周期后台检查”的任务清单。

### 10.4.3 Cron vs Heartbeat

```
普通 Cron
→ 每个 Job 有明确 Prompt/Schedule
→ 通常回到创建它的 Session

Heartbeat
→ Protected System Cron
→ 读取 HEARTBEAT.md
→ 适合长期安静检查
→ Routine Result 可以不通知
```

因此原版 `keep_recent_messages` 形式的“独立 Heartbeat Service 配置”不再作为 current 主设计。

## 10.5 三者的协作关系

current-source 实际上是四类机制：

| 机制 | 触发 | 主要用途 |
|---|---|---|
| Subagent | 主 Agent Tool Call | 并行/委托明确子任务 |
| Cron | 时间调度 | Reminder / Recurring Task |
| Local Trigger | 本地命令/事件 | CI、Script、Webhook Adapter |
| Heartbeat | Protected System Cron | 周期安静检查 HEARTBEAT.md |

共同原则：

- Session-bound routing
- 最小 Tool Scope
- Concurrency/Iteration 控制
- Durable Job State
- Cancellation / Recovery
- 不依赖 LLM“自觉”防止失控

## 10.6 实战练习

### 练习 1：两个 Subagent 并行任务

让主 Agent 分别：

- 调研一个技术问题
- 分析一个本地文件

观察 Subagent Status、并发限制和结果注入。

### 练习 2：Cron

创建一个短周期测试 Reminder，观察：

```
workspace/cron/jobs.json
workspace/cron/runs/
```

然后删除 Job。

### 练习 3：Heartbeat

编辑：

```
workspace/HEARTBEAT.md
```

增加一个安全、只读 Active Task，启动 Gateway，观察 Routine Result 是否静默。

### 练习 4：Local Trigger

创建一个绑定当前 Topic 的 Trigger，然后从 Shell 触发，观察它如何进入对应 Session，而不是新建无关 Conversation。

## 10.7 面试高频题

### 题目 1：current Subagent 怎么设计？

> SubagentManager 构造 focused execution context，并复用 AgentRunner/AgentRunSpec；支持 background/inline 模式。并发由 maxConcurrentSubagents 控制，结果可以注入主 Session。

### 题目 2：为什么旧版固定 15 次迭代答案已经不对？

> current Subagent 的 max_iterations 由 Runtime/AgentLoop 同步，不再使用“固定 15”作为架构常量。真正的资源治理应该同时考虑 iteration、concurrency、timeout、Tool Scope。

### 题目 3：Cron 现在还基于 APScheduler 吗？

> current `CronService` 自己管理持久化 Job/Timer，并使用 croniter 计算 Cron Schedule；不应再按旧 APScheduler 代码回答。

### 题目 4：Heartbeat 和 Cron 的区别？

> current Heartbeat 本身就是 Gateway 注册的受保护 Cron Job，但语义不同：它周期读取 HEARTBEAT.md，并通过 Notification Gate 只报告有价值结果。

### 题目 5：Local Trigger 有什么价值？

> 它把 CI/脚本/本地事件安全地路由到一个已绑定 Session，让 Automations 不只依赖时间触发。

## 10.8 本章小结

### 核心概念图

```
┌──────────────────────────────────────────────────┐
│             Nanobot 并发与调度体系                 │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │              主Agent (Main Agent)          │  │
│  │  max_tool_iterations: 40                   │  │
│  │  完整工具集                                 │  │
│  │                                            │  │
│  │  ┌──────┐  ┌──────┐  ┌──────────────────┐ │  │
│  │  │spawn │  │ cron │  │ 其他工具...       │ │  │
│  │  └──┬───┘  └──┬───┘  └──────────────────┘ │  │
│  └─────┼────────┼────────────────────────────┘  │
│        │        │                                │
│   ┌────▼───┐  ┌─▼──────────────┐                │
│   │SubAgent│  │  CronService   │                │
│   │Manager │  │  (APScheduler) │                │
│   │        │  │                │                │
│   │ iter:15│  │ cron_expr      │                │
│   │ 受限   │  │ every_seconds  │                │
│   │ 工具集 │  │ at             │                │
│   └───┬────┘  └───────┬───────┘                │
│       │               │                         │
│       │    ┌──────────▼──────────┐              │
│       └───→│    MessageBus       │              │
│            │   (结果回报通道)     │              │
│            └─────────────────────┘              │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │           HeartbeatService                 │  │
│  │  interval_s: 1800                          │  │
│  │  keep_recent_messages: 5                   │  │
│  │  定期唤醒Agent，Agent自主决策              │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 面试记忆清单

| 考点 | 一句话回答 |
|------|-----------|
| SubAgent 启动 | spawn 工具启动，SubagentManager 管理 |
| SubAgent 限制 | 15 次迭代，无 message/spawn/cron 工具 |
| SubAgent 回报 | 通过 MessageBus 发 InboundMessage 回主会话 |
| Cron 引擎 | 基于 APScheduler |
| Cron 配置 | every_seconds / cron_expr+tz / at |
| Cron 防递归 | cron 上下文中禁止创建新 cron |
| Heartbeat | 周期唤醒 Agent，Agent 自主决策 |
| keep_recent_messages | 心跳时只保留最近 N 条消息 |
| 核心原则 | 受控并行 + 防递归 + 最小权限 |

---

> **下一章**：[11 - 安全与部署](../11-security-and-deploy/README.md) —— 生产环境的安全策略和 Docker 部署实践