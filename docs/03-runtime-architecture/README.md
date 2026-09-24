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

以 2026-09-24 current-source 为准，可以继续沿用原版“五层”视角，但每层的职责要更新：

```
┌──────────────────────────────────────────────────────────────┐
│ Layer 5: Surface / Channel                                   │
│ CLI / TUI / WebUI / Chat Apps / API / Python SDK            │
├──────────────────────────────────────────────────────────────┤
│ Layer 4: Transport / Gateway                                 │
│ ChannelManager / MessageBus / WebSocket / Gateway services   │
├──────────────────────────────────────────────────────────────┤
│ Layer 3: Turn Runtime                                        │
│ AgentLoop / TurnContext / ContextBuilder / SessionManager    │
├──────────────────────────────────────────────────────────────┤
│ Layer 2: Model Execution                                     │
│ AgentRunner / Provider / ModelRuntimeResolver                │
├──────────────────────────────────────────────────────────────┤
│ Layer 1: Capabilities & State                                │
│ ToolRegistry / Skills / MCP / Memory / Cron / Subagent       │
└──────────────────────────────────────────────────────────────┘
```

官方 `docs/architecture.md` 给出的核心流是：

```
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
OutboundMessage
  ↓
Channel
```

### 各层职责说明

| 层 | 核心职责 | current-source 代表 |
|---|---|---|
| Surface / Channel | 平台协议适配、用户入口 | `nanobot/channels/`、WebUI、CLI、SDK |
| Transport / Gateway | 消息总线、长期服务、Channel 生命周期 | `bus/`、`channels/manager.py`、`cli/gateway_runtime.py` |
| Turn Runtime | Session、Workspace、Context、Turn pipeline | `agent/loop.py`、`agent/context.py`、`session/` |
| Model Execution | Provider/Tool Loop、Streaming、Stop Reason | `agent/runner.py`、`providers/` |
| Capabilities & State | Tool、MCP、Skill、Memory、Automation | `agent/tools/`、`agent/memory.py`、`cron/` |

### 架构设计原则

**1. 关注点分离**

- Channel 不理解模型 Provider。
- AgentRunner 不理解 Telegram/Feishu。
- MCPProvider 不由 AgentLoop 负责 connect/close。
- Session persistence 与 model execution 分开。

**2. 面向 Contract**

current-source 的关键边界包括：

```
InboundMessage / OutboundMessage
TurnContext
TranscriptInput
AgentRunSpec / AgentRunResult
Tool Schema
LLMRuntime
WorkspaceScope
```

**3. Composition Root 管理生命周期**

CLI、Gateway、SDK 负责组装共享 `ToolRegistry`、`MCPProvider`、`AgentLoop` 等基础设施，而不是让核心对象偷偷创建外部连接。

**4. 可恢复状态**

Session 不只保存聊天文本，还保存 metadata、provider state、summary/recovery 相关状态，使长期运行的 Agent 能处理取消、恢复和并发消息。

## 3.2 四大核心模块详解

> 原版教程把 MemoryStore + MEMORY/HISTORY 作为“四大模块”之一。current-source 更适合把核心 Runtime 理解为下面四组协作边界。

### 3.2.1 AgentLoop（智能体循环）——Turn 编排层

`nanobot/agent/loop.py` 负责的是**一次面向用户/Channel 的 Turn**，而不是直接承担全部 ReAct 细节。

核心职责：

- 计算 effective session key；
- 同 Session FIFO admission；
- restore Session / Recovery state；
- AutoCompact；
- command routing；
- resolve Runtime / Workspace Scope；
- build Context / RequestContext；
- 调用 AgentRunner；
- persist Turn；
- prepare/deliver Outbound。

`_process_message()` 当前明确走七阶段：

```
restore
→ compact
→ command
→ build
→ run
→ save
→ respond
```

#### 当前并发模型

同 Session 通过：

