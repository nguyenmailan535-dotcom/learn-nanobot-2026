# 04 - Nanobot 源码逐文件走读

> **阅读时间**：约 4 小时  
> **前置知识**：[03 - 架构深入解析](../03-runtime-architecture/README.md)  
> **学习目标**：沿着原版 learn-nanobot 的“逐文件走读”结构，以 **2026-09-24 HKUDS/nanobot main** 为准，读懂 AgentLoop、AgentRunner、ContextBuilder、Memory、Subagent、Tool、MessageBus、Channel 与 Config 的真实职责。

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

原版教程的阅读方法仍然正确：**不要从第一行一路读到最后一行，而是先抓核心文件，再沿调用链扩散。**

2026-09-24 建议优先看：

```text
nanobot/
├── agent/
│   ├── loop.py                 # 面向 Channel/Session 的 Turn 编排
│   ├── runner.py               # 面向模型的 Provider/Tool Loop
│   ├── context.py              # Prompt / Transcript 构建
│   ├── memory.py               # MemoryStore / Consolidator / Dream
│   ├── autocompact.py          # idle Session 压缩
│   ├── subagent.py             # 子 Agent 生命周期
│   ├── model_runtime.py        # Runtime / Preset 解析
│   ├── turn_delivery.py        # Turn 输出和交付
│   └── tools/
│       ├── base.py
│       ├── schema.py
│       ├── registry.py
│       ├── loader.py
│       ├── filesystem.py
│       ├── shell.py
│       ├── web.py
│       ├── mcp.py
│       ├── cron.py
│       └── ...
├── bus/
│   ├── events.py
│   ├── queue.py
│   └── outbound_events.py
├── session/
│   ├── manager.py
│   ├── summary.py
│   ├── recovery.py
│   └── ...
├── channels/
│   ├── base.py
│   ├── manager.py
│   └── <channel-package>/
├── providers/
│   ├── base.py
│   ├── registry.py
│   └── ...
├── config/
│   ├── schema.py
│   ├── loader.py
│   └── paths.py
├── cron/
├── triggers/
├── security/
└── cli/
```

### 推荐阅读顺序

```text
events.py
  ↓
queue.py
  ↓
loop.py
  ↓
context.py
  ↓
runner.py
  ↓
tools/registry.py
  ↓
session/manager.py
  ↓
memory.py
  ↓
subagent.py / mcp.py / channels/
```

> 💡 **源码阅读原则**：每次只回答一个问题，例如“第一次进入 AgentRunner 前 messages 如何生成？”而不是“解释整个 loop.py”。

---

## 4.2 AgentLoop - loop.py

### 文件定位

```text
nanobot/agent/loop.py
```

### 核心类：AgentLoop

旧版教程把 AgentLoop 描述为“核心推理引擎”。current-source 更准确的说法是：

> **AgentLoop 是 channel-facing Turn Orchestrator。**

它负责的不是所有模型循环细节，而是把一个外部消息变成一次完整、可恢复、可持久化的 Turn。

### 构造函数参数详解

current-source 的 AgentLoop 会协调：

- `MessageBus`
- `LLMProvider`
- `ModelRuntimeResolver`
- `ContextBuilder`
- `SessionManager`
- `ToolRegistry`
- `AgentRunner`
- `Consolidator`
- `SubagentManager`
- `AutoCompact`
- `WorkspaceScopeResolver`
- `CronService` / Local Trigger Store
- Turn hooks / delivery

其中一个特别重要的 current 设计是：

```python
AgentLoop.from_config(..., *, tool_registry: ToolRegistry)
```

`ToolRegistry` 由调用方拥有。这样 application composition root 可以把同一个 Registry 同时交给 AgentLoop 和 MCPProvider。

### run() 方法：核心消费循环

概念链：

```text
MessageBus.consume_inbound()
        ↓
runtime-control / priority command
        ↓
effective session key
        ↓
_enqueue_session_message()
        ↓
每个 Session 一个 pending queue + worker
        ↓
_dispatch_one()
        ↓
_process_message()
```

current-source 不再是旧版“每条消息 create_task + 一个固定全局 Semaphore”。

