# 04 - 源码逐行解读

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

```
nanobot/
├── __init__.py
├── __main__.py                 # 入口点 → 启动 CLI
├── cli.py                      # 命令行接口
│
├── agent/                      # 核心 Agent 模块
│   ├── __init__.py
│   ├── loop.py                 # ★ AgentLoop - 消息消费和会话管理
│   ├── runner.py               # ★ AgentRunner - ReAct 循环执行器
│   ├── context.py              # ★ ContextBuilder - Prompt 构建
│   ├── memory.py               # ★ MemoryStore - 记忆系统
│   ├── subagent.py             # SubagentManager - 子 Agent 管理
│   └── tools/                  # 工具子模块
│       ├── __init__.py
│       ├── registry.py         # ★ ToolRegistry - 工具注册表
│       ├── mcp.py              # ★ MCPToolWrapper - MCP 工具包装器
│       ├── message.py          # MessageTool - 消息回复工具
│       └── spawn.py            # SpawnTool - 子 Agent 生成工具
│
├── bus/                        # 消息总线
│   ├── __init__.py
│   └── message_bus.py          # ★ MessageBus - 双队列消息总线
│
├── channels/                   # 通道适配器
│   ├── __init__.py
│   ├── base.py                 # BaseChannel - 通道基类
│   ├── telegram.py             # Telegram 适配器
│   ├── discord.py              # Discord 适配器
│   ├── feishu.py               # 飞书适配器
│   ├── dingtalk.py             # 钉钉适配器
│   ├── wechat.py               # 微信适配器
│   ├── qq.py                   # QQ 适配器
│   ├── slack.py                # Slack 适配器
│   └── web.py                  # Web 适配器
│
├── providers/                  # LLM 供应商
│   ├── __init__.py
│   ├── base.py                 # BaseProvider - 供应商基类
│   ├── openai.py               # OpenAI 适配
│   ├── anthropic.py            # Anthropic/Claude 适配
│   ├── deepseek.py             # DeepSeek 适配
│   ├── dashscope.py            # 通义千问适配
│   ├── ollama.py               # Ollama 本地模型
│   ├── groq.py                 # Groq 适配
│   └── registry.py             # PROVIDERS 注册表
│
├── config/                     # 配置管理
│   ├── __init__.py
│   ├── schema.py               # 配置数据类定义
│   └── loader.py               # YAML 配置加载
│
└── utils/                      # 工具函数
    ├── __init__.py
    ├── logging.py              # 日志
    └── helpers.py              # 通用辅助函数
```

> 标注 ★ 的文件是核心文件，面试必须掌握。

---

## 4.2 AgentLoop - loop.py

### 文件定位

```
nanobot/agent/loop.py
```

### current-source 定位

AgentLoop 是 **channel/session-facing Turn orchestration**，而不是把整个 ReAct 都包在一个类里。

构造阶段会协调：

```
ContextBuilder
SessionManager
ToolRegistry
AgentRunner
Consolidator
SubagentManager
AutoCompact
CommandRouter
WorkspaceScopeResolver
TurnDeliveryFactory
```

### run()：Session Admission

`run()` 从 `MessageBus.consume_inbound()` 取消息，计算 effective session key，然后通过：

```
_enqueue_session_message()
→ _run_session_queue()
→ _dispatch_one()
```

形成 per-session FIFO。

### _process_message()：七阶段 Pipeline

```
restore
→ compact
→ command
→ build
→ run
→ save
→ respond
```

每个阶段通过 `_run_turn_stage()` 记录 duration/outcome。

### _register_default_tools()

current-source 不是硬编码一个个 Tool，而是：

```
ToolContext(...)
→ ToolLoader().load(ctx, registry)
```

MCP Tool 的连接生命周期不在这里；MCPProvider 由应用组合层拥有，并向共享 ToolRegistry 动态注册。

### 面试要点

