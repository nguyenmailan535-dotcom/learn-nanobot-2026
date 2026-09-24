# 02 - Nanobot 项目概览

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

**HKUDS**（The University of Hong Kong Data Science Lab）是香港大学的数据科学研究实验室。Nanobot 仓库于 **2026-02-01** 创建，并在 2026 年快速演进。

截至本教程固定的 **2026-09-24 current-source 快照**，GitHub 仓库约 **48.5K Stars / 8.5K Forks**，仓库描述已经明确包含：

```
WebUI
tools
memory
MCP
multi-agent workflows
automation
chat apps
```

因此，早期“4000 行超轻量 Demo”的宣传语可以帮助理解项目起点，但已经不适合描述今天的源码规模和产品边界。

### 项目诞生的背景

Nanobot 仍然坚持“可理解、自托管、Python-first”的方向，但 current-source 已经解决了更完整的 Agent Runtime 问题：

```
┌─────────────────────────────────────────────────────────────┐
│                 2026-09-24 Nanobot Runtime                  │
│                                                             │
│  Product Surfaces                                           │
│  ├── CLI / Native TUI                                       │
│  ├── WebUI / WebSocket                                      │
│  ├── Chat Apps                                              │
│  ├── OpenAI-compatible API                                  │
│  └── Python SDK                                             │
│                                                             │
│  Agent Runtime                                              │
│  ├── AgentLoop：Session / Workspace / Turn orchestration     │
│  ├── AgentRunner：Provider / Tool execution loop             │
│  ├── ContextBuilder：Prompt / History / Skills / Memory      │
│  ├── ToolRegistry + ToolLoader                              │
│  └── ModelRuntimeResolver / Provider Registry               │
│                                                             │
│  Stateful / Long-running                                    │
│  ├── Session + AutoCompact                                  │
│  ├── Consolidator + Dream                                   │
│  ├── Subagent                                               │
│  ├── Cron / Local Trigger / Heartbeat                       │
│  └── Gateway                                                │
│                                                             │
│  Extension & Security                                       │
│  ├── MCPProvider                                            │
│  ├── Skills / Agent Plugins                                 │
│  ├── Workspace scope / sandbox                              │
│  └── SSRF / pairing / allowlists                            │
└─────────────────────────────────────────────────────────────┘
```

### 项目定位

current README 对 Nanobot 的定位是一个：

> **Ultra-lightweight, open-source, self-hosted personal AI agent framework in Python**

“Ultra-lightweight”今天更适合理解为**核心概念和运行链路仍然可追踪**，而不是“整个仓库只有约 4000 行”。

本课程因此不以“周末读完全部源码”为目标，而以：

1. 追清一条真实 Turn；
2. 理解 AgentLoop / AgentRunner / ContextBuilder / ToolRegistry / Session 的边界；
3. 做最小可复现实验；
4. 能解释 current-source 的设计取舍。

## 2.2 为什么叫"超轻量级"

### 代码量对比

原版教程用“约 4000 行”解释 Nanobot 的早期设计哲学。这个历史背景可以保留，但**不要再把 4000 行当成 current-source 的事实**。

2026-09-24 的仓库已经包含：

```
nanobot/
webui/
tui/
tests/
docs/
SDK / API / Gateway / Channels / Security / Automations ...
```

所以面试中更有价值的不是背代码量，而是说明：

> Nanobot 在功能明显扩展后，仍然通过职责边界把复杂度拆开。

### 4000 行代码如何做到的？

这部分应当改成“早期极简思想在新版里保留了什么”。

**1. 仍然让 LLM 负责局部决策**

Nanobot 没有把所有任务都硬编码成 DAG。多数 Tool Selection 与下一步动作仍由模型在 AgentRunner 中决定。

**2. 用清晰 Contract 控制复杂度**

current-source 的关键 Contract 包括：

```
InboundMessage / OutboundMessage
TurnContext
AgentRunSpec / AgentRunResult
Tool Schema
Provider Contract
Session / Workspace Scope
```

**3. Registry / Discovery 替代大面积硬编码**

Provider、Tool、Channel、Skill、Plugin 都有 registry/discovery 路径。

**4. Composition Root 管理基础设施**

MCPProvider 等连接型基础设施由 CLI/Gateway/SDK 等应用入口组装，而不是塞进 AgentLoop。

**5. 文件仍然是重要的透明持久化介质**

但 current-source 已不是简单的 `MEMORY.md + HISTORY.md`：

```
Session JSONL
memory/history.jsonl
SOUL.md
USER.md
memory/MEMORY.md
cron/jobs.json
```

### 面试中如何解释"超轻量级"

