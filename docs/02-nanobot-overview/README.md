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

**HKUDS**（The University of Hong Kong Data Science Lab）是香港大学的数据科学研究实验室，在大模型、推荐系统、图神经网络等方向有深厚的学术积累。

Nanobot 是 HKUDS 在 2026 年 2 月开源的项目，定位为一个**超轻量级 AI Agent 框架**。从发布到现在短短两个月内就获得了 37K+ Stars，增长速度惊人。

### 项目诞生的背景

```
┌─────────────────────────────────────────────────────────────┐
│                   Nanobot 诞生的时代背景                      │
│                                                             │
│  问题 1: Agent 框架过于复杂                                   │
│  ├── LangChain 50万行代码，学习曲线陡峭                       │
│  ├── AutoGPT 10万行代码，概念验证但不实用                     │
│  └── 初学者和个人开发者难以入门                                │
│                                                             │
│  问题 2: 缺少适合亚洲市场的 Agent 框架                        │
│  ├── 大多数框架不支持微信/飞书/钉钉                           │
│  ├── 国内 LLM（通义千问/DeepSeek）接入不便                    │
│  └── 中文生态支持不足                                        │
│                                                             │
│  问题 3: MCP 协议刚刚成熟，需要原生支持                       │
│  ├── 2024年底 Anthropic 发布 MCP 协议                        │
│  ├── 2025年各大公司跟进支持                                   │
│  └── 需要一个从设计之初就原生支持 MCP 的框架                   │
│                                                             │
│  Nanobot 的解答：                                            │
│  → 4000 行代码，极简但完整                                   │
│  → 原生支持微信/飞书/钉钉等 8+ 平台                          │
│  → MCP 原生支持，从第一天就内置                               │
│  → MIT 开源，对所有人免费                                    │
└─────────────────────────────────────────────────────────────┘
```

### 项目定位

Nanobot 的定位非常清晰：

> **一个任何人都能在 5 分钟内启动、一个周末就能读完全部源码的 AI Agent 框架。**

它不追求功能全面（那是 LangChain 的定位），也不追求自主通用（那是 AutoGPT 的定位），而是追求**极简、实用、可理解**。

---

## 2.2 为什么仍然适合源码学习

原版教程把 Nanobot 的核心卖点概括为“约 4000 行 Python 代码”。这适用于早期版本，但已经不符合 2026-09-24 的 HKUDS/nanobot main。

current-source 已经包含：

- CLI / TUI
- WebUI / WebSocket
- Gateway
- OpenAI-compatible API
- Python SDK
- Provider Registry / Model Presets
- AgentLoop / AgentRunner
- Tool discovery / MCP
- Agent Plugins v1 / Skills
- Session / AutoCompact / Consolidation / Dream
- Subagent / Cron / Local Trigger / Heartbeat
- 多种 Chat Channels
- Workspace / Project Scope
- Sandbox / SSRF / Pairing
- Hooks / Runtime Events / Usage Tracking

因此今天选择 Nanobot 学源码，不是因为“全部源码只有几千行”，而是因为它的**核心责任边界仍然清晰**：

```
Channel / Surface
      ↓
MessageBus
      ↓
AgentLoop
      ↓
Context + Session
      ↓
AgentRunner
      ↔ Provider
      ↔ Tools
```

### current-source 的学习优势

1. **核心链路可追踪**：可以沿一条真实消息追到 Provider、Tool 和 Session。
2. **产品级问题真实存在**：Session FIFO、streaming、recovery、MCP lifecycle、workspace security 都能在源码中看到。
3. **扩展点清楚**：Provider、Channel、Tool、Skill、Agent Plugin、MCP 各有不同边界。
4. **可以局部实验**：Context、Tool、Memory、Subagent、MCP 都可以单独验证。

### 面试中如何解释

> “我学习的是 Nanobot 2026 current-source，而不是早期几千行版本。我主要沿 MessageBus → AgentLoop → AgentRunner → ToolRegistry → Session 追核心链路，再用 MCP、Dream、Subagent 和 Channel 做扩展实验。它的价值不是代码量小，而是能在一个真实产品化 Runtime 中看清 Agent 各层 ownership。”

## 2.3 核心特性详解

### 特性一：多 Provider + Model Runtime