#### 同 Session FIFO

```text
_pending_queues[session_key]
```

已经存在时，新消息进入相同队列。

独立 Turn 保持 FIFO；允许注入的 follow-up 可以在 Runner 迭代边界被消费。

#### 全局并发

```python
_max = int(os.environ.get("NANOBOT_MAX_CONCURRENT_REQUESTS", "0"))
```

- `_max <= 0`：不增加全局 Semaphore；
- `_max > 0`：创建 `asyncio.Semaphore(_max)`。

### _process_message()：七阶段 Turn Pipeline

这是 current-source 最值得掌握的一段：

```text
restore
→ compact
→ command
→ build
→ run
→ save
→ respond
```

`TurnContext` 在这些阶段之间共享状态，包括：

```text
msg
session_key
turn_id
runtime
session
history
transcript_input
request_context
runtime_context_blocks
provider_state
final_content
stop_reason
usage
pending_queue
tools
```

每个阶段还通过 `_run_turn_stage` 记录 duration/outcome。

### _register_default_tools() 方法

current-source 不在 AgentLoop 里手写一个工具列表。

概念上：

```text
ToolContext(
  config,
  workspace,
  bus,
  subagent_manager,
  cron_service,
  sessions,
  sandbox,
  runtime_control,
  ...
)
        ↓
ToolLoader().load(...)
        ↓
ToolRegistry
```

这使 Tool discovery 与 AgentLoop 解耦。

### _save_turn() / Persist Stage

保存逻辑的关键不是“把 Runner messages 全 append”。

Runner 返回的 messages 里包含已有历史，如果全量保存会重复。

因此 current code 会维护：

- save boundary
- early-persisted user input
- hidden/runtime metadata
- provider state
- summary checkpoint

### 面试要点

1. AgentLoop 是 Turn Orchestrator，不是 Provider/Tool Loop 本身；
2. 同 Session 使用 queue/worker 保证 FIFO；
3. 全局并发是可选环境配置；
4. MCP 生命周期不属于 AgentLoop；
5. Turn 被拆成可观测的七阶段 Pipeline。

---

## 4.3 AgentRunner - runner.py

### 文件定位

```text
nanobot/agent/runner.py
```

### 核心类：AgentRunner

类注释可以直接作为面试定义：

> Run a tool-capable LLM loop without product-layer concerns.

也就是：

> 它只管一次 Model/Tool Execution，不管 Telegram、WebUI、Session 页面之类产品层逻辑。

### run() 方法：ReAct 循环核心

入口大致是：

```text
AgentRunner.run(AgentRunSpec)
        ↓
_initial_transcript_and_compaction
        ↓
hook.before_run
        ↓
_run_core
        ↓
AgentRunResult
        ↓
hook.after_run / on_error / on_finally
```

### AgentRunSpec

current Run Contract 包含：

```text
tools
runtime
max_iterations
max_tool_result_chars
transcript_input
transcript_builder
hook
concurrent_tools
workspace
session_key
checkpoint_callback
consolidate_history
consolidate_provider_compaction
injection_callback
terminal_injection_callback
continuation_callback
provider_state
events
```

这比旧版“runner.run(messages, tools)”更接近真实 production execution。

### Tool 执行

current-source 中不要再寻找“`_execute_tool()` 拦截 `save_memory`”这个旧逻辑。

现在 Tool execution 通过 Registry / Execution helper 统一执行，长期记忆由 Consolidator + Dream 管理。

核心闭环：

```text
Provider Response
├── 没有 Tool Call → Final
└── Tool Calls
      ↓
   validate / execute
      ↓
   Tool Result
      ↓
   context governance
      ↓
   append to transcript
      ↓
   next Provider call
```

### Lifecycle Hooks 详解

Runner 支持：

- `before_run`
- `after_run`
- `on_error`
- `on_finally`

Loop 还会把 Turn Events / streaming hooks 组装进来。

### 关键设计决策

#### 1. Tool Result 上限是配置，不是固定私有常量

current default：

```text
agents.defaults.maxToolResultChars = 16000
```