> "我不会再用‘只有 4000 行’描述 2026-09 的 Nanobot，因为 current-source 已经扩展成完整 self-hosted Agent Runtime。它现在值得学习的地方，是复杂度增长后仍保留了清晰分层：AgentLoop 管用户 Turn，AgentRunner 管模型/工具循环，ContextBuilder 管上下文，ToolRegistry 管能力，Session/Dream 管状态，MCPProvider 由 Composition Root 管连接生命周期。相比记代码量，这些边界更能迁移到实际 Agent 工程。"

## 2.3 核心特性详解

### 特性一：多 LLM Provider / Gateway支持

“11+”仍然成立，但 current-source 已不适合用固定小列表概括。Provider metadata 集中在 `nanobot/providers/registry.py`，配置在 `nanobot/config/schema.py`。

current-source 同时包含：

- 通用 OpenAI-compatible Provider 路径；
- Anthropic、Azure OpenAI、AWS Bedrock、OpenAI Codex、GitHub Copilot 等专用路径；
- OpenRouter 等 Gateway Provider；
- Local Provider / custom API base。

模型选择还加入了：

```
model presets
provider inference
context window
fallback models
runtime selection
```

### 特性二：多种 Chat Apps / WebSocket支持

“8+”也只是早期下限。2026-09-24 源码中的 Channel Package 包括：

```
Telegram / Discord / Slack / Feishu / DingTalk
WeChat / WeCom / WhatsApp / QQ / NapCat
Matrix / Mattermost / MS Teams / Signal / Email
Linear / MoChat / WebSocket ...
```

Channel 由 package/registry discovery 管理，核心仍然通过统一的 `InboundMessage / OutboundMessage` 与 Agent Core 解耦。

### 特性三：MCP 协议原生支持

Nanobot 仍原生支持 MCP，但 current ownership 已经非常明确：

```
Application Composition Root
        ↓
shared ToolRegistry
        ↓
MCPProvider.connect()
        ↓
动态注册 MCP Tool / Resource / Prompt wrappers
        ↓
AgentLoop / AgentRunner 使用同一 Registry
```

`AgentLoop` **不负责** MCP 连接的 connect/close lifecycle。

### 特性四：Session + AutoCompact + Dream 记忆体系

这一标题来自旧版教程；current-source 实际已经演化成多层 Memory/Session 架构：

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

- Session：近期可恢复 conversation state；
- history.jsonl：压缩归档历史；
- Dream：长期信息整理；
- SOUL/USER/MEMORY：curated durable memory。

### 特性五：Skills 技能系统

current SkillsLoader 支持：

```
Workspace Skills
Agent Plugin Skills
Built-in Skills
```

并继续使用 Progressive Disclosure：通常先给模型 Skill 名称、描述、路径与可用性；完整 Skill 内容按需加载。

此外用户可以通过 `$skill-name` 显式激活某个 Skill。

### 特性六：子Agent与定时任务

current-source 已不只是“SubAgent + Cron”：

- `SubagentManager` 支持 background spawn 与 inline run；
- `agents.defaults.maxConcurrentSubagents` 当前默认 4；
- `CronService` 使用自有持久化 store + `croniter` 计算 schedule；
- Local Trigger 可以从本地脚本/CI 等显式触发 Session Turn；
- Heartbeat 是 Gateway 注册的**受保护系统 Cron Job**，默认每 30 分钟检查 `HEARTBEAT.md`；
- Dream 也由 Gateway 作为 system job 管理。

## 2.4 项目数据与里程碑

### 关键数据

以 **2026-09-24** GitHub API 快照为准：

| 指标 | 快照 |
|------|------|
| 仓库创建 | 2026-02-01 |
| Stars | 约 48.5K |
| Forks | 约 8.5K |
| 主语言 | Python |
| License | MIT |
| 源码基线 | HKUDS/nanobot main |

> ⚠️ Stars/Forks 会变化，面试时没有必要背精确数字。真正有用的是说明你基于哪个 Commit/日期读的源码。

### 增长轨迹

对学习者更重要的“里程碑”不是 Star 曲线，而是架构演化：

```
早期：单体式轻量 Agent
  ↓
AgentLoop / AgentRunner 分层
  ↓
WebUI / Gateway / API / SDK
  ↓
Session / AutoCompact / Dream
  ↓
MCPProvider / Agent Plugins / Skills
  ↓
Automations / Triggers / Pairing / Sandbox
```

这也是为什么本教程固定学习快照：Nanobot 更新快，旧博客中的具体类、默认值、配置字段很容易过时。

## 2.5 为什么选 Nanobot 学习

### 面试价值分析