- AgentLoop = 一个用户 Turn 的编排层
- per-session pending queue 保证 FIFO
- TurnContext 是跨阶段共享状态对象
- global concurrency cap 来自 `NANOBOT_MAX_CONCURRENT_REQUESTS`，未设置默认不加 cap

## 4.3 AgentRunner - runner.py

### 文件定位

```
nanobot/agent/runner.py
```

### 核心类：AgentRunner

类注释强调它负责：

> tool-capable LLM loop without product-layer concerns

也就是不处理 Channel UI / Session 页面，只处理一次 model execution。

### AgentRunSpec

current Runner 通过 `AgentRunSpec` 接收：

- transcript_input / transcript_builder
- tools
- runtime
- max_iterations
- max_tool_result_chars
- hooks/events
- checkpoint callback
- consolidation callbacks
- follow-up injection callback
- provider conversation state

### run()

```
initial transcript / compaction state
→ hook.before_run
→ _run_core
→ AgentRunResult
→ after_run / on_error / on_finally
```

### Tool Loop

```
Provider
  ↓
Assistant Response
  ├─ final → stop
  └─ tool calls
       ↓
    ToolRegistry
       ↓
    Tool Results
       ↓
    append messages
       ↓
    Provider again
```

current Loop 创建 spec 时可启用 `concurrent_tools=True`，因此一轮多个独立 Tool Call 可以并发执行。

### 与旧版的差异

- 不再在 Runner 里拦截旧版 `save_memory` 虚拟工具作为长期记忆主路径。
- Tool Result 大小通过可配置的 `max_tool_result_chars` 治理，current default 可在 `AgentDefaults` / Settings 中查看，不应把实现写死成“永远 16000 常量”。
- 支持 Provider Conversation State、checkpoint、injection、streaming、compaction。

## 4.4 ContextBuilder - context.py

### 文件定位

```
nanobot/agent/context.py
```

### BOOTSTRAP_FILES

current-source：

```python
BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md"]
```

### build_system_prompt()

System Context 不是单一模板，而会组合：

- Runtime/Tool Contract
- Agent Workspace 的身份文件
- Effective Project 的 AGENTS.md
- Long-term Memory
- Always-active Skills
- Skills Summary
- Session Summary
- Runtime Context

### TranscriptInput

AgentLoop 不必提前把所有内容拼死成一个 messages list，而是先组织：

```
history
current_message
media
session_summary
runtime_context_blocks
```

Runner 通过 transcript builder 在需要时构造/重构 transcript，便于 compaction 与 provider state 兼容。

### Prompt Cache

current-source 仍会尽量保持稳定 Prompt Prefix，让经常变化的内容靠后，从而提高支持缓存的 Provider 的命中机会。

## 4.5 MemoryStore - memory.py

### 文件定位

```
nanobot/agent/memory.py
nanobot/agent/autocompact.py
nanobot/session/manager.py
```

### MemoryStore

current 注释：

```python
"""Pure file I/O for memory files: MEMORY.md, history.jsonl, SOUL.md, USER.md."""
```

管理：

```
memory/MEMORY.md
memory/history.jsonl
SOUL.md
USER.md
.cursor
.dream_cursor
legacy HISTORY.md
GitStore
```

### current Memory Pipeline

```
Session
→ AutoCompact / Consolidator
→ history.jsonl
→ Dream
→ SOUL / USER / MEMORY
→ ContextBuilder
```

`HISTORY.md` 主要用于旧数据迁移；current 不再以旧 `save_memory` 虚拟工具为核心。

### 为什么要 GitStore

Dream 是模型驱动的长期文件更新，因此 Durable Memory 需要 diff、审计与恢复，而不是“模型写了就永久信任”。

## 4.6 SubagentManager - subagent.py

### 文件定位

```
nanobot/agent/subagent.py
nanobot/agent/tools/spawn.py
```

### 核心类：SubagentManager

current SubagentManager 负责 background/inline subagent execution，并复用：

```
AgentRunner
AgentRunSpec
ToolLoader
SkillsLoader
WorkspaceScope
```

### spawn()

