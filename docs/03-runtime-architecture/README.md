# 03 - 架构深入解析

> 🎯 **本章目标**：深入理解 Nanobot 的五层架构、四大核心模块、数据流以及 10 个关键设计模式。这一章是面试中展现"技术深度"的核心素材。

---

## 目录

- [3.1 整体架构概览](#31-整体架构概览)
- [3.2 四大核心模块详解](#32-四大核心模块详解)
- [3.3 数据流图](#33-数据流图)
- [3.4 模块间的协作关系](#34-模块间的协作关系)
- [3.5 关键设计模式](#35-关键设计模式)
- [3.6 架构对比](#36-架构对比)
- [3.7 面试高频题](#37-面试高频题)
- [3.8 本章总结](#38-本章总结)

---

## 3.1 整体架构概览

### 五层架构

Nanobot 的架构可以清晰地划分为五个层次，从上到下分别是：

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Layer 5: UI 层 (User Interface)                                │
│  ┌──────────┬──────────┬────────┬────────┬───────┬──────────┐  │
│  │ Telegram │ Discord  │  飞书  │  钉钉  │ 微信  │   Web    │  │
│  └────┬─────┴────┬─────┴───┬────┴───┬────┴──┬────┴────┬─────┘  │
│       │          │         │        │       │         │         │
│═══════╪══════════╪═════════╪════════╪═══════╪═════════╪═════════│
│       │          │         │        │       │         │         │
│  Layer 4: Gateway 层 (消息网关)                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           ChannelManager + MessageBus                   │    │
│  │   ┌──────────────────┐  ┌──────────────────────┐       │    │
│  │   │  Inbound Queue   │  │   Outbound Queue     │       │    │
│  │   │  (用户消息入队)   │  │   (回复消息出队)      │       │    │
│  │   └────────┬─────────┘  └──────────┬───────────┘       │    │
│  └────────────┼────────────────────────┼───────────────────┘    │
│               │                        │                        │
│═══════════════╪════════════════════════╪════════════════════════│
│               │                        ↑                        │
│  Layer 3: Core Agent 层 (核心智能体)                             │
│  ┌────────────▼────────────────────────┼───────────────────┐    │
│  │                                     │                   │    │
│  │   ┌──────────────┐   ┌─────────────┴──┐                │    │
│  │   │  AgentLoop   │──→│  AgentRunner   │                │    │
│  │   │  (消息消费)   │   │  (ReAct循环)   │                │    │
│  │   └──────────────┘   └───────┬────────┘                │    │
│  │                              │                          │    │
│  │         ┌────────────────────┼────────────────┐         │    │
│  │         │                    │                │         │    │
│  │   ┌─────▼──────┐   ┌───────▼────────┐  ┌────▼─────┐  │    │
│  │   │ContextBuilder│ │  MemoryStore   │  │SubAgent  │  │    │
│  │   │(上下文构建)  │  │  (记忆管理)    │  │Manager   │  │    │
│  │   └─────────────┘  └───────────────┘  └──────────┘  │    │
│  │                                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│               │                                              │
│═══════════════╪══════════════════════════════════════════════│
│               │                                              │
│  Layer 2: Provider 层 (LLM 提供者)                            │
│  ┌────────────▼──────────────────────────────────────────┐   │
│  │  ┌────────┐ ┌─────────┐ ┌────────┐ ┌──────────────┐  │   │
│  │  │ OpenAI │ │Anthropic│ │DeepSeek│ │  Ollama/...  │  │   │
│  │  └────────┘ └─────────┘ └────────┘ └──────────────┘  │   │
│  └───────────────────────────────────────────────────────┘   │
│               │                                              │
│═══════════════╪══════════════════════════════════════════════│
│               │                                              │
│  Layer 1: Tool 层 (工具执行)                                  │
│  ┌────────────▼──────────────────────────────────────────┐   │
│  │  ┌───────────────┐  ┌──────────────────────────────┐  │   │
│  │  │  Built-in Tools│  │       MCP Tools              │  │   │
│  │  │  ·MessageTool  │  │  ·MCPToolWrapper             │  │   │
│  │  │  ·SpawnTool    │  │  ·mcp_{server}_{tool}        │  │   │
│  │  │  ·save_memory  │  │  ·远程/本地 MCP Server       │  │   │
│  │  └───────────────┘  └──────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 各层职责说明

| 层次 | 名称 | 核心职责 | 关键组件 |
|------|------|----------|----------|
| **Layer 5** | UI 层 | 面向用户的交互界面 | Telegram/Discord/飞书/钉钉/微信等 Channel 适配器 |
| **Layer 4** | Gateway 层 | 消息的统一收发 | MessageBus（双队列）、ChannelManager |
| **Layer 3** | Core Agent 层 | 核心推理和决策 | AgentLoop、AgentRunner、ContextBuilder、MemoryStore、SubagentManager |
| **Layer 2** | Provider 层 | LLM 调用封装 | OpenAI/Anthropic/DeepSeek 等 Provider |
| **Layer 1** | Tool 层 | 工具注册与执行 | ToolRegistry、MCPToolWrapper、内置工具 |

### 架构设计原则

Nanobot 的架构遵循以下核心原则：

**1. 关注点分离（Separation of Concerns）**

每一层只负责自己的职责，层与层之间通过明确的接口交互。Channel 不需要知道 AgentLoop 的实现细节，AgentLoop 不需要知道消息来自哪个平台。

**2. 依赖倒置（Dependency Inversion）**

高层模块不依赖低层模块的具体实现，而是依赖抽象接口。例如 AgentRunner 不直接依赖 OpenAI SDK，而是通过 Provider 抽象层调用 LLM。

**3. 单一职责（Single Responsibility）**

每个类只负责一件事：AgentLoop 负责消息消费和会话管理，AgentRunner 负责 ReAct 循环，ContextBuilder 负责构建 prompt，MemoryStore 负责记忆读写。

---

![Nanobot 架构漫画](../../comics/02-nanobot-architecture.png)

*Nanobot 四大核心模块：AgentLoop（核心引擎）、ToolRegistry（工具注册表）、MEMORY.md（长期记忆）、SkillLoader（技能加载器）*

## 3.2 四大核心模块详解

原版这里把 AgentLoop、AgentRunner、MemoryStore、MessageBus 视为“四大核心模块”。这些名字仍然重要，但 current-source 的职责已经发生明显演进。

### 3.2.1 AgentLoop —— 面向用户 Turn 的编排层

`nanobot/agent/loop.py` 当前负责：

- InboundMessage 的 Session admission
- per-session pending queue / FIFO
- TurnContext
- restore → compact → command → build → run → save → respond
- ModelRuntimeResolver
- ContextBuilder / SessionManager 协作
- Workspace Scope
- TurnDelivery
- Subagent / AutoCompact / CommandRouter 的协调

它不再等于“整个 ReAct 执行器”。

### 3.2.2 AgentRunner —— 面向模型的 Provider/Tool Loop

`nanobot/agent/runner.py` 的定位是：

> Run a tool-capable LLM loop without product-layer concerns.

它接收 `AgentRunSpec`，负责：

```
provider call
→ assistant response
→ tool calls?
→ ToolRegistry execution
→ Tool Result
→ next provider call
→ final answer / limit / error
```

并处理 streaming、hooks、provider state、compaction、follow-up injection、checkpoint 等执行语义。

### 3.2.3 Session / Memory —— 多层状态系统

current-source 不再是单纯 `MEMORY.md + HISTORY.md`：

```
Session JSONL
  ↓
AutoCompact / Consolidator
  ↓
memory/history.jsonl
  ↓
Dream
  ↓
SOUL.md / USER.md / memory/MEMORY.md
```

`HISTORY.md` 主要用于 legacy migration。

### 3.2.4 MessageBus —— 双队列 + Typed Event Dispatch

MessageBus 仍然持有：

```
inbound: Queue[InboundMessage]
outbound: Queue[OutboundMessage]
```

同时 current-source 还支持 local typed event subscriber：

- `publish()`：按注册顺序 await 本地 subscriber
- `publish_event()`：将 typed event 转为 routed outbound delivery
- local state transition 不需要等待网络发送

因此今天更准确的描述是“消息双队列 + typed runtime event dispatch”，而不只是简单的生产者/消费者队列。

## 3.3 数据流图

### 完整消息处理流程

```
Chat App / CLI / WebUI
       │
       ▼
InboundMessage
       │
       ▼
MessageBus.inbound
       │
       ▼
AgentLoop.run()
       │
       ├── effective session key
       ├── per-session pending queue
       └── _dispatch_one()
                │
                ▼
          _process_message()
                │
                ▼
          TurnContext
                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼
   restore   compact   command
                          │
                          ▼
                        build
                          │
                 TranscriptInput
                          │
                          ▼
                    AgentRunSpec
                          │
                          ▼
                     AgentRunner
                    ↙           ↘
               Provider       ToolRegistry
                    ↖           ↙
                      Tool Result
                          │
                          ▼
                    AgentRunResult
                          │
                    save → respond
                          │
                          ▼
                 TurnDelivery / Bus
                          │
                          ▼
                       Channel
```

### 关键边界

- Channel 只做平台协议 ↔ Inbound/OutboundMessage 适配。
- AgentLoop 负责一个 Session-facing Turn。
- AgentRunner 负责一个 model-facing execution loop。
- ContextBuilder 决定模型本轮看到什么。
- ToolRegistry 统一 Native/MCP/Plugin Tool 的运行时接口。
- SessionManager 管 conversation persistence。
- Memory/Dream 管跨更长时间的 durable knowledge。

## 3.4 模块间的协作关系

### 依赖关系图

```
Application Composition Root
├── MessageBus
├── ToolRegistry
├── MCPProvider ────────────┐
├── Provider                │ dynamic MCP tools
├── CronService             ▼
└── AgentLoop ─────────→ ToolRegistry
     ├── ContextBuilder
     ├── SessionManager
     ├── ModelRuntimeResolver
     ├── AgentRunner
     ├── Consolidator
     ├── SubagentManager
     ├── AutoCompact
     └── CommandRouter
```

### 创建顺序为什么重要

current-source 的 `AgentLoop.from_config(..., tool_registry=...)` 明确要求 caller-owned ToolRegistry。这样 CLI、Gateway、SDK 等入口可以：

1. 创建共享 ToolRegistry；
2. 创建 MCPProvider 并让它向 Registry 动态注册能力；
3. 创建 AgentLoop；
4. 启动 MCP / Channel / Gateway 等 application-owned infrastructure；
5. shutdown 时由同一 owner 关闭资源。

这是典型 Composition Root，而不是让 AgentLoop 随意 new 所有依赖。

## 3.5 关键设计模式

### 模式 1：异步消息总线 / 生产者-消费者

Channel 向 inbound queue 发布，Core 向 outbound queue 发布；平台 SDK 与 Agent Core 解耦。

### 模式 2：Registry / Discovery

Provider、Tool、Channel 都尽量通过 Registry/Discovery 管理，而不是在核心逻辑里写长 if/elif。

### 模式 3：Strategy / Adapter

不同 Provider、Channel、MCP Tool 共享高层 contract，但保留各自实现。

### 模式 4：Composition Root

共享 ToolRegistry、MCPProvider、CronService 等 infrastructure 在 CLI/Gateway/SDK 启动层组装。

### 模式 5：Pipeline

current Turn 明确分为：

```
restore → compact → command → build → run → save → respond
```

每个 stage 有单独 timing/error boundary。

### 模式 6：Context Object

`TurnContext` 集中保存一次 Turn 的共享状态，避免跨阶段传递大量独立参数。

### 模式 7：Workspace / Project Scope

Agent-owned state 与 effective project workspace 分离：

- SOUL/USER/Memory/Custom Skills 属于 Agent Workspace
- Project AGENTS/relative files/shell cwd 属于 Effective Project

### 模式 8：Progressive Disclosure

Skills 先提供 name/description/path summary，需要时再加载完整 SKILL.md，减少 Context Bloat。

### 模式 9：Per-session FIFO + Optional Global Concurrency Gate

current-source 通过 `_pending_queues[session_key]` 为每个 Session 建单 worker，保持 FIFO；同时可用 `NANOBOT_MAX_CONCURRENT_REQUESTS` 设置全局并发上限。未设置或 ≤0 表示 Nanobot 不主动加全局 Semaphore。

### 模式 10：Checkpoint / Recovery

长 Turn 在 Provider/Tool execution 中产生 checkpoint，异常或进程恢复时可以安全处理未完成状态，而不是把所有失败都当成“重新问一遍”。

### 模式 11：Model-facing Contract

Tool Name、Schema、Error Message、Runtime Context 都是模型契约。修改这些表面行为可能改变模型决策，不能只当普通内部重构。

## 3.6 架构对比

### Nanobot vs LangChain 架构对比

| 维度 | Nanobot | LangChain |
|------|---------|-----------|
| **核心抽象** | MessageBus + AgentLoop | Chain + Agent + Memory + Tool |
| **编排方式** | LLM 自主决策（隐式） | LangGraph 显式编排 / AgentExecutor |
| **消息传递** | 双队列 MessageBus | Callback 机制 |
| **工具注册** | ToolRegistry + MCPToolWrapper | BaseTool + Toolkit |
| **配置方式** | JSON / WebUI 文件 | Python 代码 |
| **记忆实现** | MEMORY.md + HISTORY.md | ConversationBufferMemory / VectorStoreMemory 等 |
| **抽象层级** | 2-3 层 | 5-7 层 |
| **源码可读性** | 高（4K行，架构清晰） | 低（50万行+，抽象层多） |

**关键差异**：

```
LangChain 的做法：
  用户请求 → Prompt Template → Chain → Agent → Tool → Output Parser → Memory
                ↑ 每一步都有抽象层

Nanobot 的做法：
  用户消息 → MessageBus → AgentRunner(LLM + Tools 循环) → 响应
                ↑ 最小必要抽象
```

### Nanobot vs CrewAI 架构对比

| 维度 | Nanobot | CrewAI |
|------|---------|--------|
| **Agent 模型** | 单 Agent + SubAgent | 多 Agent 角色 |
| **任务分配** | LLM 自主决定 | 用户预定义角色和任务 |
| **协作方式** | SubAgent 后台并行 | Agent 间消息传递 |
| **适用场景** | 个人助手 | 团队协作模拟 |

---

## 3.7 面试高频题

### Q1: 请描述 Nanobot 的架构设计

> current-source 可以分为 Surface/Channel、MessageBus、AgentLoop、AgentRunner/Provider/Tools、Session/Memory 五类责任。AgentLoop 负责 Session-facing Turn，AgentRunner 负责 model-facing Provider/Tool Loop；ContextBuilder 和 SessionManager 分别负责“模型这轮看到什么”和“Conversation 如何持久化”。

### Q2: 为什么 AgentLoop 和 AgentRunner 要拆开？

> 两者变化原因不同。Loop 随 Channel、Session、Workspace、Command、Delivery 等产品需求变化；Runner 随 Provider、Tool、Streaming、Compaction 等执行语义变化。拆开后 Subagent 等场景也可以复用 Runner。

### Q3: MessageBus 现在还是双队列吗？

> 是，current `MessageBus` 仍有 inbound/outbound Queue；但还增加 typed local event subscriber，`publish` 用于本地状态 fan-out，`publish_event` 复用 outbound delivery，所以“只有双队列”已经不完整。

### Q4: 会话并发怎么控制？

> 同 Session 使用 pending queue + single worker 保持 FIFO，并配合 Session Lock；全局请求并发由 `NANOBOT_MAX_CONCURRENT_REQUESTS` 可选控制，默认未设置时不加全局 cap；Subagent 又有独立 `maxConcurrentSubagents`。

### Q5: 旧版 save_memory / HISTORY.md 现在是什么状态？

> current 主路径已经变成 Session → AutoCompact/Consolidation → history.jsonl → Dream → SOUL/USER/MEMORY。HISTORY.md 主要保留 legacy migration；不应再把 save_memory 虚拟工具作为新版记忆架构核心。

## 3.8 本章总结

```
┌─────────────────────────────────────────────────────┐
│                   本章核心要点                        │
│                                                     │
│  五层架构                                            │
│  ├── UI 层 → Channel 适配器                          │
│  ├── Gateway 层 → MessageBus 双队列                  │
│  ├── Core Agent 层 → AgentLoop + AgentRunner         │
│  ├── Provider 层 → LLM 供应商抽象                    │
│  └── Tool 层 → ToolRegistry + MCPToolWrapper         │
│                                                     │
│  四大核心模块                                        │
│  ├── AgentLoop → 消息消费 + 会话管理                  │
│  ├── AgentRunner → ReAct 循环执行                    │
│  ├── MemoryStore → 双层记忆管理                      │
│  └── MessageBus → 异步消息传递                       │
│                                                     │
│  10 个设计模式                                       │
│  ├── 生产者-消费者、注册表、适配器                     │
│  ├── 包装器、配置驱动、Workspace中心                  │
│  ├── 渐进披露、虚拟工具                              │
│  └── 会话并发控制、Prompt Cache                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 下一章

理解了架构设计之后，接下来我们将深入源码，逐文件、逐函数地解读 Nanobot 的核心实现。

➡️ [04 - 源码逐行解读](../04-source-code-walkthrough/README.md)

---

> 📝 **本章小结**：Nanobot 的架构设计是"极简但不简单"。五层架构清晰分离了关注点，四大核心模块各司其职，10 个经典设计模式保证了代码的扩展性和可维护性。理解这些架构设计，你就掌握了面试中最有深度的技术素材。