| 维度 | Nanobot 的优势 | 其他框架的问题 |
|------|---------------|---------------|
| **源码可读性** | current-source 规模已扩大，但核心边界仍可按调用链深入跟踪 | 数万行甚至数十万行，根本读不完 |
| **架构理解** | 五层架构清晰明了 | 抽象层过多，难以把握全局 |
| **设计模式** | 10+ 经典设计模式可讲 | 模式混杂，难以提炼 |
| **技术热点** | MCP原生支持（面试热门话题）| 后来追加，理解不深 |
| **项目热度** | 2026-09-24 约 48.5K Stars；面试更应强调固定源码快照与真实实验 | 需要额外解释项目背景 |
| **差异化** | 很少有人深入研究Nanobot | 人人都说学过LangChain |
| **实战性** | 可以快速搭建真实的Agent | 搭建过程复杂，Demo效果一般 |

### "以小见大"的学习策略

```
通过 Nanobot current-source 的核心链路，你可以理解：

Agent 核心概念
├── AgentLoop → 理解 Agent 的推理循环
├── Memory → 理解 Agent 的记忆管理
├── Tools → 理解 Agent 的工具调用
└── MCP → 理解工具标准化协议

软件工程思想
├── 异步编程 → asyncio 实战
├── 设计模式 → 适配器、注册表、生产者-消费者等
├── 配置驱动 → Pydantic schema + config.json + WebUI Settings
└── 关注点分离 → 层次清晰的模块化设计

系统设计能力
├── 消息队列 → MessageBus 双队列设计
├── 并发控制 → 会话锁 + 并发闸门
├── 插件系统 → Skill/MCP 热加载
└── 多平台适配 → 适配器模式
```

### 与 LangChain 学习路径对比

| 阶段 | 学习 Nanobot | 学习 LangChain |
|------|-------------|---------------|
| 入门 | 1天：跑通示例，理解配置 | 3天：理解概念，跑通示例 |
| 架构 | 2天：通读源码，理解架构 | 2周：部分模块源码，理解抽象层 |
| 深入 | 3天：掌握设计模式和关键实现 | 1月：深入部分模块，仍有盲区 |
| 面试 | 1周内可完成面试准备 | 需要数周，且难以讲清全局 |

**结论**：Nanobot 让你在一周内就能达到面试中"项目深度"的要求，而且因为读过全部源码，面试时任何关于架构设计的追问都能从容回答。

---

## 2.6 与其他框架的差异化对比

### 全维度对比表

| 维度 | Nanobot | LangChain | CrewAI | AutoGPT | OpenClaw |
|------|---------|-----------|--------|---------|----------|
| **设计哲学** | 极简、够用 | 全面、生态 | 协作导向 | 全自主 | 企业全栈 |
| **核心代码** | ~4K行 | ~500K行 | ~30K行 | ~100K行 | ~430K行 |
| **学习曲线** | 1天上手 | 1周入门 | 3天入门 | 3天入门 | 1周入门 |
| **Agent模式** | 单Agent+SubAgent | 灵活组合 | 多Agent协作 | 单Agent循环 | 单Agent/多Agent |
| **LLM支持** | 多 Provider / Gateway | 50+供应商 | 依赖LangChain | 主要OpenAI | 多供应商 |
| **MCP支持** | 原生内置 | 扩展支持 | 有限 | 无 | 支持 |
| **记忆系统** | 文件系统 | 多后端 | 内置 | 内置 | 多模态 |
| **平台集成** | 多 Channel package | 需自行集成 | 无 | Web UI | 有限 |
| **定时任务** | 内置Cron | 无 | 无 | 无 | 有限 |
| **安全机制** | workspace沙箱 | 基本 | 基本 | 基本 | 完善 |
| **配置方式** | JSON/Pydantic + WebUI | 代码/配置 | 代码+装饰器 | 代码 | 代码+配置 |
| **部署难度** | 简单(pip) | 中等 | 中等 | 较复杂 | 复杂 |
| **适合人群** | 个人/小团队 | 企业开发者 | 多Agent场景 | 研究者 | 企业客户 |

### 核心差异解读

#### Nanobot vs LangChain

```
LangChain 的设计理念："提供一切可能需要的工具和抽象"
├── 优势：生态丰富，几乎什么都能做
├── 劣势：过度封装，代码复杂，更新频繁导致 API 不稳定
└── 类比：一个装满工具的大工具箱

Nanobot 的设计理念："提供恰好够用的核心能力"
├── 优势：代码简洁，架构清晰，一目了然
├── 劣势：功能较少，生态不如 LangChain 丰富
└── 类比：一把精心打造的瑞士军刀
```

