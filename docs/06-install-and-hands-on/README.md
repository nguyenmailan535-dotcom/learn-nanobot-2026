# 06 - 安装与上手

> **阅读时间**：约 2 小时  
> **2026 current-source 说明**：本章直接沿用原版 learn-nanobot 的章节结构与主体内容；凡涉及 Nanobot 具体源码、配置、路径、记忆、并发、MCP 生命周期等实现细节，均按 HKUDS/nanobot main @ 2026-09-24 (source trace snapshot around 62aa6ba6a33790a656b952ef150517bd70d6eb30) 修订。

> **前置知识**：[05 - MCP 协议详解](../05-mcp-protocol/README.md)  
> **学习目标**：完成 Nanobot 的安装配置，运行你的第一个 AI Agent，理解全部配置项

---

## 目录

- [6.1 为什么需要动手实践](#61-为什么需要动手实践)
- [6.2 环境准备](#62-环境准备)
- [6.3 安装 Nanobot](#63-安装-nanobot)
- [6.4 配置向导 nanobot onboard](#64-配置向导-nanobot-onboard)
- [6.5 config.json 配置详解](#65-configjson-配置详解)
- [6.6 第一次运行：交互模式](#66-第一次运行交互模式)
- [6.7 自定义 AGENTS.md：定义 Agent 身份](#67-自定义-agentsmd定义-agent-身份)
- [6.8 引导文件体系](#68-引导文件体系)
- [6.9 常见问题排错](#69-常见问题排错)
- [6.10 实战练习](#610-实战练习)
- [6.11 面试话术](#611-面试话术)
- [6.12 本章小结](#612-本章小结)

---

## 6.1 为什么需要动手实践

学习 AI Agent 框架，**纸上得来终觉浅**。在面试中，面试官最看重的不是你能背多少概念，而是：

1. **你有没有真正用过？** —— 安装、配置、调试的全流程经验
2. **你能不能描述细节？** —— 配置文件的字段含义、启动参数的作用
3. **你遇到过什么问题？** —— 排错经历本身就是加分项

> 💡 **面试真相**：一个能说出 "我在配置 Nanobot 的 context_window_tokens 时发现设置过大会导致记忆压缩不触发" 的候选人，比只能背概念的候选人强 10 倍。

---


## 6.2 环境准备

### 6.2.1 系统要求

current-source 学习建议：
- Python 3.11+；
- Git；
- Windows / macOS / Linux 均可；
- 如果要开发 WebUI/TUI，按仓库当前开发文档准备 Bun 等前端工具；
- 一个可用 LLM Provider credential。

### 6.2.2 Python 环境配置

~~~powershell
python --version
git --version
~~~

建议使用独立虚拟环境：

~~~powershell
python -m venv .venv
..venvScriptsActivate.ps1
python -m pip install -U pip
~~~

macOS/Linux：

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
~~~

current-source 不再按旧教程的 Python 3.11 作为基线。

### 6.2.3 LLM API Key 准备

优先通过 `nanobot onboard --wizard` 或 WebUI Settings 配置，不要把 key 写进：
- Git 仓库；
- AGENTS.md / SOUL.md / USER.md；
- Skill；
- MCP command-line arguments。


## 6.3 安装 Nanobot

### 6.3.1 方式一：Stable Package

如果目标只是日常使用，可按官方 README 当前发布方式安装 stable package。

### 6.3.2 方式二：独立工具环境

也可以使用 uv/pipx 一类隔离工具安装 CLI，具体命令以 current README 为准。

### 6.3.3 方式三：从源码安装（本课程推荐）

~~~powershell
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
python -m venv .venv
..venvScriptsActivate.ps1
python -m pip install -e .
~~~

为什么使用 editable install？

~~~text
修改 checkout 源码
→ 当前环境直接使用修改后的代码
→ 方便断点 / test / source trace
~~~

学习前建议记录：

~~~powershell
nanobot --version
git rev-parse HEAD
~~~

### 6.3.4 安装后验证

~~~powershell
nanobot --help
nanobot status
nanobot agent -m "Reply only with install-ok"
~~~


## 6.4 配置向导 nanobot onboard

### 6.4.1 运行配置向导

current 推荐：

~~~powershell
nanobot onboard --wizard
~~~

如果已有较旧配置，可以关注 current `--refresh` 行为，它会按当前 schema 补齐缺省字段，同时尽量保留已有值。

### 6.4.2 向导流程详解

重点关注：
1. Config path；
2. Agent workspace；
3. Provider / model；
4. Channel；
5. Tool / MCP；
6. Gateway/Heartbeat/Dream 等 defaults。

### 6.4.3 向导生成的文件

current 默认概念：

~~~text
~/.nanobot/config.json        # Runtime Config
~/.nanobot/workspace/         # Agent-owned Workspace
<config-dir>/sessions/...     # Session Runtime Data
~~~

不要再假设“在哪个项目目录运行 onboard，config 就自动放那里”。


## 6.5 config.json 配置详解

### 6.5.1 完整配置示例

本章不固定粘贴一份很长的 snapshot，因为 current schema 会继续变化。查看：
- `nanobot/config/schema.py`
- 官方 `docs/configuration.md`
- WebUI Settings。

### 6.5.2 agents.defaults 字段详解

常见 current 概念包括：
- workspace；
- modelPreset / provider/model selection；
- context window；
- max tool iterations；
- max tool result chars；
- maxConcurrentSubagents；
- timezone；
- unifiedSession；
- disabledSkills；
- Dream settings。

### 6.5.3 providers 配置

Provider metadata 集中在 Provider registry。优先使用已有 OpenAI-compatible path；只有协议不同才需要专用 Provider implementation。

### 6.5.4 channels 配置

每个 Channel 是 self-contained package，配置是否启用、凭据、allowFrom/pairing 等平台字段。

### 6.5.5 tools 配置

current Tool Config 包括：
- restrictToWorkspace；
- exec sandbox；
- web search/fetch；
- SSRF whitelist；
- MCP Servers；
- image generation 等。

### 6.5.6 配置文件查找与写回

默认 Config：

~~~text
~/.nanobot/config.json
~~~

current schema 接受 camelCase 和 snake_case；官方文档优先 camelCase，因为 Nanobot 写回配置时使用 aliases。


## 6.6 第一次运行：交互模式

### 6.6.1 启动 Agent

~~~powershell
nanobot agent
~~~

One-shot：

~~~powershell
nanobot agent -m "Hello!"
~~~

WebUI：

~~~powershell
nanobot webui
~~~

Gateway：

~~~powershell
nanobot gateway
~~~

### 6.6.2 交互界面

Terminal、TUI/WebUI 都只是 Surface。核心 Runtime 仍然沿：

~~~text
MessageBus
→ AgentLoop
→ AgentRunner
~~~

运行。

### 6.6.3 常用交互命令

命令列表会随 current 版本变化，直接使用 `/help` / 官方 `docs/chat-commands.md`。本课程后续会重点用到：
- model/runtime 相关命令；
- compact；
- Dream；
- trigger/automation；
- status/debug 类命令。

### 6.6.4 观察 Agent 的行为

重点观察真实路径：

~~~text
~/.nanobot/config.json
~/.nanobot/workspace/
├── AGENTS.md
├── SOUL.md
├── USER.md
├── memory/
│   ├── MEMORY.md
│   └── history.jsonl
├── skills/
├── plugins/
└── cron/

<config-dir>/sessions/<workspace-id>/*.jsonl
~~~

## 6.7 自定义 AGENTS.md：定义 Agent 身份

### 6.7.1 AGENTS.md 的作用

`AGENTS.md` 是 Nanobot 中定义 Agent 身份和行为的核心文件。它的内容会被注入到 System Prompt 中，决定了 Agent "是谁"、"能做什么"、"怎么做"。

### 6.7.2 基础格式

```markdown
# My Assistant

你是一个专业的编程助手，擅长 Python 和 JavaScript 开发。

## 行为准则

- 回答问题时要准确、简洁
- 编写代码时注重可读性和可维护性
- 遇到不确定的问题要诚实说明

## 专业领域

- Python 后端开发
- React 前端开发
- 数据库设计与优化
```

### 6.7.3 高级 AGENTS.md 示例

```markdown
# 技术面试教练

你是一位经验丰富的技术面试教练，专门帮助候选人准备 AI Agent 方向的面试。

## 核心职责

1. **知识讲解**：深入浅出地解释 AI Agent 相关概念
2. **模拟面试**：模拟真实面试场景进行提问
3. **答案优化**：帮助候选人优化回答的结构和表达
4. **查漏补缺**：发现知识盲区并提供学习建议

## 回答风格

- 先给结论，再展开解释
- 使用"总-分-总"的结构
- 适当使用类比帮助理解
- 每个回答控制在 3 分钟以内

## 工具使用

- 使用 `read_file` 查阅参考资料
- 使用 `web_search` 搜索最新面试题
- 使用 `write_file` 生成面试笔记
```

### 6.7.4 AGENTS.md 与 System Prompt 的关系

```
System Prompt 构建过程：
┌──────────────────────────────────┐
│  1. 内置基础指令（Nanobot 框架）   │
│  2. SOUL.md（全局人格指引）        │
│  3. AGENTS.md（Agent 身份定义）    │
│  4. USER.md（用户信息）           │
│  5. TOOLS.md（工具使用指引）       │
│  6. MEMORY.md（长期记忆）         │
│  7. 技能摘要（Skills 目录）       │
│  = 最终 System Prompt             │
└──────────────────────────────────┘
```

---


## 6.8 引导文件体系

### 6.8.1 SOUL.md —— Agent-owned identity

SOUL.md 表达长期 personality/style，由 Agent Workspace 所有，也可能由 Dream 管理。

### 6.8.2 USER.md —— 用户画像

USER.md 适合保存稳定用户偏好和长期 profile，避免把一次性信息全部固化。

### 6.8.3 AGENTS.md / Project Instructions

current `ContextBuilder.BOOTSTRAP_FILES` 包含：

~~~python
["AGENTS.md", "SOUL.md", "USER.md"]
~~~

另外 current-source 还区分 Agent Workspace 与 effective Project Workspace：
- Agent Workspace：SOUL/USER/Memory/custom Skills；
- Project Workspace：Project AGENTS、relative tool paths、shell cwd。

旧教程中的 TOOLS.md 不应再被描述为 current ContextBuilder 的固定 bootstrap file；工具行为主要由 Tool schema、Skill 和 current runtime contract 驱动。

### 6.8.4 文件优先级与覆盖关系

不是简单“后一个文件覆盖前一个文件”。应理解为不同来源共同构造 Context，并有各自 ownership：
- Stable identity/tool contract；
- Agent-owned bootstrap；
- Project instruction；
- Memory；
- Active Skills；
- Session summary/history；
- Current input。


## 6.9 常见问题排错

### 6.9.1 安装问题

**命令找不到**

~~~powershell
Get-Command python
Get-Command nanobot
~~~

确认 terminal 使用的是安装 Nanobot 的虚拟环境。

**源码修改不生效**

确认使用 editable install：

~~~powershell
python -m pip install -e .
~~~

并记录 `git rev-parse HEAD`。

### 6.9.2 配置问题

**Provider / Model / API Base 不匹配**

先运行：

~~~powershell
nanobot status
~~~

再按 current provider registry/schema 检查，而不是照旧教程硬套某一模型名。

**旧 Config 字段失效**

使用 current `nanobot onboard --refresh`，并查看 config migration。

### 6.9.3 运行时问题

**文件访问 denied**
- effective Project Workspace 是否正确；
- `tools.restrictToWorkspace`；
- exec sandbox；
- plugin/skill read-only capabilities。

**Web fetch blocked**
- current SSRF guard 是否把目标判定为 private/internal；
- 只在明确可信时设置窄范围 `tools.ssrfWhitelist`。

**MCP Tools missing**
- Server 是否成功启动；
- `enabledTools`；
- MCPProvider connect/reconnect；
- plugin 是否 enabled；
- ToolRegistry 实际注册名。


## 6.10 实战练习

### 练习 1：创建一个翻译助手

沿用原版目标，但用 current Workspace：
1. 在 Agent Workspace / Project Workspace 中写 AGENTS；
2. 不需要修改 Nanobot core；
3. 通过 Terminal/WebUI 测试多轮翻译；
4. 观察 Session JSONL。

### 练习 2：创建一个代码审查助手

增加 current-source 要求：
- 建一个 `code-reviewer` Skill；
- 默认只给 read-only file tools；
- 对比显式 `$code-reviewer` 与未启用 Skill 的行为。

### 练习 3：观察新版记忆系统

对话：

~~~text
我叫张三，是一名后端开发工程师。
我最近在学习 Kubernetes。
我喜欢用 Python。
~~~

然后观察：
1. 当前 Session JSONL；
2. compact 后的 summary/history；
3. 手动触发 Dream；
4. USER.md / MEMORY.md 的变化；
5. 新建 Session 后是否还能利用 durable memory。

不要继续以“退出后看 memory/history.jsonl 是否追加”为验证标准。

## 6.11 面试话术

### 话术 1：描述你如何搭建 Nanobot 环境

> **面试官**：你有使用过 AI Agent 框架吗？能描述一下搭建过程吗？
>
> **参考回答**：
>
> "有的，我深入学习并使用过 HKUDS/nanobot 框架。搭建过程主要分几步：
>
> 首先是环境准备，Nanobot 要求 Python 3.11 以上，我用的是 uv 来安装，因为它比 pip 快很多。安装命令是 `uv tool install nanobot-ai`，这样会创建独立的虚拟环境，不污染全局。
>
> 然后运行 `nanobot onboard` 进行交互式配置，主要是选择 LLM Provider、填入 API Key、选择默认模型。它会生成一个 config.json 文件。
>
> 配置文件里有几个关键参数我特别关注：`context_window_tokens` 控制上下文窗口大小，直接影响记忆压缩的触发时机；`max_tool_iterations` 限制了单次对话中工具调用次数，防止 Agent 陷入死循环。
>
> 最后通过 AGENTS.md 定义 Agent 的身份和行为规范，就可以运行 `nanobot` 启动交互模式了。整个过程大概 10 分钟就能跑起来一个可用的 Agent。"

### 话术 2：配置文件的设计理念

> **面试官**：你觉得 Nanobot 的配置设计有什么特点？
>
> **参考回答**：
>
> "Nanobot 的配置设计体现了 **Markdown 即配置** 的理念，这是它区别于其他框架的一大特色。
>
> 具体来说，它用 JSON 文件管理技术配置（API Key、模型参数等），用 Markdown 文件管理行为配置（Agent 身份、用户画像、使用规范等）。这种分离很优雅：JSON 给机器读，Markdown 给人和 AI 读。
>
> 特别值得一提的是它的引导文件体系——SOUL.md 定义人格、AGENTS.md 定义身份、USER.md 定义用户画像、TOOLS.md 定义工具规范——这四个文件共同构建了一个层次清晰的 System Prompt。这种设计让非技术人员也能通过修改 Markdown 来定制 Agent 行为，大大降低了使用门槛。"

### 话术 3：遇到的问题和解决方案

> **面试官**：搭建过程中遇到过什么问题吗？
>
> **参考回答**：
>
> "遇到过几个典型问题。一个是 API 连接超时，因为在国内直连 OpenAI API 不稳定，我的解决方案是在 config.json 的 providers 里把 api_base 改为代理地址，也可以直接换用 DeepSeek 这样的国内 Provider。
>
> 另一个是 context_window_tokens 的设置问题。一开始我设得比较大，结果发现记忆压缩一直不触发，对话越来越长导致 API 费用很高。后来理解了这个参数的作用——当 `estimate_prompt_tokens_chain` 超过这个值时才会触发 Consolidator——就把它调到了一个合理的范围。
>
> 还有一个工具调用权限的问题，默认的 `restrict_to_workspace` 配置会限制 Agent 只能操作 workspace 内的文件，一开始没理解，尝试让 Agent 操作外部文件时总是失败。理解了这个安全机制后，我反而觉得这是一个很好的设计。"

---

## 6.12 本章小结

### 核心知识点回顾

| 知识点 | 要点 |
|--------|------|
| 安装方式 | pip install / uv tool install / 源码安装 |
| 配置向导 | `nanobot onboard` 交互式生成 config.json |
| 核心配置 | agents.defaults / providers / channels / tools |
| 关键参数 | context_window_tokens, max_tool_iterations |
| 引导文件 | SOUL.md → AGENTS.md → USER.md → TOOLS.md |
| 运行模式 | `nanobot` 直接进入交互模式 |

### 面试核心要点

1. **安装方式**：推荐 uv，解释 uv 的优势
2. **配置设计**：JSON + Markdown 双配置体系
3. **关键参数**：context_window_tokens 与记忆压缩的关系
4. **引导文件**：四层引导体系的设计理念
5. **实际经验**：能描述具体问题和解决方案

---

> **下一章**：[07 - 记忆系统实战](../07-memory-system/README.md) —— 深入理解 Nanobot 的双层记忆架构