Provider 元数据集中在 `nanobot/providers/registry.py`，配置在 `nanobot/config/schema.py`。current-source 支持多种 hosted/local/OpenAI-compatible 后端，并针对 Anthropic、Azure OpenAI、AWS Bedrock、OpenAI Codex、GitHub Copilot 等提供专门路径。

模型选择还引入 Model Preset、Provider Snapshot 与 Session 级选择，不再只是一个固定 `provider + model` 字符串。

### 特性二：多 Surface / 多 Channel

Nanobot 不只支持聊天平台，还提供：

```
CLI
TUI
WebUI / WebSocket
Gateway
OpenAI-compatible API
Python SDK
Chat Apps
```

current Channel 以自包含 package 形式存在于 `nanobot/channels/<channel>/`，由 `ChannelManager` 负责发现、生命周期和出站路由。

### 特性三：MCP 原生集成

MCP current 架构不再是“AgentLoop 自己维护一组 MCP wrapper”。应用组合层创建共享 `ToolRegistry` 和 `MCPProvider`：

```
MCPProvider
    ↓ dynamic registration
ToolRegistry
    ↑
AgentLoop / AgentRunner
```

MCPProvider 负责 connect/reconnect/close；AgentRunner 只看到统一 Tool。

### 特性四：Session + Memory 2.0

旧版“MEMORY.md + HISTORY.md 双层记忆”已经升级为：

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

`HISTORY.md` 主要保留为 legacy migration 输入。

### 特性五：Skills + Agent Plugins

SkillsLoader 当前支持：

```
Workspace Skills
→ Enabled Agent Plugin Skills
→ Built-in Skills
```

并采用 progressive loading：先向模型暴露 Skill 摘要，需要时再读取完整 SKILL.md。Agent Plugin v1 可以把 Skill 与 MCP Server 打包成一个可安装、验证、显式启用的 capability package。

### 特性六：Subagent + Automations

current-source 包含：

- SubagentManager：后台与 inline 子 Agent
- CronService：定时任务
- Local Trigger：外部本地事件触发
- Heartbeat：Gateway 注册的受保护 Cron Job，读取 `HEARTBEAT.md`
- Dream：长期记忆系统任务

Subagent 的并发由 `agents.defaults.maxConcurrentSubagents` 控制（current default 4）；Inbound Turn 的全局并发则由 `NANOBOT_MAX_CONCURRENT_REQUESTS` 独立控制。

### 特性七：安全与可观察性

current-source 还包含：

- `tools.restrictToWorkspace`
- `tools.exec.sandbox`（Linux bwrap / macOS seatbelt）
- SSRF guard / whitelist
- Channel pairing / allowFrom
- Turn stage timing
- Agent hooks / typed runtime events
- usage tracking
- recovery checkpoints

## 2.4 项目数据与里程碑

> 本仓库固定以 **2026-09-24 的 HKUDS/nanobot main** 作为学习基线。Stars、Forks、Contributors 等社区数字会持续变化，不再把它们写成“固定架构事实”。

### 2026-09-24 学习快照的关键里程碑

| 维度 | current-source 状态 |
|---|---|
| 核心执行 | AgentLoop + AgentRunner 分层 |
| 用户入口 | CLI / TUI / WebUI / Gateway / API / SDK |
| Tool | Native Tools + MCP + Plugin Entry Points |
| Memory | Session + AutoCompact + Consolidation + Dream |
| 扩展 | Provider / Channel / Tool / Skill / Agent Plugin |
| Automation | Cron / Local Trigger / Heartbeat / Dream |
| 安全 | Workspace Guard / Exec Sandbox / SSRF / Pairing |
| WebUI | Conversation、Workspace、Model、Settings、Apps/Channels 管理 |

### 为什么版本快照重要

Agent 项目变化快。如果面试时继续背：

```
4000 行
8 个平台
11 个 Provider
MEMORY.md + HISTORY.md
固定 Semaphore(3)
```

这些曾经正确的细节会变成错误答案。

更好的做法是：

```
先说稳定架构边界
→ 再说明自己学习的 commit / 日期
→ 对会变化的数字只给“当前快照”
```

## 2.5 为什么选 Nanobot 学习

### 面试价值分析

