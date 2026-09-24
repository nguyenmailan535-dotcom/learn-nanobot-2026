# 10 - 子Agent与定时任务

> **阅读时间**：约 1.5 小时  
> **2026 current-source 说明**：本章直接沿用原版 learn-nanobot 的章节结构与主体内容；凡涉及 Nanobot 具体源码、配置、路径、记忆、并发、MCP 生命周期等实现细节，均按 HKUDS/nanobot main @ 2026-09-24 (source trace snapshot around 62aa6ba6a33790a656b952ef150517bd70d6eb30) 修订。

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

### 10.2.1 Spawn Tool 启动子代理

current Subagent Tool 通过 ToolContext 获得 `SubagentManager`。主 Agent 调用后，可选择 background 或 inline execution。

~~~text
Main Agent
  ↓ spawn
SubagentManager
  ↓
create task/status
  ↓
focused prompt + scoped tools
  ↓
AgentRunner
  ↓
result
  ↓
主 Session pending/injection path
~~~

### 10.2.2 SubagentManager 管理

current `SubagentManager` 管：
- task id / label / description；
- running asyncio tasks；
- per-session task ownership；
- status / error；
- concurrency capacity；
- cleanup/shutdown；
- focused system prompt；
- scoped ToolRegistry。

### 10.2.3 SubAgent 与主Agent的区别

| 维度 | 主 Agent Turn | Subagent |
|---|---|---|
| 用户入口 | 直接来自 Channel/WebUI | 主 Agent / tool 发起 |
| Session | 产品会话 | 绑定 origin session/task |
| Prompt | 完整 Agent Context | focused subagent prompt |
| Tool | current full/effective set | scope=subagent 的受限集 |
| 执行器 | AgentRunner | 同样复用 AgentRunner |
| 并发 | inbound concurrency | maxConcurrentSubagents |

### 10.2.4 为什么限制工具集

防止：
- 无边界递归 spawn；
- 子 Agent 冒充主 Agent 直接对用户乱发消息；
- 子任务创建不受控 Automation；
- 权限扩大。

current ToolLoader 会根据 scope 构建 Subagent Registry，而不是只靠 Prompt “请不要调用某工具”。

### 10.2.5 迭代限制的设计思考

**旧版固定“主 40、子 15”已经过时。**

current AgentLoop 初始化 SubagentManager 时把：

~~~text
max_iterations=self.max_iterations
~~~

传入，且 runtime 会同步可变 limit。真正的资源边界还包括 `maxConcurrentSubagents`（current 默认 4）。

工程原则：
- iteration limit 防止模型/工具循环失控；
- concurrency limit 防止后台任务爆炸；
- timeout/cancellation 防止悬挂。

### 10.2.6 结果回报机制

current result 会带 task metadata 回到 origin Session，活跃 Turn 可以通过 pending injection 接收 Subagent completion；否则作为后续 Session work 继续处理。

这比旧版“简单向 MessageBus 发一条 sender_id=subagent 消息”更完整，因为还要考虑：
- durable follow-up；
- hidden history marker；
- FIFO；
- terminal wait；
- cancellation。

### 10.2.7 使用场景

适合：
- 可并行检索；
- 长耗时分析；
- 独立代码/文档检查；
- 多来源 Research。

不适合：
- 需要频繁用户确认；
- 强共享可变状态；
- 极短任务（调度开销反而更高）。


## 10.3 定时任务（Cron）系统

### 10.3.1 CronService

**current CronService 不是基于 current CronService。**

源码：

~~~text
nanobot/cron/service.py
nanobot/cron/types.py
nanobot/agent/tools/cron.py
~~~

current `CronService` 自己管理：
- jobs.json store；
- FileLock；
- action log；
- run records；
- timer task；
- next-run 计算；
- corrupted store recovery。

Cron expression 解析使用 `croniter`，时区使用标准 `zoneinfo`。

### 10.3.2 cron 工具的操作

CronTool current 主要面向 scheduled reminders/tasks，并支持 list/add/remove 等当前 schema 行为。实际参数以 Tool definition 为准。