Tool Result governance 会截断或 spill，防止 Observation 把 Context 撑爆。

#### 2. maxToolIterations 当前默认 200

```text
agents.defaults.maxToolIterations = 200
```

这是可配置 Runtime 限制。

#### 3. concurrent_tools

Loop 构造 RunSpec 时 current-source 使用：

```python
concurrent_tools=True
```

模型一次返回多个 Tool Call 时可以并行执行，但有写副作用的 Tool 仍需考虑 ordering。

#### 4. Follow-up Injection

Runner 可以在迭代边界从 Session pending queue 注入用户后续输入或 Subagent result，使长任务不必等整个 Turn 完成后才能观察新事件。

---

## 4.4 ContextBuilder - context.py

### 文件定位

```text
nanobot/agent/context.py
```

### 核心类：ContextBuilder

它回答的问题是：

> **这一次 Provider 调用到底看见什么？**

current-source 明确：

```python
BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md"]
```

同时 Context 还可能加入：

- Project `AGENTS.md`
- long-term memory
- Skill Summary / Active Skill
- Session Summary
- RuntimeContextBlock
- History
- Current Message / Media

### build_system_prompt() 方法

不要把它理解为简单：

```text
AGENTS + MEMORY + TOOLS
```

current source 会区分：

```text
Agent Workspace
vs
Effective Project Workspace
```

Agent-owned：

```text
SOUL.md
USER.md
memory/
workspace skills
```

Project-owned：

```text
project AGENTS.md
relative Tool paths
shell working directory
```

### build_messages() / build_transcript()

Loop 会先生成 `TranscriptInput`：

```text
history
current_message
media
session_summary
runtime_context_blocks
```

然后由 ContextBuilder 构造最终 Provider Transcript。

这种设计使：

- AutoCompact 后可以重建 Transcript；
- Provider state 可选择 resume 或 full replay；
- RuntimeContext 可以按 Turn 注入。

### Prompt Cache 优化策略解读

current tests 会验证稳定前缀不因 Project path 等动态信息无谓变化。

工程思想是：

```text
Stable Identity / Tool Contract
        ↓
尽量稳定
        ↓
Dynamic Project / Session / Current Input
```

支持 Prompt Cache 的 Provider 能因此获得更高 cache hit。

### 面试要点

> Session 是“保存了什么”，ContextBuilder 决定“这次给模型看什么”。

---

## 4.5 MemoryStore - memory.py

### 文件定位

```text
nanobot/agent/memory.py
```

### 核心类：MemoryStore

current 注释：

> Pure file I/O for memory files: MEMORY.md, history.jsonl, SOUL.md, USER.md.

当前路径：

```text
<workspace>/
├── SOUL.md
├── USER.md
└── memory/
    ├── MEMORY.md
    ├── history.jsonl
    ├── .cursor
    └── .dream_cursor
```

`HISTORY.md` 只保留 legacy migration 路径。

### read_memory() / write_memory()

`MemoryStore` 负责纯文件 I/O。

真正长期记忆的“决定写什么”不是简单 Tool Call，而由 Dream 的模型流程负责。

### append_history() 方法

history entry 会先经过治理：

- strip internal think/template leak
- bounded length
- atomic cursor allocation
- append JSONL
- optional session key

### Consolidator 压缩机制

current `Consolidator` 负责：

- Session transcript summarization
- idle compaction
- provider compaction summary
- archive into history

`AutoCompact` 会根据 idle TTL 调度它。

### Dream

Dream 再从 history archive 中整理：

```text
SOUL.md
USER.md
memory/MEMORY.md
```

并用 `GitStore` 保留可审计/恢复的版本。

---

## 4.6 SubagentManager - subagent.py

### 文件定位

```text
nanobot/agent/subagent.py
```

### 核心类：SubagentManager

Subagent 并不是“再 new 一个完整 AgentLoop”。

它直接复用：

```text
AgentRunner
AgentRunSpec
```

这正好验证 AgentLoop / AgentRunner 分层的价值。

### spawn() 方法

current `spawn` 会：

