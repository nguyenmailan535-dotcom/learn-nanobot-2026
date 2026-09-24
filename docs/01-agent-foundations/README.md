# 01 - 什么是 AI Agent：从概念到 Nanobot Runtime

> 🎯 **本章目标**：建立后续阅读 Nanobot 源码所需的 Agent 心智模型。理解 LLM 与 Agent 的本质区别、Tool Calling、ReAct、Context、Session、Memory、Workflow 和 Eval；最后把这些概念映射到 2026-09-24 的 HKUDS/nanobot current-source。

---

## 目录

- [1.1 为什么先学 Agent，而不是先背框架 API](#11-为什么先学-agent而不是先背框架-api)
- [1.2 LLM 与 Agent 的本质区别](#12-llm-与-agent-的本质区别)
- [1.3 Agent 的核心组成](#13-agent-的核心组成)
- [1.4 Tool Calling：模型如何“请求行动”](#14-tool-calling模型如何请求行动)
- [1.5 ReAct：真正重要的是反馈闭环](#15-react真正重要的是反馈闭环)
- [1.6 最小 Agent Loop](#16-最小-agent-loop)
- [1.7 Agent 与 Workflow 的边界](#17-agent-与-workflow-的边界)
- [1.8 Context、Session、Memory 为什么必须分开](#18-contextsessionmemory-为什么必须分开)
- [1.9 Agent 失败的分层诊断](#19-agent-失败的分层诊断)
- [1.10 映射到 Nanobot current-source](#110-映射到-nanobot-current-source)
- [1.11 动手实验](#111-动手实验)
- [1.12 面试高频题](#112-面试高频题)
- [1.13 本章总结](#113-本章总结)

---

## 1.1 为什么先学 Agent，而不是先背框架 API

很多 Agent 教程一上来就教某个 SDK：

~~~python
from langchain...
from llama_index...
~~~

这样做 Demo 很快，但很容易出现一个问题：

> 框架一升级，原来的 API 变了，你就不知道系统到底在干什么。

你现在的目标不是“会调用一个 Agent 框架”，而是能去面试 Agent 开发、AI 应用、AI 平台岗位。因此真正应该掌握的是一套**框架无关的运行时心智模型**。

一个最小 Agent 可以抽象成：

~~~text
用户目标
  ↓
构造上下文
  ↓
模型决策
  ↓
是否调用工具？
  ├─ 否 → 最终回答
  └─ 是
      ↓
    执行工具
      ↓
    Observation / Tool Result
      ↓
    回到模型
~~~

所以本章最重要的一句话是：

> **Agent 不是“一个更聪明的模型”，而是一个围绕模型构建的、有状态、有执行能力、有反馈闭环的软件系统。**

这和你熟悉的 Java 后端也很像：模型只是系统中的一个依赖，并不是整个应用本身。

---

## 1.2 LLM 与 Agent 的本质区别

### 1.2.1 普通 LLM 调用

最简单的 LLM 应用：

~~~text
messages
   ↓
provider
   ↓
response
~~~

程序把消息发送给模型，然后拿到输出。

### 1.2.2 Agent 调用

Agent 至少增加了：

~~~text
State / Context
      ↓
   LLM Call
      ↓
Action Decision
      ↓
Environment / Tool
      ↓
Observation
      ↓
更新状态
      ↓
下一轮 LLM Call
~~~

因此两者差异不在“是不是多轮对话”，而在：

| 维度 | 普通 LLM 应用 | Agent |
|---|---|---|
| 状态 | 通常直接拼 messages | Session / Context / Memory 分层 |
| 外部行动 | 通常没有 | Files / Shell / Web / MCP / API |
| 控制流 | 一次 request-response | 多轮 provider-tool loop |
| 环境反馈 | 没有 | Tool Result 会重新进入模型 |
| 停止条件 | API 返回 | final answer / iteration limit / error / cancel |
| 可观察性 | 输入、输出 | 还要看 tool trace、state、runtime events |

### 1.2.3 一个常见误区

错误理解：

> “用了 Function Calling，所以就是 Agent。”

不一定。

如果程序只是：

~~~text
模型返回 tool_call
→ 程序执行一次函数
→ 直接结束
~~~

它只是“带工具调用的 LLM 应用”。

真正的 Agentic Loop 是：

~~~text
模型
→ Tool Call
→ Tool Result
→ 模型再次判断
→ 可能继续 Tool Call
→ ...
→ Final Answer
~~~

---

## 1.3 Agent 的核心组成

旧教程经常总结为：

~~~text
Planning + Memory + Tool Use
~~~

这个框架仍然有价值，但为了理解真实 Runtime，可以拆得更工程化。

### 1.3.1 Reasoning / Planning

模型负责决定：

- 是否需要工具；
- 调哪个工具；
- 参数是什么；
- 工具结果是否足够；
- 是否继续执行；
- 最终什么时候停止。

注意：真实 Agent 框架不一定存在一个独立的 Planner 类。

Nanobot current-source 的主要局部规划就发生在 AgentRunner 的 provider/tool loop 中。

### 1.3.2 Tool Use

工具让模型能够对外部世界产生作用：

~~~text
read_file
write_file
shell
web_search
web_fetch
MCP tools
cron
spawn
~~~

一个 Tool 通常需要稳定的：

~~~text
name
description
parameter schema
execution behavior
result
error contract
~~~

### 1.3.3 State

Agent 不是无状态函数。

真实系统至少可能有：

~~~text
当前 provider transcript
当前 Session
session metadata
workspace
project workspace
runtime context
long-term memory
provider conversation state
~~~

这些状态的生命周期不同，所以不能全部叫“Memory”。

### 1.3.4 Control Loop

有人必须负责：

~~~text
call model
→ parse tool calls
→ execute tools
→ append results
→ call model again
→ stop
~~~

在 Nanobot current-source 中，这一职责主要属于 AgentRunner。

---

## 1.4 Tool Calling：模型如何“请求行动”

### 1.4.1 模型不会直接执行 Python 函数

模型通常只是返回结构化意图。例如概念上：

~~~json
{
  "name": "read_file",
  "arguments": {
    "path": "README.md"
  }
}
~~~

真正执行函数的是 Agent Host。

因此：

~~~text
Function Calling
≠
Function Execution
~~~

模型决定“想调用什么”，宿主决定“是否允许、如何执行、结果是什么”。

### 1.4.2 Tool Schema 为什么重要

如果工具定义模糊：

~~~text
name: search
description: search something
~~~

模型很难判断：

- 什么时候该调用；
- query 应怎么写；
- 返回结果代表什么。

所以 Tool Schema 是**模型与运行时之间的契约**。

Nanobot 官方 current architecture 也把工具名称、schema 和错误行为视为 model-facing contract。

---

## 1.5 ReAct：真正重要的是反馈闭环

经典 ReAct 常写成：

~~~text
Thought
→ Action
→ Observation
→ Thought
→ Action
→ Observation
~~~

但现代模型/API 未必把完整 Thought 暴露出来。

所以不要把：

> “有没有打印 Thought”

当成：

> “有没有 ReAct”。

工程上真正重要的是：

~~~text
Model
  ↓
Tool Call
  ↓
Environment
  ↓
Tool Result
  ↓
Model
~~~

也就是推理与行动之间的反馈闭环。

---

## 1.6 最小 Agent Loop

下面是**教学伪代码**，不是 Nanobot 源码：

~~~python
messages = initial_messages

for _ in range(max_iterations):
    response = await provider.chat(
        messages=messages,
        tools=tool_registry.get_definitions(),
    )

    messages.append(response.as_assistant_message())

    if not response.tool_calls:
        return response.content

    for call in response.tool_calls:
        result = await tool_registry.execute(
            call.name,
            call.arguments,
        )
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": result,
        })

raise RuntimeError("max iterations reached")
~~~

真实框架要复杂得多，还要解决：

- streaming；
- reasoning blocks；
- 多工具并发；
- provider retry；
- tool timeout；
- tool result 过长；
- context compaction；
- cancellation；
- session checkpoint；
- mid-turn follow-up；
- subagent result injection。

所以“能写一个 while 循环”和“能设计 Agent Runtime”是两回事。

---

## 1.7 Agent 与 Workflow 的边界

### Workflow

控制流主要由开发者提前规定：

~~~text
Step A
→ Step B
→ if condition
→ Step C
~~~

### Agent

下一步行动更多由模型运行时决定：

~~~text
Goal
→ model chooses tool
→ sees result
→ chooses next action
~~~

### 真实系统通常是混合的

例如 Research Agent：

~~~text
上传 PDF
→ 建索引                     # deterministic
→ Agent 判断是否需要检索       # agentic
→ search_papers              # deterministic tool
→ Agent 综合 evidence         # agentic
→ citation validator         # deterministic
~~~

面试时不要说“Agent 比 Workflow 高级”。

更准确的说法：

> 两者区别在于控制权如何分配。生产系统常用 deterministic workflow 限定边界，再在局部使用 agentic decision。

---

## 1.8 Context、Session、Memory 为什么必须分开

这是后面源码学习最重要的基础之一。

### Context

**这一次模型调用实际看到的内容。**

### Session

**某个持续对话的持久化状态。**

### Memory

**跨更长时间被整理保留下来的 durable knowledge。**

关系：

~~~text
Session History
      ↓
ContextBuilder
      + AGENTS / SOUL / USER
      + Memory
      + Skills
      + Runtime Context
      ↓
Current Model Context
~~~

所以：

> Session 是“系统保存了什么”，Context 是“这次给模型看什么”。

这两个概念如果混在一起，后面读 ContextBuilder、SessionManager、AutoCompact、Dream 会全部混乱。

---

## 1.9 Agent 失败的分层诊断

以后看到“RAG 回答错了”或“Agent 做错了”，不要先换模型。

先按层定位：

~~~text
1. Context Failure
   └─ 应该给模型的信息没有进入 context

2. Retrieval Failure
   └─ RAG 没找到证据

3. Planning / Tool-selection Failure
   └─ 模型没调工具或调错工具

4. Tool Execution Failure
   └─ 参数、权限、网络、进程、超时错误

5. Observation Failure
   └─ Tool Result 太长、格式坏、被错误截断

6. Generation Failure
   └─ evidence 已经存在，但模型总结错

7. Citation / Grounding Failure
   └─ answer 看似正确，但 source 不支持 claim

8. Delivery Failure
   └─ Agent 做完了，但 channel 没发出去
~~~

这套故障分层会直接用在后面的 Research Agent Eval。

---

## 1.10 映射到 Nanobot current-source

2026-09-24 current-source 的主链：

~~~text
Channel
  ↓
MessageBus / InboundMessage
  ↓
AgentLoop
  ↓
ContextBuilder + Session
  ↓
AgentRunner
  ↔ Provider
  ↔ ToolRegistry
  ↓
AgentLoop
  ↓
OutboundMessage
~~~

关键源码：

| 概念 | Current-source |
|---|---|
| 输入事件 | nanobot/bus/events.py |
| 消息总线 | nanobot/bus/queue.py |
| 用户 Turn 编排 | nanobot/agent/loop.py |
| Provider/Tool Loop | nanobot/agent/runner.py |
| Context 构造 | nanobot/agent/context.py |
| Tool Registry | nanobot/agent/tools/registry.py |
| Session | nanobot/session/manager.py |
| Durable Memory | nanobot/agent/memory.py |

### 为什么拆 AgentLoop / AgentRunner

官方 current architecture 明确：

- AgentLoop：channel-facing turn；
- AgentRunner：model-facing loop。

这样主聊天 Agent、Subagent、Dream 等不同执行场景可以复用相同的 model/tool execution 思路，而不用把 channel/session 产品逻辑复制进去。

---

## 1.11 动手实验

### Experiment 01：自己写一个 30 行 Tool Loop

只用一个 Python 文件：

~~~text
calculator tool
+ fake provider / real compatible API
+ while loop
~~~

打印：

~~~text
iteration
assistant response
tool call
tool result
final answer
~~~

目标：亲眼看到模型**没有执行 tool**。

### Experiment 02：故意制造 Tool Error

让 Tool 在某个参数下抛异常，观察：

- error 是否回到模型；
- 模型是否尝试修正；
- 是否可能进入循环。

---

## 1.12 面试高频题

### Q1：LLM 和 Agent 的区别？

建议结构：

1. LLM 是推理/生成组件；
2. Agent 是完整系统；
3. Agent 增加 state、tools、control loop；
4. 用 Nanobot 的 AgentLoop/AgentRunner 举例。

### Q2：Tool Calling 和 Agent 有什么关系？

> Tool Calling 是 Agent 的一个能力接口，不等于 Agent 本身。宿主需要执行 Tool Call、把 Tool Result 回填，并继续让模型基于 Observation 决策，才能形成完整的 agentic loop。

### Q3：ReAct 一定要暴露 Thought 吗？

不需要。工程上更重要的是 Reason/Act/Observe 的闭环。

### Q4：为什么需要 Session？

一次任务可能跨多个模型调用甚至多个用户 turn。Session 保存可恢复的 conversation state，而 model context 只是当前调用输入的快照。

---

## 1.13 本章总结

现在应该形成：

~~~text
Agent
=
Model
+ Context
+ State
+ Tools
+ Execution Loop
+ Environment Feedback
+ Safety Boundary
+ Evaluation
~~~

下一章开始看：**2026 年的 Nanobot 已经不是早期“4000 行小框架”，它现在到底是一套怎样的 Agent Runtime。**
