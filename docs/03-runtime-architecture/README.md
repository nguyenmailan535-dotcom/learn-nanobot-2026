# 03 - Nanobot Runtime 架构深入解析

> 🎯 **本章目标**：深入理解 current-source 的核心分层、一次用户 Turn 的生命周期、AgentLoop/AgentRunner 边界、Context/Session/Tool/Memory 的协作方式，以及当前的并发模型。  
> **源码基线**：HKUDS/nanobot main，2026-09-24 学习快照。

---

## 目录

- [3.1 架构总览](#31-架构总览)
- [3.2 MessageBus 与事件模型](#32-messagebus-与事件模型)
- [3.3 AgentLoop：面向用户 Turn 的编排层](#33-agentloop面向用户-turn-的编排层)
- [3.4 一个 Turn 的七阶段 Pipeline](#34-一个-turn-的七阶段-pipeline)
- [3.5 AgentRunner：面向模型的 Provider/Tool Loop](#35-agentrunner面向模型的-providertool-loop)
- [3.6 ContextBuilder：模型到底看见什么](#36-contextbuilder模型到底看见什么)
- [3.7 ToolRegistry 与 ToolLoader](#37-toolregistry-与-toolloader)
- [3.8 Session、Compaction 与 Memory](#38-sessioncompaction-与-memory)
- [3.9 Workspace Scope](#39-workspace-scope)
- [3.10 并发模型](#310-并发模型)
- [3.11 Hooks、Events 与 Delivery](#311-hooksevents-与-delivery)
- [3.12 关键设计模式](#312-关键设计模式)
- [3.13 如何定位 Bug](#313-如何定位-bug)
- [3.14 面试高频题](#314-面试高频题)
- [3.15 本章总结](#315-本章总结)

---

## 3.1 架构总览

官方 docs/architecture.md 给出的主链：

~~~text
Channel
  ↓
MessageBus / InboundMessage
  ↓
AgentLoop
  ↓
AgentRunner
  ↔ Provider
  ↔ Tools
  ↓
AgentLoop
  ↓
MessageBus / OutboundMessage
  ↓
Channel
~~~

可以进一步分成五层：

~~~text
┌───────────────────────────────────────────────┐
│ Surface: CLI / WebUI / Chat Apps / API / SDK │
├───────────────────────────────────────────────┤
│ Transport: Channels / MessageBus              │
├───────────────────────────────────────────────┤
│ Turn: AgentLoop / TurnContext / Delivery      │
├───────────────────────────────────────────────┤
│ Execution: AgentRunner / Provider / Tools      │
├───────────────────────────────────────────────┤
│ State: Session / Memory / Skills / Workspace  │
└───────────────────────────────────────────────┘
~~~

旧版教程常把“AgentLoop 是心脏”作为核心结论。现在更重要的是：

> **看清每一层的 ownership，而不是找一个万能核心类。**

---

## 3.2 MessageBus 与事件模型

源码：

~~~text
nanobot/bus/events.py
nanobot/bus/queue.py
nanobot/bus/outbound_events.py
nanobot/bus/runtime_events.py
~~~

### 3.2.1 InboundMessage

所有 Channel 进入 Core 前都应该转换为统一 InboundMessage。

典型信息包括：

~~~text
channel
sender_id
chat_id
content
media
metadata
session_key
~~~

这样 AgentLoop 不需要知道 Telegram Update 或 Feishu SDK Event 的原始类型。

### 3.2.2 为什么需要 MessageBus

如果 Channel 直接调用 Agent：

~~~text
Telegram → Agent
Feishu   → Agent
WebUI    → Agent
~~~

平台层会逐渐依赖 session/runtime/tool 细节。

使用 MessageBus：

~~~text
Telegram ─┐
Feishu   ─┼→ InboundMessage → Agent Core
WebUI    ─┘
~~~

实现 transport/core 解耦。

---

## 3.3 AgentLoop：面向用户 Turn 的编排层

源码：

~~~text
nanobot/agent/loop.py
~~~

current-source 中 AgentLoop 拥有或协调：

- ModelRuntimeResolver；
- ContextBuilder；
- SessionManager；
- ToolRegistry；
- AgentRunner；
- Consolidator；
- SubagentManager；
- AutoCompact；
- per-session pending queues；
- WorkspaceScopeResolver；
- TurnDelivery；
- CommandRouter。

构造阶段可以理解为：

~~~text
AgentLoop
├── ContextBuilder
├── SessionManager
├── ToolRegistry
├── AgentRunner
├── Consolidator
├── SubagentManager
├── AutoCompact
└── CommandRouter
~~~

### 3.3.1 caller-owned ToolRegistry

current AgentLoop.from_config 明确要求 caller 提供 ToolRegistry。

原因是 application composition root 需要共享：

~~~text
ToolRegistry
├── AgentLoop
└── MCPProvider
~~~

所以 MCP connection lifecycle 不属于 AgentLoop。

这是一条非常重要的 current-source 事实。

---

## 3.4 一个 Turn 的七阶段 Pipeline

AgentLoop._process_message 创建 TurnContext 后，会明确执行：

~~~text
restore
  ↓
compact
  ↓
command
  ↓
build
  ↓
run
  ↓
save
  ↓
respond
~~~

源码结构概念上：

~~~python
await self._run_turn_stage(ctx, "restore", self._restore_turn)
await self._run_turn_stage(ctx, "compact", self._compact_session)

if await self._run_turn_stage(ctx, "command", self._dispatch_command):
    return ctx.outbound

await self._run_turn_stage(ctx, "build", self._build_turn)
await self._run_turn_stage(ctx, "run", self._run_turn)
await self._run_turn_stage(ctx, "save", self._persist_turn)
await self._run_turn_stage(ctx, "respond", self._prepare_outbound)
~~~

### Stage 1：restore

负责：

- normalize attachment；
- get/create Session；
- 根据 session policy 缩减 tools；
- restore runtime checkpoint/interruption；
- remember delivery route；
- persist workspace scope。

### Stage 2：compact

调用 AutoCompact.prepare_session，取可能存在的 pending session summary。

### Stage 3：command

处理 slash commands。

为什么在 build 前？

因为很多 command 根本不需要进入模型。

### Stage 4：build

这里会：

- resolve runtime；
- get session history；
- build RequestContext；
- resolve RuntimeContextBlock；
- prepare provider state / transcript input。

### Stage 5：run

进入 AgentRunner。

### Stage 6：save

把本轮 durable state 持久化回 Session。

### Stage 7：respond

构造 OutboundMessage 和 streaming completion 语义。

### 3.4.1 为什么 stage pipeline 值得学

它直接形成故障定位表：

| 问题 | 优先看 |
|---|---|
| Session 恢复错 | restore |
| Prompt 组装错 | build |
| Tool loop 错 | run |
| 对话没保存 | save |
| 平台没收到 | respond / channel |

---

## 3.5 AgentRunner：面向模型的 Provider/Tool Loop

源码：

~~~text
nanobot/agent/runner.py
~~~

类注释直接写：

> Run a tool-capable LLM loop without product-layer concerns.

也就是：

> Runner 不应该关心 Telegram、WebUI、具体 Session 页面，它只负责一次 model/tool execution。

### 3.5.1 AgentRunSpec

Loop → Runner 的运行契约。

关键字段包括：

~~~text
initial_messages / transcript_input
tools
runtime
max_iterations
max_tool_result_chars
hook
concurrent_tools
workspace
session_key
checkpoint_callback
consolidate_history
injection_callback
continuation_callback
provider_state
~~~

这说明 Runner 不是简单的 run(messages)。

### 3.5.2 run

AgentRunner.run 大致负责：

1. 构造 initial transcript/compaction state；
2. hook.before_run；
3. 进入 _run_core；
4. 形成 AgentRunResult；
5. after/error/finally hooks。

### 3.5.3 Tool Loop

核心仍然是：

~~~text
messages
  ↓
provider
  ↓
assistant message
  ├─ final text → stop
  └─ tool calls
       ↓
    execute tools
       ↓
    tool results
       ↓
    append
       ↓
    provider again
~~~

但 current Runner 还处理：

- streaming；
- provider conversation state；
- context compaction；
- injected follow-ups；
- tool result governance；
- max iterations；
- checkpoint；
- cancellation。

---

## 3.6 ContextBuilder：模型到底看见什么

源码：

~~~text
nanobot/agent/context.py
~~~

current class 中有：

~~~python
BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md"]
~~~

这是很重要的 source-level 事实。

### System Prompt 并不是一个固定字符串

概念上，它会组合：

~~~text
runtime/tool contract
+ bootstrap identity
+ project instructions
+ durable memory
+ skills summary
+ session summary
+ runtime context
+ current user input
~~~

并且来源还可能分属于：

~~~text
agent workspace
project workspace
current session
runtime provider
~~~

### build_system_prompt 与 transcript

你后面源码走读要重点追：

~~~text
TranscriptInput
→ ContextBuilder.build_transcript
→ AgentRunSpec
~~~

而不是只盯一个 system prompt 字符串。

---

## 3.7 ToolRegistry 与 ToolLoader

源码：

~~~text
nanobot/agent/tools/registry.py
nanobot/agent/tools/loader.py
nanobot/agent/tools/base.py
nanobot/agent/tools/schema.py
~~~

### ToolLoader

回答：

> 哪些 Tool 应该被发现和构造？

AgentLoop._register_default_tools 会先构造 ToolContext，其中包含：

~~~text
tools config
workspace
bus
subagent manager
cron service
exec session manager
sessions
provider loader
timezone
workspace sandbox
runtime control
~~~

然后：

~~~python
ToolLoader().load(ctx, self.tools)
~~~

### ToolRegistry

回答：

> 已经发现的 Tool 如何统一注册、暴露 schema、lookup 和 execute？

可以类比你熟悉的 Spring：

~~~text
ToolLoader
≈ 扫描/实例化 Bean 的阶段

ToolRegistry
≈ 一个面向模型的运行期 Registry
~~~

但不要机械等同，因为 Tool 还携带 model-facing schema 和 execution policy。

---

## 3.8 Session、Compaction 与 Memory

### SessionManager

职责是：

> Manage session identity, caching, retention, and persistence.

Session 保存结构化对话和 metadata。

### AutoCompact

AutoCompact 会关注 idle session：

~~~text
idle?
+ 存在未归档消息?
+ 没有 active turn?
→ schedule compact
~~~

### Consolidator

负责把旧 transcript 做 summarization/archive，并生成 summary checkpoint。

### Dream

再把长期积累整理成 durable files：

~~~text
SOUL.md
USER.md
memory/MEMORY.md
~~~

所以三层一定要区分：

~~~text
Session Replay
≠
Compacted Archive
≠
Curated Long-term Memory
~~~

---

## 3.9 Workspace Scope

current-source 区分：

~~~text
configured agent workspace
effective project workspace
~~~

| 数据 | Owner |
|---|---|
| SOUL / USER / Memory | Agent Workspace |
| custom skills | Agent Workspace |
| project AGENTS.md | Project Workspace |
| relative file path | Project Workspace |
| shell cwd | Project Workspace |
| session namespace | Agent Workspace identity |

这允许：

> 同一个 Agent profile 在多个 project 中工作，而不是为每个项目复制一套完整 Agent。

---

## 3.10 并发模型

### 3.10.1 Per-session FIFO

current AgentLoop 使用：

~~~text
_pending_queues[session_key]
~~~

每个 session 创建一个 sole worker。

新消息到达：

~~~text
该 session 已有 pending queue?
├─ 是 → 加入队列
└─ 否 → 新建 queue + worker
~~~

允许注入的 follow-up 可以在当前 turn 中被 Runner 消费；独立 turn 仍保持 FIFO barrier。

### 3.10.2 Session Lock

_session_locks 仍保护同一 session 的关键处理互斥。

### 3.10.3 全局并发

源码当前逻辑：

~~~python
_max = int(os.environ.get("NANOBOT_MAX_CONCURRENT_REQUESTS", "0"))
self._concurrency_gate = (
    asyncio.Semaphore(_max) if _max > 0 else None
)
~~~

含义：

- 未设置 / 0 / negative：Unlimited；
- positive：限制 running inbound requests。

### 3.10.4 Subagent 并发

另一套配置：

~~~text
agents.defaults.maxConcurrentSubagents
~~~

当前默认 4。

所以：

> inbound concurrency 与 subagent concurrency 是两套不同资源控制。

---

## 3.11 Hooks、Events 与 Delivery

current-source 还把 execution side effect 拆出来。

### Hook

Runner 生命周期钩子，例如：

~~~text
before_run
after_run
on_error
on_finally
~~~

### EventSink

用于发布 runtime/output event。

### TurnDelivery

负责：

- route；
- stream lifecycle；
- complete/fail；
- outbound publication。

这样 Runner 不需要知道 Feishu/Telegram 的发送细节。

---

## 3.12 关键设计模式

### Adapter

Channel 将平台协议转换为统一消息事件。

### Registry

Provider、Tool 都通过 registry/discovery 管理。

### Composition Root

MCPProvider、ToolRegistry 在应用启动层组装，而不是 runtime core 任意创建。

### Pipeline

Turn 明确拆成 restore/compact/command/build/run/save/respond。

### Context Object

TurnContext 集中保存一次 turn 的共享可变状态。

### Event-driven

MessageBus、runtime events、delivery 让 UI/channel/core 解耦。

---

## 3.13 如何定位 Bug

| 症状 | 第一入口 |
|---|---|
| WebUI 发消息没进 Agent | Channel / MessageBus |
| 同 Session 顺序乱 | pending queue / session worker |
| model 选错 | ModelRuntimeResolver |
| memory 没进 prompt | ContextBuilder |
| tool 没显示给模型 | ToolLoader / ToolRegistry |
| tool call 执行错 | Tool implementation |
| answer 没保存 | persist stage / SessionManager |
| stream 卡住 | Runner + TurnDelivery + Channel |
| MCP Tool 消失 | MCPProvider / Registry |
| 定时任务没触发 | CronService / automation coordinator |

---

## 3.14 面试高频题

### Q1：为什么 AgentLoop 和 AgentRunner 要拆？

因为它们的变化原因不同：

- Loop 随 channel/session/workspace/产品需求变化；
- Runner 随 provider/tool/streaming/model execution 变化。

拆开后，Runner 更容易被 Subagent 等场景复用，也更容易单测。

### Q2：为什么同 Session 要 FIFO？

否则可能出现：

- history 顺序错；
- tool result 归属错；
- provider state 覆盖；
- output 顺序错。

### Q3：默认 Unlimited 是否等于无限吞吐？

不是。

实际吞吐仍受：

- provider rate limit；
- CPU/内存；
- network；
- tools；
- channels；
- subagent。

生产环境要根据资源设置合理 cap。

---

## 3.15 本章总结

现在你应该能回答：

~~~text
谁负责一个用户 Turn？
→ AgentLoop

谁负责模型和工具循环？
→ AgentRunner

谁负责模型这次看到什么？
→ ContextBuilder

谁负责工具发现和执行？
→ ToolLoader + ToolRegistry

谁负责对话长期存在？
→ SessionManager + Memory/Compaction/Dream
~~~

下一章不再只看架构图，而是沿着**一条真实消息**把源码走到底。