```
_pending_queues[session_key]
+ single session worker
+ session lock
```

保证独立 Turn 的 FIFO。

全局并发上限则由环境变量控制：

```
NANOBOT_MAX_CONCURRENT_REQUESTS
```

- 未设置 / 0 / 负数：Nanobot 不额外限制；
- 正整数：创建 `asyncio.Semaphore(max)`。

因此旧版“固定 `Semaphore(3)`”已经失效。

### 3.2.2 AgentRunner（ReAct 循环）——Model/Tool Execution Engine

`nanobot/agent/runner.py` 的职责是：

> Run a tool-capable LLM loop without product-layer concerns.

它接受 `AgentRunSpec`，主要处理：

```
transcript
  ↓
provider call
  ↓
assistant response
  ├─ final text → stop
  └─ tool calls
       ↓
    ToolRegistry execute
       ↓
    tool results
       ↓
    append / checkpoint / compact
       ↓
    provider again
```

current `AgentRunSpec` 还携带：

- `runtime`
- `tools`
- `max_iterations`
- `max_tool_result_chars`
- `transcript_input`
- `checkpoint_callback`
- consolidation callbacks
- injection callbacks
- provider state
- hooks / events

当前 `AgentDefaults.max_tool_iterations` 默认 **200**。Subagent 也从同一默认/运行时限制继承，而不是旧版“主 Agent 40、子 Agent 15”的固定差异。

Tool Result 的默认字符上限仍为 **16,000**，但它现在是配置项 `agents.defaults.maxToolResultChars`，并由 context governance 处理，不应描述成 Runner 里的固定私有常量。

### 3.2.3 MemoryStore（记忆系统）——Session + Archive + Dream

current Memory 不再是 `MEMORY.md + HISTORY.md` 双文件。

`MemoryStore` 管理：

```
SOUL.md
USER.md
memory/MEMORY.md
memory/history.jsonl
memory/.cursor
memory/.dream_cursor
GitStore
```

此外还有独立的：

```
SessionManager
AutoCompact
Consolidator
Dream
```

完整关系：

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

旧 `HISTORY.md` 在 current-source 中主要是 migration source，不是主运行路径。

同样，旧版“`save_memory` 虚拟工具由 AgentRunner 拦截写 MEMORY.md”的描述已经不适用；长期记忆由 Dream 整理，并通过 GitStore 提供审计/恢复能力。

### 3.2.4 MessageBus（消息总线）——Channel/Core 解耦

`nanobot/bus/queue.py` 仍然是 Channel 与 Agent Core 的关键解耦层。

入站：

```
Channel
→ InboundMessage
→ MessageBus
→ AgentLoop
```

出站和 Runtime Event 则会通过 `TurnDelivery`、MessageBus 与 ChannelManager 继续路由。

current-source 还在总线上承载：

- stream delta / stream end
- reasoning/output events
- runtime/model/goal state events
- channel delivery retry

因此 MessageBus 已不应只理解成“两条 asyncio.Queue”，而是 Agent Runtime 的事件与消息边界。

## 3.3 数据流图

### 完整消息处理流程

以一个普通用户消息为例：

```
步骤 1: Channel 接收平台消息
        ↓
步骤 2: 转成 InboundMessage
        ↓
步骤 3: MessageBus.consume_inbound()
        ↓
步骤 4: AgentLoop 计算 effective session key
        ↓
步骤 5: 进入该 Session 的 pending queue / worker
        ↓
步骤 6: TurnContext
        ↓
restore → compact → command → build
        ↓
ContextBuilder + Session + RuntimeContext
        ↓
TranscriptInput
        ↓
AgentRunSpec
        ↓
AgentRunner
   ↙ Provider ↘
 Tool Call   Final Text
   ↓
ToolRegistry / MCP / Files / Shell / Web
   ↓
Tool Result
   ↘
 AgentRunner 下一轮
        ↓
AgentRunResult
        ↓
save → SessionManager
        ↓
respond → OutboundMessage / TurnDelivery
        ↓
Channel
```

