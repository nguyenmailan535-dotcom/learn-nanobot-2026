# 03 - 架构深入解析

> **2026 current-source 说明**：本章直接沿用原版 learn-nanobot 的章节结构与主体内容；凡涉及 Nanobot 具体源码、配置、路径、记忆、并发、MCP 生命周期等实现细节，均按 HKUDS/nanobot main @ 2026-09-24 (source trace snapshot around 62aa6ba6a33790a656b952ef150517bd70d6eb30) 修订。

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

沿用原版“五层”视角，但按 current-source 重新映射：

~~~text
┌─────────────────────────────────────────────────────┐
│ Layer 5：Surface                                    │
│ CLI / TUI / WebUI / Chat Apps / API / SDK          │
├─────────────────────────────────────────────────────┤
│ Layer 4：Transport & Runtime Host                   │
│ ChannelManager / MessageBus / Gateway               │
├─────────────────────────────────────────────────────┤
│ Layer 3：Turn Orchestration                         │
│ AgentLoop / TurnContext / ContextBuilder            │
├─────────────────────────────────────────────────────┤
│ Layer 2：Model Execution                            │
│ AgentRunner / Provider / ToolRegistry / MCP         │
├─────────────────────────────────────────────────────┤
│ Layer 1：State & Infrastructure                     │
│ Session / Memory / Skills / Plugins / Cron / Security│
└─────────────────────────────────────────────────────┘
~~~

### 各层职责说明

| 层 | 职责 | current-source 例子 |
|---|---|---|
| Surface | 用户和外部系统入口 | CLI、WebUI、Channels、API、SDK |
| Transport/Host | 消息路由与长期服务宿主 | MessageBus、ChannelManager、Gateway |
| Turn | 一个用户 Turn 的状态恢复、Context、Delivery | AgentLoop、TurnContext |
| Execution | LLM ↔ Tool 的循环 | AgentRunner、Provider、ToolRegistry |
| State/Infra | 持久化、扩展、安全、调度 | SessionManager、MemoryStore、MCPProvider、CronService |

### 架构设计原则

1. **Product concern 与 model execution 分离**：AgentLoop ≠ AgentRunner。
2. **统一 Tool Contract**：native/MCP/plugin capability 最终统一到 ToolRegistry。
3. **Session 与 Context 分离**：持久化状态不等于本轮模型输入。
4. **Application-owned infrastructure**：例如 MCPProvider 生命周期由 composition root 管理。
5. **Workspace scope 是安全与语义边界**。
6. **事件与 Delivery 解耦 Channel 与 Runner**。


## 3.2 四大核心模块详解

原版以四大模块讲解。current-source 仍可沿用这个结构，但具体责任需要更新。

### 3.2.1 AgentLoop（智能体循环）——Turn 编排器

current `AgentLoop` 不应再描述为“单独承担全部推理的心脏”。它主要面向 channel-facing turn，持有/协调：

~~~text
ModelRuntimeResolver
ContextBuilder
SessionManager
ToolRegistry
AgentRunner
Consolidator
SubagentManager
AutoCompact
CommandRouter
WorkspaceScopeResolver
TurnDelivery
~~~

一次普通 Turn 明确经过：

~~~text
restore
→ compact
→ command
→ build
→ run
→ save
→ respond
~~~

其中 `run` 才进入 AgentRunner。

current inbound 并发控制也不再是固定 `Semaphore(3)`。同一 Session 使用 pending queue + sole worker + session lock 保持 FIFO；可选全局 gate 由环境变量 `NANOBOT_MAX_CONCURRENT_REQUESTS` 控制，未设置/<=0 表示不主动限流。

### 3.2.2 AgentRunner（ReAct 循环）——Model/Tool 执行器

`AgentRunner` 的类级定位是：**tool-capable LLM loop without product-layer concerns**。

它消费 `AgentRunSpec`，负责：
- initial transcript / compaction state；
- provider streaming；
- tool call parsing / execution；
- concurrent tool calls；
- tool result governance；
- provider state；
- checkpoint；
- injected follow-ups；
- stop reason；
- hooks。

概念循环仍然是：

~~~text
Provider
  ↓
Assistant response
  ├─ final → stop
  └─ tool calls
       ↓
   ToolRegistry.execute
       ↓
   tool results
       ↓
   Provider again
~~~

### 3.2.3 MemoryStore（记忆系统）——Durable Memory I/O

current MemoryStore 注释明确：

~~~text
Pure file I/O for memory files:
MEMORY.md, history.jsonl, SOUL.md, USER.md
~~~

新版链路：

~~~text
Session
→ AutoCompact / Consolidator
→ memory/history.jsonl
→ Dream
→ SOUL.md / USER.md / memory/MEMORY.md
~~~

旧 `memory/history.jsonl` 只保留 legacy migration 逻辑；旧 `Dream / MemoryStore` 虚拟工具也不是 current 主路径。

### 3.2.4 MessageBus（消息总线）——Transport/Core 解耦

MessageBus 继续承担 Channel 与 Agent Core 的事件边界。

~~~text
Channel
→ InboundMessage
→ MessageBus
→ AgentLoop
→ runtime/output events
→ OutboundMessage
→ ChannelManager / Channel
~~~

current-source 还存在更多 typed runtime/output events 和 TurnDelivery，因此不要把 MessageBus 简化为“只有两个 Queue 的数据结构”；它是 Runtime Event Routing 的核心边界之一。


## 3.3 数据流图

### 完整消息处理流程

~~~text
1. Channel / WebUI 接收输入
        ↓
2. 构造 InboundMessage
        ↓
3. MessageBus.consume_inbound()
        ↓
