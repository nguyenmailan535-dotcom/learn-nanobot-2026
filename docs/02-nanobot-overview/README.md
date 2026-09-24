# 02 - Nanobot 项目概览

> **2026 current-source 说明**：本章直接沿用原版 learn-nanobot 的章节结构与主体内容；凡涉及 Nanobot 具体源码、配置、路径、记忆、并发、MCP 生命周期等实现细节，均按 HKUDS/nanobot main @ 2026-09-24 (source trace snapshot around 62aa6ba6a33790a656b952ef150517bd70d6eb30) 修订。

> 🎯 **本章目标**：全面了解 HKUDS/nanobot 项目的背景、核心特性、设计理念，以及为什么它是面试学习的最佳选择。

---

## 目录

- [2.1 项目背景](#21-项目背景)
- [2.2 为什么叫"超轻量级"](#22-为什么叫超轻量级)
- [2.3 核心特性详解](#23-核心特性详解)
- [2.4 项目数据与里程碑](#24-项目数据与里程碑)
- [2.5 为什么选 Nanobot 学习](#25-为什么选-nanobot-学习)
- [2.6 与其他框架的差异化对比](#26-与其他框架的差异化对比)
- [2.7 面试话术](#27-面试话术)
- [2.8 本章总结](#28-本章总结)

---

## 2.1 项目背景

### 香港大学数据科学实验室（HKUDS）

**HKUDS**（The University of Hong Kong Data Science Lab）是香港大学的数据科学研究实验室。Nanobot 是其开源的 AI Agent 项目。

### 项目诞生的背景

原版教程发布时，Nanobot 的突出标签之一是“超轻量级、约 4000 行源码”。这个描述适用于早期版本，但已经不适合作为 **2026-09-24 current-source** 的项目定义。

原版总结的几个动机仍然成立：

~~~text
问题 1：Agent 系统容易被复杂抽象淹没
→ 学习者需要一条可以跟到底的核心调用链

问题 2：真实 Agent 不只需要模型
→ 还需要 Tool、Session、Memory、Channel、Security、Observability

问题 3：外部能力接入需要标准化
→ MCP、Tool Registry、Plugin 需要清楚的边界
~~~

current Nanobot 已经扩展为包含 CLI/TUI/WebUI/Gateway/API/SDK、多 Provider、MCP、Session/Dream、Skills/Plugins、Automations 与多平台 Channel 的完整 Agent Runtime，但核心链仍然可以沿源码追踪：

~~~text
Surface / Channel
→ MessageBus
→ AgentLoop
→ Context + Session
→ AgentRunner
→ Provider / ToolRegistry
→ Persistence / Delivery
~~~

### 项目定位

本课程不再把 Nanobot 定义成“一个周末能读完全部源码的 4000 行框架”。

更准确的定位是：

> **一个可自托管、可扩展、具有真实产品运行时边界，同时仍适合做 source trace 的 Agent Runtime。**

后续学习目标也从“读完全部源码”改为“把关键调用链、状态边界和扩展点读深，并用实验验证”。

## 2.2 为什么还可以叫“轻量、可理解”

“超轻量级”这个称呼可以保留为项目的历史设计取向，但不能再用固定代码行数来证明。

### current-source 的“轻量”主要体现在哪里

1. **核心职责边界清晰**：AgentLoop 与 AgentRunner 分层，Context、Tool、Session 各自有明确 ownership。
2. **尽量使用 Registry / Discovery**：Provider、Tool、Channel、Skill、Plugin 有稳定扩展点。
3. **模型负责局部决策**：不强制所有任务都进入复杂 DAG/Planner。
4. **Workspace 文件保持透明**：SOUL、USER、MEMORY、Skill 都能直接查看和审计。
5. **标准协议优先**：MCP 用于接入外部 Capability，而不是为每个工具生态重新定义一套专用协议。

### 为什么仍适合源码学习

current-source 已经远大于早期教学版本，但你仍可以只追一条核心链：

~~~text
InboundMessage
→ AgentLoop
→ ContextBuilder
→ AgentRunSpec
→ AgentRunner
→ ToolRegistry
→ Session Persistence
→ OutboundMessage
~~~

因此今天学习 Nanobot 的优势不是“源码少到能全部背下来”，而是：

> **能在一个真实产品化 Agent Runtime 中看清各层输入、输出、状态与失败边界。**

### 面试中如何解释

> “Nanobot 早期以极简源码著称，但我学习的是 2026 current-source。现在我不会用固定行数描述它，而是强调其核心 Runtime 边界仍然清晰：AgentLoop 负责 Session-facing Turn，AgentRunner 负责 Provider/Tool Loop，ToolRegistry、Session、MCPProvider 和 Memory 各自有明确职责。”

## 2.3 核心特性详解

### 特性一：多 Provider + Model Runtime

Provider metadata 集中在 `nanobot/providers/registry.py`，配置在 `nanobot/config/schema.py`。current-source 还支持：
- model presets；
- per-session model selection；
- context window runtime；
- hosted/local/openai-compatible provider path。

不要再背“11+”这种容易过时的固定数量。

### 特性二：多 Channel + WebUI

Channel 将平台事件统一为 `InboundMessage`，再通过 MessageBus 进入 Agent Core。current repository 采用 self-contained channel package/discovery 机制，WebUI/WebSocket 也是重要 Surface。

平台数量会持续变化，因此面试重点应放在：

~~~text
Platform SDK
→ Channel Adapter
→ InboundMessage / OutboundMessage
→ MessageBus
→ Agent Core
~~~

### 特性三：MCP

current MCP 是 application-owned infrastructure：
- composition root 创建 `MCPProvider`；
- 与 `AgentLoop` 共享 `ToolRegistry`；
- 在使用前 `connect()`；
- shutdown 时 `aclose()`。

MCP Tool 最终被适配成统一 Tool Registry 中的能力，因此 AgentRunner 不需要区分它来自 native tool 还是 MCP。

### 特性四：Memory System 2.0

不再是旧版 Session + memory/history.jsonl + Dream-managed durable memory 双层模型：

~~~text
Session JSONL
→ AutoCompact / Consolidator
→ memory/history.jsonl
→ Dream
→ SOUL.md / USER.md / memory/MEMORY.md
~~~

### 特性五：Skills + Agent Plugins

SkillsLoader 支持：
- workspace skills；
- enabled Agent Plugin skills；
- built-in skills；
- requirements 检查；
- progressive loading；
- 显式 `$skill-name` invocation；
- always skill。

Agent Plugin 可把 Skill 与 MCP server 打包，并有 manifest validation、enable state、package fingerprint 等安全机制。

### 特性六：Subagent + Automations

SubagentManager 支持 background / inline execution，并复用 AgentRunner。其迭代上限跟 current runtime limits 对齐，不再是“主 40、子 15”的固定旧设计。

Automation 包括：
- user-created Cron scheduled turn；
- local trigger；
- cron-backed protected Heartbeat system job；
- Dream schedule。

Gateway 是这些长期后台服务的重要宿主。


## 2.4 项目数据与里程碑

原版中的 Stars 数、平台数量、Provider 数量都属于高度易变数据，本仓库不再把固定数字写成学习结论。

### 2026-09-24 学习快照下的重要变化

相较早期版本，current-source 已具备：
1. Packaged WebUI / WebSocket 与项目工作区；
2. Python SDK 与 OpenAI-compatible API；
3. 更完整的 Session durability / recovery / provider state；
4. AutoCompact + Dream 双阶段长期记忆；
5. Agent Plugins v1 与 CLI Apps；
6. richer channel packages；
7. Cron / Local Trigger / Heartbeat / Dream 等 background runtime；
8. Workspace scope、SSRF、sandbox 等更系统的安全边界。

真正需要记录的是 **Git SHA + 学习日期**，而不是固定 Stars。


## 2.5 为什么选 Nanobot 学习

### 面试价值分析

current-source 的学习价值更偏向“真实 Agent Runtime 工程”：

~~~text
Message transport
+ Session durability
+ Context construction
+ Provider/tool execution
+ MCP lifecycle
+ Skill/Plugin packaging
+ Automations
+ Security boundaries
+ Observability
~~~

这些问题与后端工程高度相通：接口边界、资源生命周期、并发控制、持久化、重试、权限、可观测性。

### "以小见大"的学习策略

“以小见大”仍然成立，但方式要改：

~~~text
旧：因为整个仓库只有几千行，所以全部读完
新：选择一个真实数据流，沿边界追到底
~~~

推荐 source trace：

~~~text
InboundMessage
→ per-session queue
→ TurnContext
→ restore/build/run/save
→ AgentRunSpec
→ AgentRunner
→ ToolRegistry
→ SessionManager
~~~

### 与 LangChain 学习路径对比

不必把两个项目做“谁更好”的结论。对求职学习而言：
- Nanobot：适合看一套可运行产品的内部边界；
- LangChain/LangGraph：适合熟悉更广泛生态和图式工作流；
- OpenAI Agents SDK 等：适合学习不同的 runtime abstraction。

你需要的是可迁移的 Agent Runtime 思维，而不是绑定单一框架 API。

## 2.6 与其他框架的差异化对比

> 原版表格中的代码行数、Provider 数、平台数和具体版本会快速变化，因此这里保留比较维度，但不把易变数字当成永久事实。

### 设计取向对比

| 维度 | Nanobot current-source | LangChain / LangGraph | CrewAI | AutoGPT 类项目 |
|---|---|---|---|---|
| 核心学习点 | Agent Runtime 全链路 | 组件生态 / Graph 编排 | Multi-Agent 角色协作 | 高自主循环 |
| 执行核心 | AgentLoop + AgentRunner | Chain / Graph / Agent Runtime | Crew / Agent / Task | Autonomous Loop |
| 工具扩展 | Native Tool + MCP + Plugin | Tool / Integration 生态 | Tools / Integrations | Plugin / Tool |
| 状态 | Session + Memory + Dream | 多种 Memory/Checkpoint 后端 | Framework State | Task/Memory |
| 外部入口 | CLI/WebUI/Gateway/API/SDK/Channels | 通常由应用自行组合 | 应用层集成 | 各项目不同 |
| 学习优势 | 能追产品级 Runtime 链路 | 生态大、生产案例多 | Multi-Agent 概念直观 | Agent 历史代表 |

### Nanobot vs LangChain / LangGraph

原版“精品店 vs 大超市”的类比仍有启发，但不要再用固定代码量做论据。

更稳妥的说法：

> Nanobot 更适合追一个完整 Agent Host 从 Channel、Session、Context 到 Provider/Tool 的运行链；LangChain/LangGraph 更适合学习成熟生态下的组件组合和显式 Workflow/Graph。二者不是简单的“轻量一定优于重量”。

### Nanobot vs AutoGPT 类项目

current Nanobot 依然强调**受控执行**，但不要再背“主 Agent 40 次、SubAgent 15 次”的旧固定值。

current 资源治理包括：

- configurable max tool iterations
- per-session FIFO
- optional global inbound concurrency cap
- independent subagent concurrency
- Tool / Workspace permission boundary
- cancellation / recovery / checkpoint

### Nanobot vs CrewAI

CrewAI 更突出角色化 Multi-Agent；Nanobot current-source 以一个 Agent Runtime 为核心，并提供 Subagent delegation。是否需要 Multi-Agent 应由任务依赖与协作边界决定，而不是“Agent 数越多越高级”。

## 2.7 面试话术

### 话术一：介绍你学的 Nanobot 项目

> “我学习的是 2026-09-24 的 HKUDS/nanobot current-source。它现在是一套包含 CLI/WebUI/Gateway/API/SDK、多 Provider、MCP、Session/Dream、Skills/Plugins 与多平台 Channel 的 Agent Runtime。我不是按早期几千行版本背答案，而是沿 Channel → MessageBus → AgentLoop → AgentRunner → ToolRegistry → Session 的真实调用链做 source trace。”

### 话术二：为什么选 Nanobot 做源码学习

> “因为它已经包含真实 Agent 产品会遇到的 Session FIFO、Streaming、MCP Lifecycle、Memory、Automations 和 Security，但核心边界仍然比较清楚。我能把一个用户 Turn 的输入、状态、Tool Execution、Persistence 和 Delivery 追完整，而不是只会框架 API。”

### 话术三：Nanobot 最大的技术亮点是什么

> “我更看重它的责任拆分：AgentLoop 管 Session-facing Turn，AgentRunner 管 Provider/Tool Loop；ContextBuilder 决定模型看到什么，ToolRegistry 统一执行能力，MCPProvider 由应用组合层管理连接生命周期。这使 Channel、Subagent、MCP、Memory 都能围绕稳定边界扩展。”

## 2.8 本章总结

### 核心知识点回顾

~~~text
Nanobot current-source
├── Surface：CLI / TUI / WebUI / Gateway / API / SDK / Chat Apps
├── Turn：AgentLoop
├── Model Execution：AgentRunner
├── Context：ContextBuilder
├── Tool：ToolLoader / ToolRegistry / MCPProvider
├── State：Session / AutoCompact / Consolidation / Dream
├── Extension：Provider / Channel / Skill / Agent Plugin
└── Security：Workspace / Sandbox / SSRF / Pairing
~~~

### 面试 Checklist

- [ ] 能解释为什么不能继续用“4000 行小框架”定义 current-source
- [ ] 能画出 AgentLoop / AgentRunner 的核心链路
- [ ] 能区分 Session、Context、Memory
- [ ] 能解释 MCPProvider 与 ToolRegistry 的 ownership
- [ ] 能说明自己的源码学习快照，而不是把易变数字当永久事实

---

## 下一章

接下来，我们将深入 Nanobot 的架构设计，理解它的五层架构和四大核心模块。

➡️ [03 - 架构深入解析](../03-architecture-deep-dive/README.md)

---

> 📝 **本章小结**：Nanobot 早期以“极简但完整”著称，current-source 已经成长为更完整的 Agent Runtime。今天最值得学习的不是固定代码量，而是 MessageBus、AgentLoop、AgentRunner、Context、Tool、Session、MCP、Memory 与 Gateway 之间清晰的责任边界。