### 一个关键变化：UI History 不等于 Model History

current-source 允许 command、hidden runtime marker、summary checkpoint 等信息存在于 Session 中，但并非每一条都直接进入下一次 Provider Transcript。

这就是为什么：

```
Session persistence
≠
Current model context
```

ContextBuilder 与 Session visibility policy 负责选择真正进入模型的内容。

## 3.4 模块间的协作关系

### 依赖关系图

```
Application Composition Root
├── MessageBus
├── ToolRegistry
├── MCPProvider ─────────────┐
├── AgentLoop                │ shared registry
│   ├── ContextBuilder       │
│   ├── SessionManager       │
│   ├── AgentRunner          │
│   ├── Consolidator         │
│   ├── AutoCompact          │
│   └── SubagentManager      │
└────────────────────────────┘
```

### 创建顺序

典型 current-source 启动顺序可以抽象成：

1. 加载/迁移 Config；
2. 构造 Provider / Model Runtime；
3. 创建 MessageBus；
4. 创建共享 ToolRegistry；
5. 根据 Config/Agent Plugin 创建 MCPProvider；
6. 创建 AgentLoop，并把共享 Registry 传入；
7. 连接 MCP、启动 Gateway/Channels；
8. 启动 AgentLoop；
9. shutdown 时由 owning application 关闭 MCP/Channel/Loop 资源。

这里的重点是：

> **连接型基础设施的生命周期由应用拥有，而不是 AgentLoop 随意拥有。**

这让 CLI、Gateway、SDK 可以用不同 Composition Root 复用同一 Core。

## 3.5 关键设计模式

Nanobot current-source 仍然非常适合从设计模式角度学习，但应以真实代码边界为准。

### 模式 1：异步消息总线 / 生产者-消费者模式

Channel 将 `InboundMessage` 发布到 MessageBus；AgentLoop 消费并处理。

价值：

- 平台与 Agent Core 解耦；
- 支持多个 Channel；
- 消息/事件可以统一观测和路由。

### 模式 2：注册表模式（Registry Pattern）

`ToolRegistry`、Provider Registry、Channel discovery 都体现了 Registry/Discovery。

ToolRegistry 统一：

- Tool Name；
- JSON Schema；
- execute；
- runtime context provider。

### 模式 3：策略/适配器模式（Strategy/Adapter Pattern）

Provider 与 Channel 都通过共同 Contract 隔离具体实现。

AgentRunner 面向 Provider Contract，不直接依赖某一家 SDK。

### 模式 4：包装器模式（Wrapper/Decorator Pattern）

MCP capability 会被包装成 Nanobot 可理解的 Tool/Resource/Prompt adapter，再注册到共享 Runtime。

重要的是 Adapter Contract，而不是旧版固定类名 `MCPToolWrapper`。

### 模式 5：配置驱动组装（Configuration-Driven Assembly）

current 配置主体是：

```
~/.nanobot/config.json
+ Pydantic schema
+ WebUI Settings
```

不是旧版教程中的 `nanobot.yml`。

Config 决定 Provider、Model Preset、Channel、MCP、Tool Security、Gateway 等运行参数。

### 模式 6：Workspace 为中心

current-source 进一步区分：

```
Agent Workspace
vs
Effective Project Workspace
```

Agent Workspace 拥有 SOUL/USER/Memory/Skills；Project Workspace 决定项目 AGENTS、相对文件路径和 Shell Working Directory。

### 模式 7：渐进披露（Progressive Disclosure）

Skills 默认先暴露 Metadata Summary，需要时再加载 Full SKILL Body，减少 Context Bloat。

### 模式 8：Composition Root + Explicit Lifecycle

这是 current-source 相比旧版非常值得强调的模式。

例如 MCP：