`spawn()` 创建 task_id/status，然后使用 `asyncio.create_task` 运行子任务；结果可通过主 Session 的 pending/injection 机制重新进入当前对话。

### current 并发约束

Subagent 的并发由：

```
agents.defaults.maxConcurrentSubagents
```

控制，current default 为 4；额外任务等待 capacity。

不要继续背“Subagent 固定 15 次迭代”。current SubagentManager 的 `max_iterations` 与 AgentLoop/runtime settings 同步。

## 4.7 工具系统 - tools/

### 4.7.1 ToolRegistry - registry.py

ToolRegistry 统一管理：

```
register
get / tool_names
get_definitions
execute
runtime context providers
```

### 4.7.2 ToolLoader - loader.py

current default Tool 通过：

```
ToolContext
→ ToolLoader
→ ToolRegistry
```

完成 discovery/构造/注册。

### 4.7.3 MCPProvider - mcp.py

MCPProvider 是 application-owned infrastructure：

```
shared ToolRegistry
   ↑             ↑
MCPProvider   AgentLoop
```

它负责 MCP connect/reconnect/close 和动态 Tool Registration；AgentRunner 无需区分 Native Tool 与 MCP Tool。

### 4.7.4 其他 current Tools

current 工具目录包括 Filesystem、Shell、Web、MCP、Cron、Image Generation、Runtime Self-inspection 等；具体可用集合由配置、Plugin、Session Policy 与 Scope 决定。

## 4.8 MessageBus - bus/

### 核心类：MessageBus

current MessageBus 仍有：

```python
self.inbound = asyncio.Queue()
self.outbound = asyncio.Queue()
```

并增加 typed event subscriber：

- `publish_inbound()` / `consume_inbound()`
- `publish_outbound()` / `consume_outbound()`
- `publish()`：本地 subscriber
- `publish_event()`：typed event → routed outbound

Channel adapters 决定如何把 typed event 投影到 Telegram/Feishu/WebSocket 等具体协议。

## 4.9 Channel 适配层 - channels/

### current 目录

```
nanobot/channels/base.py
nanobot/channels/manager.py
nanobot/channels/<channel>/
```

current Channel 使用自包含 package discovery，而不是单个集中注册表硬编码所有平台。

### BaseChannel

负责平台适配的通用 contract；具体 Runtime 把外部事件转换为 `InboundMessage`，并把 `OutboundMessage`/typed event 发送回平台。

### ChannelManager

负责 discovery、生命周期、出站 routing/retry 和 runtime status。

### Feishu current-source

Feishu current guide 使用 WebSocket Long Connection，支持 QR Login 或 App ID/App Secret；不需要旧教程里的公网 Webhook + ngrok 作为默认方案。

## 4.10 配置系统 - config/schema.py

current 配置文件默认：

```
~/.nanobot/config.json
```

schema 支持 camelCase / snake_case 输入，但保存时使用 camelCase aliases。

关键区域：

- `providers`
- `modelPresets`
- `agents.defaults`
- `tools`
- `channels`
- `gateway`
- API / transcription / image generation 等可选模块

current loader 还包含旧配置迁移，例如旧 `tools.exec.restrictToWorkspace` 会迁移到 `tools.restrictToWorkspace`。

## 4.11 关键代码片段解读

### 片段 1：真实 Turn Pipeline

```python
await self._run_turn_stage(ctx, "restore", self._restore_turn)
await self._run_turn_stage(ctx, "compact", self._compact_session)
if await self._run_turn_stage(ctx, "command", self._dispatch_command):
    return ctx.outbound
await self._run_turn_stage(ctx, "build", self._build_turn)
await self._run_turn_stage(ctx, "run", self._run_turn)
await self._run_turn_stage(ctx, "save", self._persist_turn)
await self._run_turn_stage(ctx, "respond", self._prepare_outbound)
```

### 片段 2：共享 ToolRegistry + MCP

