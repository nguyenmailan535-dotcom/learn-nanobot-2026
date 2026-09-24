# 04 - 源码逐行解读

> **2026 current-source 说明**：本章直接沿用原版 learn-nanobot 的章节结构与主体内容；凡涉及 Nanobot 具体源码、配置、路径、记忆、并发、MCP 生命周期等实现细节，均按 HKUDS/nanobot main @ 2026-09-24 (source trace snapshot around 62aa6ba6a33790a656b952ef150517bd70d6eb30) 修订。

> 🎯 **本章目标**：逐文件、逐函数地解读 Nanobot 的核心源码。看完本章，你将能在面试中自信地说"我读过全部源码"。

---

## 目录

- [4.1 源码目录结构总览](#41-源码目录结构总览)
- [4.2 AgentLoop - loop.py](#42-agentloop---looppy)
- [4.3 AgentRunner - runner.py](#43-agentrunner---runnerpy)
- [4.4 ContextBuilder - context.py](#44-contextbuilder---contextpy)
- [4.5 MemoryStore - memory.py](#45-memorystore---memorypy)
- [4.6 SubagentManager - subagent.py](#46-subagentmanager---subagentpy)
- [4.7 工具系统 - tools/](#47-工具系统---tools)
- [4.8 MessageBus - bus/](#48-messagebus---bus)
- [4.9 Channel 适配层 - channels/](#49-channel-适配层---channels)
- [4.10 配置系统 - config/schema.py](#410-配置系统---configschemapy)
- [4.11 关键代码片段解读](#411-关键代码片段解读)
- [4.12 面试高频题](#412-面试高频题)
- [4.13 本章总结](#413-本章总结)

---


## 4.1 源码目录结构总览

原版教程按“约 4000 行 / 10 个核心文件”组织源码阅读，这个数字已经不符合 current-source。章节结构保留，但阅读方法改为**按调用链聚焦核心文件**。

~~~text
nanobot/
├── bus/
│   ├── events.py
│   └── queue.py
├── agent/
│   ├── loop.py
│   ├── runner.py
│   ├── context.py
│   ├── memory.py
│   ├── autocompact.py
│   ├── subagent.py
│   ├── skills.py
│   ├── plugins.py
│   └── tools/
│       ├── registry.py
│       ├── loader.py
│       ├── filesystem.py
│       ├── shell.py
│       ├── web.py
│       └── mcp.py
├── session/
│   └── manager.py
├── channels/
│   ├── base.py
│   └── manager.py
└── config/
    ├── schema.py
    ├── loader.py
    └── paths.py
~~~

### 推荐源码阅读顺序

不要从第一行“通读整个仓库”。用一条真实 Turn：

~~~text
InboundMessage
→ AgentLoop
→ ContextBuilder
→ AgentRunSpec
→ AgentRunner
→ ToolRegistry
→ AgentRunResult
→ Session Save
→ OutboundMessage
~~~

然后再分别扩展 Memory、MCP、Subagent、Channel。

## 4.2 AgentLoop - loop.py

### 文件定位

~~~text
nanobot/agent/loop.py
~~~

### 核心类：AgentLoop

current AgentLoop 的类注释仍把自己称为 core processing engine，但它现在主要负责 **channel-facing turn orchestration**，而不是把整个 ReAct loop 都写在这里。

构造阶段会协调：

~~~text
ContextBuilder
SessionManager
ToolRegistry
AgentRunner
Consolidator
SubagentManager
AutoCompact
WorkspaceScopeResolver
CommandRouter
TurnDelivery
~~~

### 构造函数参数详解

现在参数已经远多于旧版，建议按责任分类，而不是死背签名：

| 分类 | 例子 |
|---|---|
| Model Runtime | provider、model、model presets、context window |
| Limits | max iterations、tool result limit、subagent concurrency |
| State | workspace、SessionManager |
| Tools | ToolsConfig、caller-owned ToolRegistry |
| Product | channels config、unified session、timezone |
| Hooks | hook/hook factory |
| Automations | CronService、local trigger store |

### run() 方法：核心消费循环

current `run()`：
1. 从 MessageBus 消费 `InboundMessage`；
2. 计算 effective session key；
3. priority command 可 inline dispatch；
4. 若该 Session 已有 active pending queue，新消息进入同一个 inbox；
5. 否则创建 per-session queue + sole worker；
6. worker 在 `_dispatch_one()` 内做 lock / optional global gate；
7. 最终进入 `_process_message()`。

### _process_message()：七阶段

~~~text
restore
→ compact
→ command
→ build
→ run
→ save
→ respond
~~~

每个阶段通过 `_run_turn_stage()` 统一记录 duration/outcome。

### _register_default_tools() 方法

current 不是一个个在 Loop 里手写 Tool。它构造 `ToolContext` 后调用：

~~~text
ToolLoader().load(ctx, self.tools)
~~~

MCP connection 本身不在这里；MCPProvider 由 application composition root 管理，并与 Loop 共享 ToolRegistry。

### _save_turn / persist 语义

current persistence 需要考虑：
- history 不能重复 append；
- provider state；
- runtime checkpoint；
- hidden/internal metadata；
- early persisted user message；
- automation/subagent marker。

因此不能再把它简单描述为“把 USER/ASSISTANT 追加到 memory/history.jsonl”。

### 面试要点

> “我把 AgentLoop 理解为 Turn Orchestrator：它负责 session admission、restore/build/run/save/respond；真正的 model/tool loop 在 AgentRunner。current 同 Session 由 pending queue + sole worker 保持 FIFO，全局并发 gate 是可选配置。”


## 4.3 AgentRunner - runner.py

### 文件定位

~~~text
nanobot/agent/runner.py
~~~

### 核心类：AgentRunner

current 类的定位：

> Run a tool-capable LLM loop without product-layer concerns.

也就是不负责 Channel、WebUI、Session 页面，而专注模型执行。

### run() 方法：ReAct 循环核心

入口数据不再只是 messages，而是 `AgentRunSpec`：

~~~text
runtime
tools
transcript_input
transcript_builder
max_iterations
max_tool_result_chars
hooks
checkpoint callback
compaction callbacks
injection callbacks
provider state
workspace/session key
~~~

概念循环：

~~~text
Provider
→ Assistant
→ 有 Tool Call?
   ├─ 否 → Final
   └─ 是 → ToolRegistry.execute
           → append Tool Results
           → Provider again
~~~

current 还处理：
- streaming delta/reasoning；
- concurrent tools；
- tool result spill/truncation；
- provider retry；
- conversation state；
- checkpoint；
- context compaction；
- mid-turn input injection；
- max-iteration finalization；
- cancellation。

### Tool 执行

不再存在旧版“AgentRunner 特判 Dream / MemoryStore 虚拟工具”这条主路径。普通 native/MCP tools 统一进入 Tool Registry/Execution；长期记忆更新由 Consolidator/Dream 体系负责。

### Lifecycle Hooks 详解

`run()` 会围绕 core execution 调用：
- before_run；
- after_run；
- on_error；
- on_finally。

Hook 使 observability、streaming/output side effect 与核心 loop 分离。

### 关键设计决策

最大的设计点是：**把 product-layer concern 留在 AgentLoop，把 model execution 做成可复用 Runner。** SubagentManager 也因此可以复用 AgentRunner。


## 4.4 ContextBuilder - context.py

### 文件定位

~~~text
nanobot/agent/context.py
~~~

### 核心类：ContextBuilder

current 定义：

~~~python
BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md"]
~~~

ContextBuilder 还持有 `MemoryStore` 与 `SkillsLoader`。

### build_system_prompt() 方法

System Prompt 不是单一静态模板，概念上会组合：
- stable runtime/tool contract；
- Agent identity；
- AGENTS/SOUL/USER；
- Project instruction；
- long-term memory；
- always skills / skill summary；
- session summary；
- channel/workspace-specific context。

### build_messages / build_transcript

current Loop 使用 `TranscriptInput` 分离：
- history；
- current_message；
- media；
- session_summary；
- runtime_context_blocks。

再由 transcript builder 构造 provider-facing messages。

### Prompt Cache 优化策略解读

current 测试仍关注稳定 prefix。Identity/tool contract 的稳定部分尽量放前面，project/session/current input 等易变内容放后面，从而减少不必要的 cache invalidation。

### 面试要点

> “Session 保存的是 durable conversation state，ContextBuilder 决定本轮到底把哪些状态暴露给模型。这个分层对长对话、Project Workspace、多 Skill、Memory 都非常关键。”


## 4.5 MemoryStore - memory.py

### 文件定位

~~~text
nanobot/agent/memory.py
~~~

### 核心类：MemoryStore

current 注释：

~~~text
Pure file I/O for memory files:
MEMORY.md, history.jsonl, SOUL.md, USER.md
~~~

### read_memory() / write_memory()

直接管理：

~~~text
workspace/memory/MEMORY.md
~~~

### append_history()

current append-only archive 是：

~~~text
workspace/memory/history.jsonl
~~~

写入前会做内部 reasoning 泄漏清洗、大小限制、cursor 分配等。

### Consolidator 压缩机制

新版关系：

~~~text
Session
→ Consolidator / AutoCompact
→ history.jsonl
→ Dream
→ SOUL / USER / MEMORY
~~~

旧 `memory/history.jsonl` 只在 migration 路径出现；旧 `Dream / MemoryStore` 虚拟工具不是 current 记忆更新主机制。

### GitStore

Dream-managed durable files有 Git-backed audit/recovery，使模型驱动的长期记忆修改可追踪、可恢复。


## 4.6 SubagentManager - subagent.py

### 文件定位

~~~text
nanobot/agent/subagent.py
~~~

### 核心类：SubagentManager

current 负责 background / inline subagent execution，并保存 task status、session ownership 与 concurrency capacity。

### spawn() 方法

概念流程：

~~~text
spawn(task)
→ 生成 task_id / status
→ asyncio.create_task(_run_subagent)
→ 记录 session → task mapping
→ completion 后 cleanup
→ 结果通过主 Session 的 pending/injection 路径重新进入 Agent
~~~

current Subagent 使用 focused system prompt + scoped tools，并复用 `AgentRunner`。它的 max iterations 与主 runtime limit 对齐，不应再背“固定 current runtime/config 约束”。

### 并发

独立配置：

~~~text
agents.defaults.maxConcurrentSubagents
~~~

current default 为 4，超过 capacity 的任务等待。


## 4.7 工具系统 - tools/

### 4.7.1 ToolRegistry - registry.py

ToolRegistry 统一提供：
- register；
- get；
- tool_names；
- get_definitions；
- execute；
- runtime context provider exposure。

### ToolLoader

current default tools 通过：

~~~text
ToolContext
→ ToolLoader.load()
→ ToolRegistry
~~~

完成 discovery 和作用域控制。

### 4.7.2 MCP Tool - mcp.py

current `MCPProvider` 拥有 configured MCP connections 和 dynamic tool registrations。它与 AgentLoop 共享 ToolRegistry，但生命周期由 application composition root 管理。

### 4.7.3 Message Tool

MessageTool 负责向当前 Channel/用户发送消息，最终仍经 delivery/channel callback，而不是让 AgentRunner 直接依赖平台 SDK。

### 4.7.4 Spawn Tool

Spawn/long-task 类工具通过 ToolContext 获取 `SubagentManager`，不需要在 Tool 内自己创建 Agent Runtime。


## 4.8 MessageBus - bus/

### 核心类：MessageBus

current MessageBus 仍是 Channel 与 Agent Core 的异步边界，但还承载 typed runtime/output event 的路由语义。

核心关系：

~~~text
Channel
→ InboundMessage
→ MessageBus
→ AgentLoop

AgentLoop/Runner
→ EventSink / OutboundMessage
→ MessageBus
→ ChannelManager
→ Channel
~~~

不要把它只记成“两个 Queue”；真正有价值的是 transport/core 解耦。


## 4.9 Channel 适配层 - channels/

### 基类：BaseChannel

Channel 负责把平台-specific payload 转为 Nanobot event contract，并把 OutboundMessage/stream event 发送回平台。

### ChannelManager

current 负责：
- package discovery / lifecycle；
- outbound routing；
- send retry；
- streaming/progress event handling；
- runtime status。

### Telegram 适配器示例

Telegram runtime 仍是一个 platform adapter，重点看：
- update → InboundMessage；
- media/thread metadata；
- send/retry；
- channel policy。

### 飞书适配器示例

current Feishu 支持长连接等 current setup flow；不要继续照旧版教程假设“必须搭公网 Webhook + ngrok”。平台连接方式应以 current channel package/docs 为准。


## 4.10 配置系统 - config/schema.py

### 配置数据类

current Config 基于 Pydantic schema，覆盖：
- Agent defaults；
- Model presets；
- Providers；
- Tools；
- MCP Servers；
- Channels；
- Gateway；
- Heartbeat / Dream；
- Security / Web / Image generation 等。

写回 Config 时官方文档优先 camelCase，同时兼容 snake_case。

### 配置加载

默认 Config：

~~~text
~/.nanobot/config.json
~~~

Agent Workspace：

~~~text
~/.nanobot/workspace/
~~~

Session 默认放在 Config data dir 下的 workspace-scoped sessions 路径，而不是普通 Project Workspace 目录里。

loader 还包含 config migration，因此读 schema 时也要看 loader。


## 4.11 关键代码片段解读

### 片段 1：完整的消息处理链路

~~~text
Channel
→ InboundMessage
→ AgentLoop.run
→ _enqueue_session_message
→ _run_session_queue
→ _dispatch_one
→ _process_message
→ restore/compact/command/build/run/save/respond
~~~

### 片段 2：Runner 入口

~~~python
result = await self.runner.run(
    AgentRunSpec(
        tools=effective_tools,
        runtime=runtime,
        transcript_input=transcript_input,
        transcript_builder=transcript_builder,
        concurrent_tools=True,
        ...
    )
)
~~~

### 片段 3：MCP 工具注册

~~~text
shared ToolRegistry
→ MCPProvider.from_config(...)
→ await connect()
→ list remote capabilities
→ wrap/register tools
→ AgentRunner sees normal Tool definitions
~~~

### 片段 4：Provider Runtime

Provider metadata、factory、model preset/runtime resolver 分离。一次 Turn 被 admit 后使用 immutable LLMRuntime snapshot，避免中途配置切换导致同一 Turn 前后不一致。


## 4.12 面试高频题

### Q1: 请描述 AgentLoop 的执行流程

> “先做 Session admission，同 Session 进入同一 pending queue。_process_message 创建 TurnContext 后依次 restore、compact、command、build、run、save、respond；run 阶段把 AgentRunSpec 交给 AgentRunner，Runner 执行 Provider/Tool loop。”

### Q2: current Nanobot 的长期记忆怎么工作？

> “不再是 Dream / MemoryStore + memory/history.jsonl。短期是 Session JSONL；AutoCompact/Consolidator 把历史压缩归档到 memory/history.jsonl；Dream 再整理 SOUL.md、USER.md、MEMORY.md，并通过 GitStore 保留可审计/恢复记录。”

### Q3: 工具结果为什么要有大小治理？

> “Tool Result 会重新进入模型 Context，过大结果会推高 token、打爆 context window 并污染推理。因此 current runtime 有 maxToolResultChars 等治理，还可以 spill/compact，而不是依赖一个永远固定的 current maxToolResultChars 配置 常量。”

### Q4: 如何新增 Provider？

优先看：
1. `providers/registry.py` 是否可以用现有 OpenAI-compatible path；
2. `config/schema.py` 增加配置；
3. 只有协议不兼容时才增加专门 Provider implementation；
4. 写 provider tests / mocked API path。

## 4.13 本章总结

### Current-source 核心链路

~~~text
Channel
→ InboundMessage
→ MessageBus
→ per-session FIFO
→ TurnContext
→ restore / compact / command / build / run / save / respond
→ AgentRunSpec
→ AgentRunner
→ Provider / ToolRegistry
→ AgentRunResult
→ Session Persistence
→ TurnDelivery
~~~

### 源码阅读建议

1. **不要追求“全部读完”**：优先理解稳定 Runtime Boundary。
2. **每次只追一个问题**：例如“第一次进入 Runner 前 messages 如何形成”。
3. **实现和 Test 一起看**：Test 往往比注释更精确地定义 Contract。
4. **记录输入/输出/下一跳**：避免只记类名。
5. **做最小实验**：Source Trace 必须能用 breakpoint/log/test 验证。

> 📝 **本章小结**：current Nanobot 已明显大于早期教学版本。真正有面试价值的不是声称“读过全部源码”，而是能准确解释一条真实 Turn 如何跨越 Channel、Session、Context、Runner、Tool、Persistence 与 Delivery，并说明每个边界为什么存在。

---

## 下一章

接下来，我们将深入学习 MCP 协议——AI 界的"USB-C 接口"。

➡️ [05 - MCP 协议详解](../05-mcp-protocol/README.md)

---

> 📝 **本章小结**：current-source 已远超早期“10 个核心文件”的规模。真正的完成标准不是声称“通读全部源码”，而是能把一条真实 Turn 从 InboundMessage → Session admission → TurnContext → AgentRunSpec → AgentRunner → ToolRegistry → Persistence / Delivery 跟到底，并能用断点、日志或测试验证每一跳。