### 10.3.3 调度配置方式

current `CronSchedule.kind`：

~~~text
at
every
cron
~~~

对应：
- one-time timestamp；
- interval；
- cron expression + optional IANA timezone。

Tool 输入层常见：
- `at`；
- `every_seconds`；
- `cron_expr`；
- timezone。

### 10.3.4 定时任务的执行流程

~~~text
CronService
  ↓ due job
Gateway callback
  ↓
构造 session-bound automation turn
  ↓
AgentLoop.submit_cron_turn
  ↓
CronTurnCoordinator
  ↓
同一 Session FIFO
  ↓
AgentRunner
  ↓
结果投递回 origin Channel/Topic
~~~

current user-created Cron Job 与旧版“channel=cron 的随意系统消息”不同，它强调绑定具体 origin session/delivery context。

### 10.3.5 防递归 / 防失控

current runtime 通过 Tool scope、Automation coordinator、bound session contract、system job protection 等多层控制，而不是只靠某个 `if current_message.channel == "cron"`。

关键思想仍然成立：

> 自动化上下文不应该拥有无限创建自身/更多自动化的能力。


## 10.4 Heartbeat 心跳服务

### 10.4.1 什么是 Heartbeat

current Heartbeat 仍用于周期性后台检查，但实现已经 **backed by the same Cron service**。

它读取：

~~~text
<workspace>/HEARTBEAT.md
~~~

如果 `## Active Tasks` 下有任务，就执行检查；只有有用/可行动的结果才通知最近活跃的 chat target，“nothing changed” 类型结果会被抑制。

### 10.4.2 配置方式

current Config：

~~~json
{
  "gateway": {
    "heartbeat": {
      "enabled": true,
      "intervalS": 1800
    }
  }
}
~~~

默认 interval 是 30 分钟。要长期运行，必须让 `nanobot gateway` 保持运行。

### 10.4.3 心跳触发机制

~~~text
Gateway
→ cron-backed protected heartbeat job
→ HEARTBEAT.md
→ Agent Turn
→ evaluator / usefulness gate
→ useful result?
   ├─ yes → deliver
   └─ no  → suppress
~~~

Heartbeat Job 会出现在 cron list 中，但属于 system-managed job，不能像普通用户 Cron 一样删除；要停用应改 config 并重启 Gateway。

### 10.4.4 Heartbeat 的使用场景

适合：
- 周期检查 workspace task；
- 服务/状态变化提醒；
- “仅变化时通知”的安静监控。

不适合：
- 精确某个时刻必须执行一次的提醒（用 Cron at）；
- 用户明确要求每次都收到结果（用 scheduled automation）。

### 10.4.5 keep_recent_messages

旧版字段/实现不应再作为 current 面试答案。current Heartbeat 通过 session-bound runtime、HEARTBEAT.md、evaluator 和 Cron service 管理上下文；具体历史保留策略以 current Session/Context 实现为准。


## 10.5 三者的协作关系

### 10.5.1 SubAgent、Cron、Heartbeat 对比

| 维度 | Subagent | User Cron | Heartbeat |
|---|---|---|---|
| 触发 | 当前 Agent 动态发起 | 时间/间隔/Cron 表达式 | protected periodic schedule |
| 目的 | 并行/后台任务 | 明确的未来任务 | 安静的周期检查 |
| 执行器 | AgentRunner | Session-bound Agent Turn | Cron-backed system turn |
| 返回 | Origin Session injection/follow-up | Origin Channel/Topic | 最近活跃 target，且可抑制无变化结果 |
| 管理 | SubagentManager | CronService | Gateway + CronService |
| 持久化 | task/session runtime | workspace/cron/jobs.json + run records | 同一 Cron Store 的 system-managed job |

### 10.5.2 协作场景示例

Research Agent：
1. 用户问“比较 20 篇论文”；
2. 主 Agent spawn 两个 Subagent 并行检索；
3. 结果回到同一个 Session；
4. 用户设置每天 9 点生成 digest → Cron；
5. HEARTBEAT.md 里配置“只有新论文/失败任务时通知” → Heartbeat。

