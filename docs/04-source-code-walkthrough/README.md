# 04 - Current-source 源码走读：沿一条真实 Turn 跟到底

> 🎯 **本章目标**：不再“浏览源码”，而是能从 InboundMessage 追到 Context、AgentRunSpec、Tool Call、Session Save、OutboundMessage，并解释每个关键数据结构为什么存在。  
> **推荐方式**：VS Code / PyCharm + rg + Codex，只追一条链，一轮只解决一个问题。

---

## 目录

- [4.1 正确的源码阅读方法](#41-正确的源码阅读方法)
- [4.2 Current-source 目录地图](#42-current-source-目录地图)
- [4.3 Step 1：InboundMessage](#43-step-1inboundmessage)
- [4.4 Step 2：MessageBus 与 Session Admission](#44-step-2messagebus-与-session-admission)
- [4.5 Step 3：TurnContext 与七阶段 Pipeline](#45-step-3turncontext-与七阶段-pipeline)
- [4.6 Step 4：restore](#46-step-4restore)
- [4.7 Step 5：compact / command](#47-step-5compact--command)
- [4.8 Step 6：build](#48-step-6build)
- [4.9 Step 7：ContextBuilder](#49-step-7contextbuilder)
- [4.10 Step 8：AgentRunSpec](#410-step-8agentrunspec)
- [4.11 Step 9：AgentRunner Tool Loop](#411-step-9agentrunner-tool-loop)
- [4.12 Step 10：ToolRegistry](#412-step-10toolregistry)
- [4.13 Step 11：save / respond](#413-step-11save--respond)
- [4.14 Subagent 为什么能复用 Runner](#414-subagent-为什么能复用-runner)
- [4.15 Memory 代码告诉我们旧教程哪里失效](#415-memory-代码告诉我们旧教程哪里失效)
- [4.16 断点与最小实验](#416-断点与最小实验)
- [4.17 给 Codex 的源码追踪 Prompt](#417-给-codex-的源码追踪-prompt)
- [4.18 面试高频题](#418-面试高频题)
- [4.19 本章总结](#419-本章总结)

---

## 4.1 正确的源码阅读方法

不要这样：

~~~text
打开 loop.py
从第 1 行看到最后一行
↓
“好像都懂”
↓
第二天全忘
~~~

应该这样：

> 提出一个具体问题，只追一条调用链。

本章统一使用：

~~~text
用户发送：
"Read README.md and summarize it"
~~~

只追：

~~~text
消息怎么进来
→ 模型怎么拿到 context
→ read_file 怎么被调用
→ Tool Result 怎么回模型
→ final answer 怎么保存并返回
~~~

### 4.1.1 每次源码笔记固定五项

~~~text
入口：
输入：
关键状态：
输出：
下一跳：
~~~

再加一个：

> 为什么这个逻辑属于这一层，而不是另一层？

这能防止只记类名。

---

## 4.2 Current-source 目录地图

本章重点：

~~~text
nanobot/
├── bus/
│   ├── events.py
│   └── queue.py
├── agent/
│   ├── loop.py
│   ├── runner.py
│   ├── context.py
│   ├── autocompact.py
│   ├── memory.py
│   ├── subagent.py
│   └── tools/
│       ├── base.py
│       ├── schema.py
│       ├── registry.py
│       ├── loader.py
│       └── filesystem.py
└── session/
    └── manager.py
~~~

同时看：

~~~text
tests/agent/
tests/tools/
tests/session/
~~~

**Test 往往比注释更接近真实 contract。**

---

## 4.3 Step 1：InboundMessage

文件：

~~~text
nanobot/bus/events.py
~~~

InboundMessage 是所有 Channel 进入 Core 的统一格式。

为什么它重要？

因为 AgentLoop 后面只需要理解：

~~~text
channel
sender
chat
content
media
metadata
session key
~~~

而不需要理解 Telegram/Feishu SDK 的所有对象。

### 自己定位

~~~bash
rg "InboundMessage\(" nanobot/channels
~~~

选一个 Channel，观察：

~~~text
platform event
→ parse user/chat/content
→ InboundMessage
→ MessageBus
~~~

---

## 4.4 Step 2：MessageBus 与 Session Admission

文件：

~~~text
nanobot/bus/queue.py
nanobot/agent/loop.py
~~~

AgentLoop.run 会持续：

~~~python
msg = await self.bus.consume_inbound()
~~~

但 current-source 不再是“每条消息无脑 create_task”。

### Session Inbox

关键状态：

~~~text
_pending_queues: dict[session_key, asyncio.Queue]
~~~

逻辑：

~~~text
new message
   ↓
effective session key
   ↓
该 Session 是否已有 active queue?
   ├─ 有 → 放到已有 pending queue
   └─ 无 → 创建 queue + 单独 session worker
~~~

关键函数：

~~~text
_enqueue_session_message
_run_session_queue
_dispatch_one
~~~

### 为什么比一个 Lock 更复杂

第一条用户消息还没结束时，第二条可能到达。

系统需要区分：

- 能作为 mid-turn follow-up 注入的消息；
- 必须作为独立下一 Turn 执行的消息；
- priority command；
- automation turn；
- recovery turn。

所以 current-source 的 session admission 已经是一套真实的并发控制。

---

## 4.5 Step 3：TurnContext 与七阶段 Pipeline

_process_message 首先创建 TurnContext。

重要字段：

~~~text
msg
session_key
turn_id
runtime
kind
delivery
original_user_text
session
history
transcript_input
provider_state
request_context
runtime_context_blocks
final_content
all_messages
stop_reason
usage
pending_queue
tools
~~~

这是典型的 Context Object：

> 一次 Turn 有很多阶段共享状态，与其给每个函数传 20 个参数，不如集中进 TurnContext。

之后依次：

~~~text
restore
compact
command
build
run
save
respond
~~~

_run_turn_stage 还统一记录：

~~~text
stage
outcome
duration_ms
~~~

这就是天然的 observability boundary。

---

## 4.6 Step 4：restore

函数：

~~~text
AgentLoop._restore_turn
~~~

### 1. Attachment normalization

非图片附件不会简单整份文本塞进 prompt，而是转换为 reference。

### 2. Session restore/create

概念上：

~~~python
session = self.sessions.get_or_create(ctx.session_key)
~~~

某些场景可以要求 existing session。

### 3. Session policy

如果 session 禁用了某些工具：

~~~text
原 ToolRegistry
→ 构造 restricted registry
→ 跳过 disabled tools
~~~

说明 Tool Access 可以是 Session-scoped policy。

### 4. Delivery Route / Workspace Scope

恢复用户侧 route，并为文件/Shell 工具确定有效 Project Scope。

### 5. Recovery

恢复：

~~~text
runtime checkpoint
pending interruption
~~~

这说明 Session 持久化不只是“聊天记录”。

---

## 4.7 Step 5：compact / command

### compact

~~~text
AgentLoop._compact_session
→ AutoCompact.prepare_session
~~~

如果之前 idle compaction 已完成，会拿到 pending summary。

### command

~~~text
AgentLoop._dispatch_command
→ CommandRouter
~~~

例如 /compact 并不需要调用 Provider。

命令消息可以带 _command 标记：

~~~text
UI history 中可见
≠
一定进入 LLM history
~~~

这是一个非常值得记住的工程细节。

---

## 4.8 Step 6：build

函数：

~~~text
AgentLoop._build_turn
~~~

这是“第一次进入 Runner 前”最关键的一步。

### 1. Resolve Runtime

~~~text
Session model preset
→ ModelRuntimeResolver
→ immutable LLMRuntime
~~~

### 2. Read History

~~~python
ctx.history = session.get_history(...)
~~~

### 3. Build RequestContext

包含类似：

~~~text
channel
chat_id
message_id
session_key
original_user_text
runtime
sender_id
turn_id
workspace
log_content
~~~

之后 Tool 能通过 request context 获取本 Turn 的运行环境。

### 4. Runtime Context

当前用户输入可能触发：

- 显式 Skill；
- 其他 runtime context provider。

### 5. Provider State

如果 Provider 支持恢复 conversation state，可以复用；否则重新构造完整 transcript。

---

## 4.9 Step 7：ContextBuilder

文件：

~~~text
nanobot/agent/context.py
~~~

current source 明确：

~~~python
BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md"]
~~~

但这不等于 Context 只有三个文件。

最终还可能包括：

~~~text
project AGENTS
agent profile
memory
skills summary
runtime context
session summary
history
current message
~~~

### TranscriptInput

Loop 会把：

~~~text
history
current_message
media
session_summary
runtime_context_blocks
~~~

整理成 TranscriptInput，再交给 transcript builder。

这比直接传一个已经完全拼死的 messages list 更灵活，因为 Runner 仍然可以参与 compaction/rebuild。

---

## 4.10 Step 8：AgentRunSpec

AgentLoop._run_agent_loop 最终把执行依赖塞进 AgentRunSpec：

~~~text
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
checkpoint callback
consolidation callbacks
injection callbacks
provider state
~~~

然后：

~~~python
await self.runner.run(spec)
~~~

### 为什么 AgentRunSpec 很重要

这体现一个设计思想：

> 把“这一次执行需要什么”集中成 Run Contract，而不是让 Runner 到处访问全局单例。

这非常利于测试和复用。

---

## 4.11 Step 9：AgentRunner Tool Loop

文件：

~~~text
nanobot/agent/runner.py
~~~

入口：

~~~text
AgentRunner.run
→ initial transcript / compaction
→ _run_core
~~~

核心过程仍然是：

~~~text
provider
  ↓
assistant response
  ├─ final text → stop
  └─ tool calls
       ↓
    execute tools
       ↓
    append Tool Result
       ↓
    provider again
~~~

但 current Runner 还处理：

- streaming；
- reasoning；
- provider conversation state；
- injected follow-up；
- tool result governance；
- max iterations；
- checkpoint；
- cancellation；
- hooks。

### concurrent_tools

Loop 构造 AgentRunSpec 时当前显式：

~~~python
concurrent_tools=True
~~~

所以一次响应中的多个工具可能并发执行。

面试可以进一步讨论：

> 如果 Tool 有写副作用，并发执行会带来什么 ordering 问题？

---

## 4.12 Step 10：ToolRegistry

文件：

~~~text
nanobot/agent/tools/registry.py
~~~

理解三个核心动作：

~~~text
register
get_definitions
execute
~~~

### 默认 Tool 如何进入 Registry

不是 AgentLoop 一个个硬编码。

current-source：

~~~text
AgentLoop._register_default_tools
→ ToolContext(...)
→ ToolLoader().load(ctx, registry)
~~~

ToolLoader 负责 discovery/构造，ToolRegistry 负责运行期统一管理。

### MCP Tool 如何进入

MCP Connection 不由 AgentLoop 自己开。

应用启动层：

~~~text
shared ToolRegistry
→ MCPProvider(config, registry)
→ await connect
→ dynamic MCP tools register
→ AgentLoop 使用同一个 registry
~~~

这是 current-source 和旧教程差异最大的地方之一。

---

## 4.13 Step 11：save / respond

Runner 返回 AgentRunResult，其中包含：

~~~text
final_content
messages
stop_reason
tools_used
usage
provider_state
...
~~~

### save

回到 Loop 的 persist stage：

~~~text
AgentRunResult.messages
→ 根据 save boundary 取新增部分
→ Session
→ SessionManager.save
~~~

为什么不能直接把 Runner messages 全 append？

因为里面包含原来的 history，重复保存会导致历史膨胀。

### respond

~~~text
prepare outbound
→ OutboundMessage
→ TurnDelivery
→ MessageBus
→ Channel
~~~

Streaming 场景还要区分：

- StreamDelta；
- StreamEnd；
- final outbound；
- error/cancel。

---

## 4.14 Subagent 为什么能复用 Runner

文件：

~~~text
nanobot/agent/subagent.py
~~~

SubagentManager 直接依赖：

~~~text
AgentRunner
AgentRunSpec
~~~

这验证了第 03 章的分层：

> Runner 是 Model/Tool Execution Engine，不是“主聊天 Agent”。

Subagent 可以构造自己的：

- focused prompt；
- scoped ToolRegistry；
- runtime；
- project workspace；

然后复用 Runner。

---

## 4.15 Memory 代码告诉我们旧教程哪里失效

文件：

~~~text
nanobot/agent/memory.py
~~~

current MemoryStore 初始化时管理：

~~~text
memory/MEMORY.md
memory/history.jsonl
legacy HISTORY.md
SOUL.md
USER.md
.dream_cursor
GitStore
~~~

HISTORY.md 现在主要用于 legacy migration。

所以旧回答：

> Nanobot 是 MEMORY.md + HISTORY.md 双层记忆，并通过 save_memory 工具写入。

已经不应该继续使用。

current mental model：

~~~text
Session
→ Consolidation / history.jsonl
→ Dream
→ SOUL / USER / MEMORY
~~~

---

## 4.16 断点与最小实验

### Experiment A：第一次进入 Runner 前 Context 如何生成

断点：

~~~text
AgentLoop._build_turn
AgentLoop._run_agent_loop
ContextBuilder.build_transcript
AgentRunner.run
~~~

记录：

~~~text
ctx.history
TranscriptInput
effective project workspace
Tool names
最终 initial transcript
~~~

### Experiment B：一次 read_file

断点：

~~~text
AgentRunner._run_core
ToolRegistry.execute
filesystem tool execute
~~~

记录：

~~~text
tool name
arguments
tool result
messages before/after
~~~

### Experiment C：Session Save

断点：

~~~text
AgentLoop._persist_turn
Session.add_message
SessionManager.save
~~~

再打开对应 JSONL 对比。

---

## 4.17 给 Codex 的源码追踪 Prompt

可以直接使用仓库：

~~~text
prompts/codex-source-trace.md
~~~

原则只有三个：

1. 一轮只追一个问题；
2. 先定位真实调用点；
3. 必须给输入、输出和下一跳。

不要让 Codex 一次“解释整个 Nanobot”。

---

## 4.18 面试高频题

### Q1：你是怎么读 Nanobot 源码的？

> 我按一条真实消息做 source trace。先从 Channel 构造 InboundMessage，跟到 AgentLoop 的 per-session FIFO 和 TurnContext，再追 restore/compact/build/run/save/respond；run 阶段继续跟 AgentRunSpec → AgentRunner → ToolRegistry，最后回到 Session persistence 和 Outbound delivery。我对每一跳都记录输入输出数据结构，并用断点/测试验证。

### Q2：current-source 最关键的架构变化是什么？

一个很好的回答：

> AgentLoop/AgentRunner 分层，以及 Turn pipeline 化。前者把产品层状态与 model execution 解耦，后者让 restore、context build、run、persist、delivery 的错误边界更清晰。

### Q3：ToolRegistry 为什么不是 MCPRegistry？

因为 Registry 管的是统一 model-callable Tool，MCP 只是 Tool 来源之一。

---

## 4.19 本章总结

你现在应该能白板画出：

~~~text
Channel
→ InboundMessage
→ MessageBus
→ Session FIFO
→ TurnContext
→ restore
→ compact
→ build
→ TranscriptInput
→ AgentRunSpec
→ AgentRunner
→ Provider
→ ToolRegistry
→ Tool Result
→ Provider
→ AgentRunResult
→ save
→ OutboundMessage
→ Channel
~~~

如果这条链能不看文档讲清楚，Phase 1 的源码核心才算真正掌握。