1. 生成 task id；
2. 创建 `SubagentStatus`；
3. 创建后台 task；
4. 记录 Session → Subagent 关系；
5. 执行完成后清理状态；
6. 把结果作为可注入事件回到父 Session。

current 还提供 `run_inline()`，适合需要同步获得 Subagent 结果的场景。

### Tool Scope

Subagent 使用独立 ToolRegistry scope，避免默认获得所有主 Agent capability。

其工具集由 ToolLoader 的 `scope="subagent"` 约束。

### 并发

```text
agents.defaults.maxConcurrentSubagents
```

current default 为 **4**。

Subagent 的 `max_iterations` 当前从同一 AgentDefaults / Runtime Limit 继承，而不是旧版固定 15 次。

---

## 4.7 工具系统 - tools/

### 4.7.1 ToolRegistry - registry.py

核心职责：

```text
register
get
tool_names
get_definitions
execute
runtime_context_providers
```

它统一管理模型可调用能力。

### 4.7.2 MCP - mcp.py

current-source 的中心对象是 `MCPProvider`：

```python
class MCPProvider:
    """Own configured MCP connections and their dynamic tool registrations."""
```

典型生命周期：

```text
ToolRegistry()
     ↓
MCPProvider.from_config(config, registry)
     ↓
await connect()
     ↓
发现 Server capabilities
     ↓
注册 Tool/Resource/Prompt wrappers
     ↓
AgentLoop 使用相同 Registry
     ↓
shutdown → aclose()
```

所以不要再把 MCP 描述成 AgentLoop 内部固定的 `MCPToolWrapper` 列表。

### 4.7.3 MessageTool - message.py

Message Tool 属于“显式发送/交付”能力，用于某些需要 Tool 主动发送消息或媒体的场景。

但普通 Turn 的最终回复主要通过：

```text
AgentRunResult
→ AgentLoop
→ TurnDelivery
→ Channel
```

完成。

### 4.7.4 SpawnTool - spawn.py / Subagent Tool

ToolLoader 会把 SubagentManager 能力暴露成 model-callable Tool；真正生命周期仍在 SubagentManager。

### 其他 current Tools

current-source 还包括：

- filesystem / grep / patch
- shell
- web
- cron
- image generation
- long task / sustained goal
- self/runtime inspection
- notebook editing 等

实际可见 Tool 取决于 Config、Session policy、scope、Plugin/MCP 与 Security。

---

## 4.8 MessageBus - bus/

### 核心类：MessageBus

文件：

```text
nanobot/bus/queue.py
```

它仍然承担 Channel/Core 解耦。

但 current-source 不应只记“双 Queue”。

除了 Inbound/Outbound Message，还存在 Runtime Event publication，用于：

- streaming
- reasoning
- turn status
- runtime model change
- goal state
- channel delivery

`EventSink` 和 `TurnDelivery` 把这些事件绑定到一次 Turn 的 route。

---

## 4.9 Channel 适配层 - channels/

### 基类：BaseChannel

Channel 做两件事：

```text
平台输入 → InboundMessage
Outbound/Event → 平台发送 API
```

它不应该自己实现 Agent reasoning。

### ChannelManager

current `ChannelManager` 负责：

- discovery
- start/stop lifecycle
- outbound routing
- retry
- streaming platform behavior
- hot reload/status

### Telegram 适配器示例

Telegram package 在：

```text
nanobot/channels/telegram/
```

重点不是 SDK 细节，而是观察它如何把平台 update 映射为：

```text
sender_id
chat_id
content
media
metadata
```

### 飞书适配器示例

Feishu current guide 支持 long-lived connection / connection setup，不能继续照搬旧版“必须自己部署公网 Webhook + ngrok”的教程。

### 添加新平台的正确路径

优先参考 current：

```text
docs/channel-package-guide.md
```

实现自包含 Channel Package 和 `ChannelPlugin` 描述，而不是直接改一个巨型 manager switch。

---

## 4.10 配置系统 - config/schema.py

### 配置数据类

current 使用 Pydantic Schema。

关键区域：

```text
agents.defaults
modelPresets
providers
channels
tools
gateway
transcription
...
```