### 10.5.3 设计模式分析

- Boss/Worker；
- Scheduler；
- Session-bound Event Routing；
- Bounded Concurrency；
- Protected System Job；
- Eventual Result Injection。

## 10.6 实战练习

### 练习 1：使用 SubAgent 并行处理

```bash
# 启动 Agent
nanobot

# 对话示例：
# You: 帮我做两件事：
#   1. 搜索 Python 3.12 的新特性
#   2. 搜索 Rust 2024 的发展趋势
# 分别用后台任务处理

# Agent 应该会调用两次 spawn，启动两个 SubAgent 并行执行
# 你可以继续与主Agent对话，等后台任务完成后收到结果
```

### 练习 2：创建定时任务

```bash
nanobot

# 对话示例：
# You: 帮我创建一个定时任务，每小时提醒我休息一下

# Agent 会调用 cron 工具：
# {
#   "action": "add",
#   "name": "rest_reminder",
#   "schedule": {"every_seconds": 3600},
#   "message": "休息提醒：已经工作1小时了，起来活动一下吧！"
# }

# 查看任务列表
# You: 列出所有定时任务

# 删除任务
# You: 删除休息提醒任务
```

### 练习 3：配置 Heartbeat

```json
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "enabled": true,
        "interval_s": 300,
        "keep_recent_messages": 3
      }
    }
  }
}
```

```bash
# 启动后，每5分钟Agent会自动醒来
# 你可以在 AGENTS.md 中告诉它醒来时要做什么：

# AGENTS.md 中添加：
# ## 心跳行为
# 当收到心跳唤醒时：
# 1. 检查 workspace 中是否有新文件
# 2. 如果有 TODO.md，检查待办事项的状态
# 3. 如果发现需要处理的事项，主动通知用户
```

---


## 10.7 面试高频题

### 题目 1：Nanobot 的 SubAgent 系统怎么设计？

> “SubagentManager 用 asyncio task 管 background/inline execution，构造 focused prompt 和 scope=subagent 的 ToolRegistry，然后复用 AgentRunner。任务按 origin session 记录，完成结果回到主 Session 的 pending/injection 路径；maxConcurrentSubagents 控制后台并发。”

### 题目 2：如何防止 Agent 系统中的递归/失控？

分层回答：
- Tool scope 限制子 Agent capability；
- iteration limit；
- subagent concurrency limit；
- Cron/Automation bound session contract；
- system-managed Heartbeat/Dream job 保护；
- cancellation/timeout；
- Workspace/Sandbox 安全边界。

### 题目 3：Cron 和 Heartbeat 有什么区别？

> “都由 current CronService 提供时间调度基础，但用户 Cron 是明确的 session-bound scheduled turn；Heartbeat 是 protected system job，周期读取 HEARTBEAT.md，并通过 usefulness gate 只在值得通知时投递。”

### 题目 4：设计并行任务系统要注意什么？

- capacity / backpressure；
- cancellation propagation；
- result ownership；
- ordering / FIFO；
- duplicate/retry idempotency；
- shared mutable state；
- timeout；
- observability；
- graceful shutdown。

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
│   │Manager │  │  (current CronService) │                │
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
| SubAgent 限制 | current runtime/config limit迭代，无 message/spawn/cron 工具 |
| SubAgent 回报 | 通过 MessageBus 发 InboundMessage 回主会话 |
| Cron 引擎 | 基于 current CronService |
| Cron 配置 | every_seconds / cron_expr+tz / at |
| Cron 防递归 | cron 上下文中禁止创建新 cron |
| Heartbeat | 周期唤醒 Agent，Agent 自主决策 |
| keep_recent_messages | 心跳时只保留最近 N 条消息 |
| 核心原则 | 受控并行 + 防递归 + 最小权限 |

---

> **下一章**：[11 - 安全与部署](../11-security-and-deploy/README.md) —— 生产环境的安全策略和 Docker 部署实践