```
Composition Root
→ MCPProvider.connect()
→ register into shared ToolRegistry
→ AgentLoop uses registry
→ shutdown → MCPProvider.aclose()
```

### 模式 9：会话并发控制

同一 Session：

```
pending queue
+ sole worker
+ lock
```

不同 Session 可以并行。

可选全局上限：

```
NANOBOT_MAX_CONCURRENT_REQUESTS
```

Subagent 还有独立的 `maxConcurrentSubagents`。

### 模式 10：Prompt Cache / Stable Prefix

ContextBuilder 会尽量让稳定 identity/tool contract 位于可复用前缀，动态 project/session 部分放在后面，减少支持 Prompt Cache 的 Provider 上的重复计算。

重点不是“缓存整个 Prompt”，而是**控制 Prompt 结构的稳定性**。

## 3.6 架构对比

### Nanobot vs LangChain 架构对比

| 维度 | Nanobot current-source | LangChain / LangGraph 生态 |
|---|---|---|
| 核心 Runtime | AgentLoop + AgentRunner | Runnable / Graph / Agent abstraction |
| 状态 | Session + Workspace + Dream | Checkpoint/Memory 取决于选型 |
| Tool | ToolRegistry + MCP/Plugins | Tool / Toolkit / MCP adapters |
| Workflow | Model-driven Tool Loop + Automations | Graph/Workflow 表达能力更强 |
| Channel | 内置多平台 Channel Runtime | 通常由应用自己集成 |
| 自托管 UI/Gateway | 内置 | 取决于应用 |
| 学习方式 | 适合沿源码追一条完整 Runtime | 适合学习大型生态和显式 Graph |

**不要得出“谁更高级”**。二者设计目标和抽象层级不同。

### Nanobot vs CrewAI 架构对比

CrewAI 更强调 Role/Task/Crew 的多 Agent 编排；Nanobot current-source 更像一个长期运行的 personal Agent Runtime，核心是 Session、Tools、Channels、Memory、Automations 与 self-hosted Gateway。

选择取决于问题：

- 固定角色协作流程：Crew/Graph 类框架可能更直接；
- 长期个人 Agent + 多 Channel + Tools + Memory：Nanobot 这类 Runtime 更自然。

## 3.7 面试高频题

### Q1: 请描述 Nanobot 的架构设计

> "我基于 2026-09-24 current-source 理解 Nanobot。外部平台通过 Channel 转成 InboundMessage 进入 MessageBus；AgentLoop 负责一次 Turn 的 Session、Workspace、Context 与七阶段 pipeline；build 阶段构造 TranscriptInput，run 阶段把 AgentRunSpec 交给 AgentRunner。AgentRunner 只负责 Provider/Tool Loop，通过 ToolRegistry 执行 native/MCP Tool。结果回到 AgentLoop 后持久化 Session 并经 TurnDelivery 发回 Channel。长期状态再由 AutoCompact、Consolidator 和 Dream 维护。"

### Q2: Nanobot 用了哪些设计模式？

可以回答：

1. MessageBus：生产者-消费者 / Event-driven；
2. Provider/Channel：Adapter / Strategy；
3. Tool/Provider：Registry / Discovery；
4. Turn：Pipeline + Context Object；
5. MCP：Composition Root + Adapter；
6. Skill：Progressive Disclosure；
7. Session worker：Actor-like per-session serialization。

### Q3: MessageBus 为什么不用 Channel 直接调用 AgentLoop？

核心是隔离平台协议与 Agent Core，使多个 Channel 共享同一 Runtime，并为 streaming/runtime events、retry、routing 提供统一边界。

### Q4: 会话串行与全局并发限制有什么区别？

> 同 Session FIFO 是正确性约束，防止 conversation state 乱序；`NANOBOT_MAX_CONCURRENT_REQUESTS` 是资源治理约束，限制不同 Session 同时运行的数量。前者必须保证语义一致，后者可以按部署资源调整。

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