AgentDefaults 当前重要默认值包括：

```text
contextWindowTokens = 200000
temperature = 0.1
maxToolIterations = 200
maxConcurrentSubagents = 4
maxToolResultChars = 16000
session TTL / idle compact
Dream
```

### 配置加载

```text
nanobot/config/loader.py
```

还负责旧 Config migration，例如：

```text
tools.exec.restrictToWorkspace
→
tools.restrictToWorkspace
```

current schema 接受 camelCase / snake_case 的兼容输入，但保存时以 current alias 为准。

---

## 4.11 关键代码片段解读

### 片段 1：完整的消息处理链路

```text
Channel
→ bus.publish_inbound
→ AgentLoop.run
→ _enqueue_session_message
→ _run_session_queue
→ _dispatch_one
→ _process_message
→ restore/compact/command/build/run/save/respond
→ AgentRunner.run
→ ToolRegistry / Provider
→ AgentRunResult
→ TurnDelivery
→ Channel
```

这是你最应该亲自用 Debugger 验证的一条链。

### 片段 2：MCP 工具注册流程

```text
Config + enabled Agent Plugins
        ↓
MCPProvider.from_config
        ↓
connect_mcp_servers
        ↓
server.list_tools/resources/prompts
        ↓
enabledTools filter
        ↓
wrap/register into shared ToolRegistry
        ↓
AgentRunner sees definitions
```

### 片段 3：Provider 注册表与工厂

```text
config / model preset
        ↓
providers.registry metadata
        ↓
providers.factory
        ↓
ProviderSnapshot / LLMRuntime
        ↓
AgentLoop admission
        ↓
AgentRunner
```

current Runtime 可以按 Session model preset 选择 Provider/Model，而不是整个进程只能有一个固定模型字符串。

---

## 4.12 面试高频题

### Q1: 请描述 AgentLoop 的执行流程

> "Channel 消息先进入 MessageBus。AgentLoop 根据 effective session key 把消息送入 per-session FIFO worker；_process_message 创建 TurnContext，然后按 restore、compact、command、build、run、save、respond 七阶段执行。build 阶段确定 Runtime、History、Workspace 和 TranscriptInput；run 阶段才交给 AgentRunner 做 Provider/Tool Loop；最后把新增消息持久化并通过 TurnDelivery 返回 Channel。"

### Q2: 旧版 save_memory 虚拟工具现在怎么了？

> "2026-09-24 current-source 不再把长期记忆描述成 AgentRunner 拦截 save_memory 写 MEMORY.md。现在短期会话由 SessionManager 管理，Consolidator/AutoCompact 负责归档，Dream 从 history.jsonl 整理 SOUL.md、USER.md 和 memory/MEMORY.md，并通过 GitStore 支持审计和恢复。"

### Q3: 为什么工具结果默认限制 16000 字符？

> "这是 Context Governance。过长 Tool Result 会挤占模型上下文、增加延迟和成本。current-source 把上限做成 agents.defaults.maxToolResultChars 配置，而不是不可改的固定常量；超大结果还可以通过 spill/reference 方式处理。"

### Q4: 如何新增一个 LLM Provider？

> "先判断 OpenAI-compatible 通用路径是否足够；如果只是兼容 API，通常添加 Provider metadata/config 即可。如果协议、鉴权或 streaming 语义特殊，再实现专用 Provider。current-source 的 Provider metadata 在 registry.py，配置字段在 config/schema.py，实例化走 factory/model runtime。"

---

## 4.13 本章总结

### 源码阅读建议

不要背类图，亲自完成下面三条 Trace：

1. **普通消息**：InboundMessage → AgentRunner → Final Answer；
2. **Tool Call**：Provider → ToolRegistry → Tool Result → Provider；
3. **第二条同 Session 消息**：pending queue → injection 或 FIFO 下一 Turn。

每条 Trace 都记录：

```text
入口
输入数据结构
关键状态
输出数据结构
下一跳
失败点
```

这样源码才会真正变成你的能力。

---

## 下一章

➡️ [05 - MCP 协议详解](../05-mcp-protocol/README.md)