```
Composition Root
├── tools = ToolRegistry()
├── mcp = MCPProvider.from_config(config, tools)
├── await mcp.connect()
└── AgentLoop.from_config(config, tool_registry=tools)
```

### 片段 3：全局并发

```python
_max = int(os.environ.get("NANOBOT_MAX_CONCURRENT_REQUESTS", "0"))
gate = asyncio.Semaphore(_max) if _max > 0 else None
```

这与旧版固定 `Semaphore(3)` 不同。

## 4.12 面试高频题

### Q1: 请描述 AgentLoop 的执行流程

> 从 MessageBus 取 InboundMessage 后，先进入 per-session pending queue；single worker 保证 Session FIFO。_process_message 创建 TurnContext，依次执行 restore、compact、command、build、run、save、respond；run 阶段才进入 AgentRunner 的 Provider/Tool Loop。

### Q2: AgentRunner 和 AgentLoop 的区别？

> AgentLoop 面向产品层 Turn；AgentRunner 面向模型执行。Loop 管 Session/Workspace/Delivery，Runner 管 Provider/Tool/Streaming/Compaction。

### Q3: current Memory 怎么实现？

> Session JSONL 保存结构化会话；AutoCompact/Consolidator 将旧上下文归档到 history.jsonl；Dream 再整理 SOUL/USER/MEMORY；ContextBuilder 后续选择性注入。

### Q4: current MCP 怎么注册 Tool？

> Composition Root 创建 shared ToolRegistry 和 MCPProvider，MCPProvider connect 后向 Registry 动态注册；AgentLoop/Runner 使用同一 Registry。

### Q5: Tool Result 为什么需要大小治理？

> 防止单个 Observation 吞掉 Context Window、增加成本或造成 Provider 请求失败。current-source 将上限参数化为 `max_tool_result_chars`，并配合更完整的 Tool Result governance，而不是把实现理解成一个永远不变的 magic constant。

## 4.13 本章总结

```
┌──────────────────────────────────────────────────────┐
│                   核心文件速查表                       │
│                                                      │
│  文件                    │ 核心类           │ 职责    │
│  ─────────────────────────────────────────────────── │
│  agent/loop.py           │ AgentLoop        │ 消息消费│
│  agent/runner.py         │ AgentRunner      │ ReAct  │
│  agent/context.py        │ ContextBuilder   │ Prompt │
│  agent/memory.py         │ MemoryStore      │ 记忆   │
│  agent/subagent.py       │ SubagentManager  │ 子Agent│
│  agent/tools/registry.py │ ToolRegistry     │ 工具   │
│  agent/tools/mcp.py      │ MCPToolWrapper   │ MCP    │
│  bus/message_bus.py      │ MessageBus       │ 消息   │
│  channels/base.py        │ BaseChannel      │ 通道   │
│  config/schema.py        │ NanobotConfig    │ 配置   │
│                                                      │
│  总代码量：约 4000 行 Python                           │
│  核心文件：10 个                                       │
│  核心类：10 个                                         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 源码阅读建议

```
推荐阅读顺序：

1. config/schema.py     → 理解配置结构
2. bus/message_bus.py    → 理解消息传递
3. agent/loop.py         → 理解消息消费
4. agent/runner.py       → 理解 ReAct 循环（核心！）
5. agent/context.py      → 理解 Prompt 构建
6. agent/memory.py       → 理解记忆系统
7. agent/tools/          → 理解工具系统
8. channels/             → 理解平台适配
9. providers/            → 理解 LLM 封装
```

---

## 下一章

接下来，我们将深入学习 MCP 协议——AI 界的"USB-C 接口"。

➡️ [05 - MCP 协议详解](../05-mcp-protocol/README.md)

---

> 📝 **本章小结**：通过逐文件解读，我们看到 Nanobot 的 4000 行代码如何构建出一个完整的 Agent 框架。核心是 10 个文件、10 个类，每个类职责清晰。掌握这些源码细节，你就能在面试中自信地说"我通读了全部源码"，并能深入讨论任何实现细节。