**面试说法**：
> "如果说 LangChain 是一个大型超市，什么都有但找东西费劲；那 Nanobot 就是一家精品店，东西不多但每样都精心挑选。从学习角度，Nanobot 更适合理解 Agent 的本质设计，就像学操作系统不应该从 Linux 内核开始，而应该从 xv6 这样的教学操作系统开始。"

#### Nanobot vs AutoGPT

```
AutoGPT：追求"完全自主"
├── 想法前卫，但实际可靠性低
├── Token 消耗大，容易陷入循环
└── 更像一个概念验证（PoC）

Nanobot：追求"实用可靠"
├── 明确的迭代限制（40次/15次）防止无限循环
├── workspace 沙箱保证安全
└── 更像一个生产就绪的工具
```

#### Nanobot vs CrewAI

```
CrewAI：多 Agent 协作框架
├── 擅长多个 Agent 角色分工
├── 但单 Agent 场景下过于复杂
└── 依赖 LangChain 生态

Nanobot：以单 Agent 为核心
├── 通过 SubAgent 实现有限的多 Agent
├── 单 Agent 场景下简洁高效
└── 完全独立，无外部框架依赖
```

---

## 2.7 面试话术

### 话术一：介绍你学的 Nanobot 项目

> "我学习的是 HKUDS/nanobot 的 2026-09-24 current-source，而不是早期 4000 行版本。我重点追过 Channel/MessageBus → AgentLoop → ContextBuilder → AgentRunner → ToolRegistry → Session 的完整调用链。新版还包含 WebUI、Gateway、MCPProvider、Dream、Subagent 和 Automations，所以我把它当成一个真实的 self-hosted Agent Runtime 来学习。"

### 话术二：为什么选这个项目而不是只学 LangChain

> "我不是用 Nanobot 去替代 LangChain，而是用它做源码学习。它的核心边界比较容易跟踪：AgentLoop 负责产品层 Turn，AgentRunner 负责 Provider/Tool Loop，工具和 Channel 都有 Registry/Adapter，状态又拆成 Session、Compaction 和 Dream。这样我可以把 Agent 的工程原理学透，再迁移到其他框架。"

### 话术三：Nanobot 最大的技术亮点是什么

> "我认为亮点不是某个固定代码量，而是复杂度增长后仍然保持清晰 ownership。例如 MCPProvider 的连接生命周期由 Composition Root 管，而 AgentLoop 只共享 ToolRegistry；同一 Session 通过 pending queue + worker 保证 FIFO，同时支持 mid-turn injection；Memory 又把 Session Replay、History Archive 和 Dream Durable Memory 分开。这些设计比单纯的 ReAct while-loop 更接近真实生产系统。"

## 2.8 本章总结

### 核心知识点回顾

```
┌─────────────────────────────────────────────────────┐
│                   本章核心要点                        │
│                                                     │
│  1. Nanobot 是 HKUDS 开源的超轻量级 Agent 框架      │
│     → current-source Runtime | 约48.5K Stars（2026-09-24） | MIT             │
│                                                     │
│  2. 六大核心特性                                     │
│     → 多 LLM Provider / Gateway                                │
│     → 多种 Chat Apps / WebSocket                                    │
│     → MCP 协议原生支持                                │
│     → Session + AutoCompact + Dream 记忆体系                                    │
│     → Skills 技能系统                                 │
│     → 子Agent + 定时任务                              │
│                                                     │
│  3. "超轻量"的设计哲学                                │
│     → 利用 LLM 规划能力                               │
│     → 配置驱动代替代码驱动                             │
│     → 文件系统代替数据库                               │
│     → 标准协议代替自定义抽象                           │
│                                                     │
│  4. 面试价值                                         │
│     → 源码可读 | 架构清晰 | 差异化 | 热度高            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 面试 Checklist

- [ ] 能用 30 秒介绍 Nanobot 项目
- [ ] 能解释"超轻量级"的含义和设计决策
- [ ] 能列举 Nanobot 的 6 大核心特性
- [ ] 能对比 Nanobot 与 LangChain/AutoGPT 的差异
- [ ] 能说出选择 Nanobot 学习的理由

---

## 下一章

接下来，我们将深入 Nanobot 的架构设计，理解它的五层架构和四大核心模块。

➡️ [03 - 架构深入解析](../03-runtime-architecture/README.md)

---

> 📝 **本章小结**：Nanobot 从早期极简框架演化为完整 self-hosted Agent Runtime。对面试者而言，真正有价值的是沿 current-source 理解 Runtime 分层、状态治理、工具生命周期、并发与安全边界，而不是继续背早期代码量。