| 维度 | Nanobot 的优势 | 其他框架的问题 |
|------|---------------|---------------|
| **源码可读性** | 核心链路清晰，可按调用链深入阅读 | 数万行甚至数十万行，根本读不完 |
| **架构理解** | 五层架构清晰明了 | 抽象层过多，难以把握全局 |
| **设计模式** | 10+ 经典设计模式可讲 | 模式混杂，难以提炼 |
| **技术热点** | MCP原生支持（面试热门话题）| 后来追加，理解不深 |
| **项目热度** | 37K Stars，面试官大概率听过 | 需要额外解释项目背景 |
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
├── 配置驱动 → YAML 组装系统
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
| **LLM支持** | 11+供应商 | 50+供应商 | 依赖LangChain | 主要OpenAI | 多供应商 |
| **MCP支持** | 原生内置 | 扩展支持 | 有限 | 无 | 支持 |
| **记忆系统** | 文件系统 | 多后端 | 内置 | 内置 | 多模态 |
| **平台集成** | 8+ | 需自行集成 | 无 | Web UI | 有限 |
| **定时任务** | 内置Cron | 无 | 无 | 无 | 有限 |
| **安全机制** | workspace沙箱 | 基本 | 基本 | 基本 | 完善 |
| **配置方式** | YAML | 代码 | 代码+装饰器 | 代码 | 代码+配置 |
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

> "我深入学习了 HKUDS/nanobot 这个项目，它是香港大学数据科学实验室开源的超轻量级 AI Agent 框架，它已经是一套包含 CLI/WebUI/Gateway/API/SDK、多 Provider、MCP、Session/Dream、Skills/Plugins 与多平台 Channel 的 Agent Runtime。
> 
> 我按真实调用链重点研究了三个方面：一是 AgentLoop 的 Turn Pipeline 与 AgentRunner 的 Provider/Tool Loop；二是 shared ToolRegistry + application-owned MCPProvider 的生命周期；三是 Session、AutoCompact、Consolidation 与 Dream 组成的新版 Memory System。"

### 话术二：为什么选这个项目而不是 LangChain

> "我选择 Nanobot 而不是 LangChain，主要考虑了三点。第一，深度胜过广度——Nanobot 的核心运行时边界足够清晰，我可以沿一条真实消息追完整个执行链并验证关键设计决策，这在面试中意味着任何追问我都能回答；第二，Nanobot 的架构更纯粹，它把 Agent 的核心概念——循环推理、记忆管理、工具调用——用最简洁的方式实现了，没有 LangChain 那种过度封装的问题；第三，它原生支持 MCP 协议，这是目前 AI 工具调用的标准化方向，面试中可以展示我对技术趋势的把握。"

### 话术三：Nanobot 最大的技术亮点是什么

> "我认为 Nanobot 最大的技术亮点是它的'配置驱动 + LLM 自主规划'的设计哲学。很多 Agent 框架花大量代码去实现复杂的任务编排引擎、状态机、DAG 执行器。但 Nanobot 的核心洞察是：LLM 本身就是最好的规划器。所以 Nanobot 只需要实现一个简洁的 ReAct 循环（AgentRunner），让 LLM 自己决定调用什么工具、什么顺序、什么时候结束。这种设计让 4000 行代码就能实现其他框架数十万行才能做到的功能。"

---

## 2.8 本章总结

### 核心知识点回顾

```
┌─────────────────────────────────────────────────────┐
│                   本章核心要点                        │
│                                                     │
│  1. Nanobot 是 HKUDS 开源的超轻量级 Agent 框架      │
│     → 4000行代码 | 37K+ Stars | MIT 协议             │
│                                                     │
│  2. 六大核心特性                                     │
│     → 11+ LLM 供应商                                │
│     → 8+ 聊天平台                                    │
│     → MCP 协议原生支持                                │
│     → 双层记忆系统                                    │
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

➡️ [03 - 架构深入解析](../03-architecture-deep-dive/README.md)

---

> 📝 **本章小结**：Nanobot 是一个"极简但完整"的 AI Agent 框架。它用 4000 行代码证明了：好的架构设计不在于代码多少，而在于是否抓住了问题的本质。对面试者而言，Nanobot 是一个"以小见大"的完美学习素材。