4. AgentLoop 计算 effective session key
        ↓
5. _pending_queues[session] 做 FIFO admission
        ↓
6. _process_message() 创建 TurnContext
        ↓
7. restore / compact / command / build
        ↓
8. ContextBuilder + Session history + RuntimeContext
        ↓
9. AgentRunSpec
        ↓
10. AgentRunner
      ↔ Provider
      ↔ ToolRegistry
        ↓
11. AgentRunResult
        ↓
12. persist stage → SessionManager.save
        ↓
13. respond → TurnDelivery / OutboundMessage
        ↓
14. ChannelManager → 平台
~~~

current-source 还支持：
- active Turn 中 follow-up injection；
- Subagent completion injection；
- provider conversation state checkpoint；
- cancellation/recovery；
- streaming events。


## 3.4 模块间的协作关系

### 依赖关系图

~~~text
Composition Root
├── MessageBus
├── shared ToolRegistry
├── MCPProvider ───────────────┐
├── Provider                   │ registers dynamic tools
└── AgentLoop                  │
    ├── ContextBuilder         │
    ├── SessionManager         │
    ├── AgentRunner ◄──────────┘
    ├── Consolidator
    ├── SubagentManager
    ├── AutoCompact
    └── TurnDelivery
~~~

### 创建顺序

典型长期运行入口的思想是：

~~~text
1. load Config
2. create MessageBus
3. create shared ToolRegistry
4. create MCPProvider with shared registry
5. create Provider / AgentLoop
6. connect MCP infrastructure
7. start Channels / Cron / Gateway services
8. run AgentLoop
9. shutdown: stop runtime + aclose MCP/owned resources
~~~

重要点：

> `AgentLoop.from_config()` 要求 caller-owned ToolRegistry，就是为了让 application composition 可以与 MCPProvider 共享 registry。


## 3.5 关键设计模式

### 模式 1：异步消息总线 / 生产者-消费者模式

Channel 与 Agent Core 通过 Inbound/Outbound event contract 解耦。

### 模式 2：Registry Pattern

Provider metadata 与 Tool 都使用 Registry/Discovery 思路。模型执行层只依赖统一 contract。

### 模式 3：Strategy / Adapter

不同 Provider、Channel、MCP Tool Adapter 在统一接口下替换。

### 模式 4：Composition Root

MCPProvider、ToolRegistry、Channels、Cron 等资源在应用入口组装，避免业务对象偷偷管理全局资源生命周期。

### 模式 5：Pipeline

一次 Turn 分成：

~~~text
restore → compact → command → build → run → save → respond
~~~

每个阶段都有统一的 timing/error logging。

### 模式 6：Context Object

`TurnContext` 集中保存一次 Turn 跨阶段共享的状态。

### 模式 7：Workspace-Centric + Scoped Project Context

Agent-owned workspace 与 effective project workspace 分开，既支持多项目，又能定义文件/Shell边界。

### 模式 8：Progressive Disclosure

Skills 先注入 summary，需要时再读取 full body；显式 `$skill-name` 可形成 active runtime context。

### 模式 9：Session FIFO + Optional Global Gate

同 Session 使用 sole worker 保证顺序；全局并发限流按环境变量可选开启。

### 模式 10：Prompt / Provider State Reuse

current ContextBuilder 与 ProviderConversationState 都在尽量减少不必要的上下文重建；具体是否命中 provider cache 取决于 Provider 能力。

## 3.6 架构对比

### Nanobot vs LangChain 架构对比

| 维度 | Nanobot | LangChain |
|------|---------|-----------|
| **核心抽象** | MessageBus + AgentLoop | Chain + Agent + Memory + Tool |
| **编排方式** | LLM 自主决策（隐式） | LangGraph 显式编排 / AgentExecutor |
| **消息传递** | 双队列 MessageBus | Callback 机制 |
| **工具注册** | ToolRegistry + MCP tool adapter / wrapper | BaseTool + Toolkit |
| **配置方式** | YAML 文件 | Python 代码 |
| **记忆实现** | Session + memory/history.jsonl + Dream-managed durable memory | ConversationBufferMemory / VectorStoreMemory 等 |
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

> “current Nanobot 可以分成 Surface、Transport/Host、Turn Orchestration、Model Execution、State/Infrastructure 几层。Channel 把平台消息变成 InboundMessage，经 MessageBus 进入 AgentLoop；AgentLoop 负责 Session、Workspace、Context、Command、Persistence 和 Delivery；真正的 Provider/Tool loop 由 AgentRunner 负责。ToolRegistry 统一 native/MCP 能力，SessionManager 负责 conversation durability，Memory 则通过 Consolidation + Dream 形成长期状态。”

### Q2: Nanobot 用了哪些设计模式？

可以答：
- Adapter / Strategy；
- Registry / Discovery；
- Composition Root；
- Pipeline；
- Context Object；
- Producer-Consumer / Event-driven；
- Progressive Disclosure。

### Q3: MessageBus 为什么存在？

核心不是背“双队列”三个字，而是解释：
- Channel 与 Agent Core 解耦；
- 不同平台统一消息 contract；
- streaming/runtime events 可以沿独立 delivery path 发布；
- Core 不依赖平台 SDK。

### Q4: current 并发模型怎么设计？

> “同一 Session 有 pending queue + sole worker + lock 保证 FIFO；允许部分 follow-up 在当前 run 中注入。不同 Session 可以并发。全局并发可通过 NANOBOT_MAX_CONCURRENT_REQUESTS 设置正整数 gate，默认不主动限流；Subagent 还有独立 maxConcurrentSubagents。”

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
│  └── Tool 层 → ToolRegistry + MCP tool adapter / wrapper         │
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
