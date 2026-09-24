# 06 - 安装与上手

> **阅读时间**：约 2 小时  
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

2026-09-24 current-source 建议：

- Python **3.11+**
- Git
- 一个可用的 LLM Provider Credential
- 如果参与 WebUI/TUI 源码开发，再准备 current repo 对应的 Bun/前端环境

检查：

```powershell
python --version
git --version
```

> 原版教程中的“Python 3.10.x 或更高”已经不再作为 current-source 基线，本课程统一按 Python 3.11+。

### 6.2.2 为什么要建独立虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

源码学习时不要把实验依赖装进系统 Python。

### 6.2.3 LLM API Key

可以使用官方支持的 Provider 或任意兼容路径。重点是：

- Credential 放环境变量或受保护的配置
- 不写进 Git
- 不写进 AGENTS/SKILL
- 不把 Secret 放 MCP command args

---

## 6.3 安装 Nanobot

### 6.3.1 学 current-source：推荐 Editable Install

```powershell
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Editable Install 的价值：

```
本地源码修改
→ 当前 Python 环境立即使用
→ 可以下断点 / 跑 Test / Source Trace
```

### 6.3.2 Stable Package

如果只是日常使用，可以安装发布版本；但本课程涉及 `main` 源码，因此所有源码结论都以学习快照为准，不保证与旧 stable wheel 完全一致。

### 6.3.3 验证

```powershell
nanobot --version
nanobot status
git rev-parse HEAD
```

建议把 version + commit SHA 写进学习笔记。

---

## 6.4 配置向导 nanobot onboard

### 6.4.1 首次配置

current-source 可以使用：

```powershell
nanobot onboard --wizard
```

也可以通过 WebUI Settings 完成 Provider、Model、Channel、MCP 等配置。

### 6.4.2 current 默认路径

```
~/.nanobot/config.json
~/.nanobot/workspace/
~/.nanobot/sessions/<workspace-id>/
```

不要再把“当前工作目录下的 my-agent/config.json + sessions/”当成唯一模式。

### 6.4.3 为什么要先跑 status

```powershell
nanobot status
```

确认：

- 实际读取哪个 config
- 实际 Agent Workspace
- 当前 model/provider

很多“我改了配置但没生效”的问题，本质是改错实例。

---

## 6.5 config.json 配置详解

current schema 主要位于：

```
nanobot/config/schema.py
nanobot/config/loader.py
nanobot/config/paths.py
```

常见区域：

```json
{
  "agents": {
    "defaults": {}
  },
  "providers": {},
  "modelPresets": {},
  "tools": {},
  "channels": {},
  "gateway": {}
}
```

### 6.5.1 CamelCase 与兼容

schema 能兼容部分 snake_case / legacy 字段，但 current 保存配置时以 camelCase aliases 为主。

例如 current 安全字段：

```
tools.restrictToWorkspace
tools.exec.sandbox
tools.ssrfWhitelist
```

loader 还会迁移旧配置，例如旧：

```
tools.exec.restrictToWorkspace
```

迁移到：

```
tools.restrictToWorkspace
```

### 6.5.2 MCP

current MCP 配置位于：

```
tools.mcpServers.<name>
```

也可以通过 WebUI Apps/MCP 管理。

### 6.5.3 Model Preset

current-source 不建议只理解为“全局固定 provider/model”；还支持 model presets 与 Session 级 model selection。

---

## 6.6 第一次运行：交互模式

### 6.6.1 One-shot Smoke Test

```powershell
nanobot agent -m "Reply only with setup-ok"
```

### 6.6.2 Terminal Agent

```powershell
nanobot agent
```

### 6.6.3 WebUI

```powershell
nanobot webui
```

### 6.6.4 Gateway

```powershell
nanobot gateway
```

Gateway 是长期运行入口，会承载 enabled chat channels、WebSocket/WebUI、Cron、Dream、Heartbeat 等系统任务。

### 6.6.5 OpenAI-compatible API

```powershell
nanobot serve
```

### 6.6.6 第一次观察文件

current ownership：

```
~/.nanobot/
├── config.json
├── sessions/
│   └── <workspace-id>/
└── workspace/
    ├── AGENTS.md
    ├── SOUL.md
    ├── USER.md
    ├── memory/
    │   ├── MEMORY.md
    │   └── history.jsonl
    ├── skills/
    ├── plugins/
    └── cron/
```

`HISTORY.md` 只应视为 legacy migration，而不是新安装后的长期历史主文件。

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

current ContextBuilder 的 bootstrap files：

```python
BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md"]
```

### 6.8.1 AGENTS.md

用于 Agent / Project Instructions。current-source 还区分：

- Agent Workspace 的 Agent-owned state
- Effective Project Workspace 的 Project AGENTS.md

### 6.8.2 SOUL.md

长期人格、行为风格、价值取向。Dream 可以维护它。

### 6.8.3 USER.md

稳定用户画像与长期偏好。Dream 可以维护它。

### 6.8.4 MEMORY.md

位于：

```
<agent-workspace>/memory/MEMORY.md
```

用于 long-term durable facts。

### 6.8.5 history.jsonl

位于：

```
<agent-workspace>/memory/history.jsonl
```

它是 Consolidation/Dream 的历史来源，不是每轮都全部塞进 Prompt。

### 6.8.6 Agent Workspace vs Project Workspace

| 内容 | Owner |
|---|---|
| SOUL / USER / MEMORY | Agent Workspace |
| Custom Skills / Plugins | Agent Workspace |
| Project AGENTS.md | Effective Project |
| Relative File Tool Path | Effective Project |
| Shell Working Directory | Effective Project |

## 6.9 常见问题排错

### 问题 1：nanobot 命令找不到

```powershell
Get-Command python
Get-Command nanobot
```

确认 terminal 使用正确 venv。

### 问题 2：源码改了没生效

确认使用：

```
pip install -e .
```

并记录 `git rev-parse HEAD`。

### 问题 3：配置改了没生效

先执行：

```powershell
nanobot status
```

确认 active config path。

### 问题 4：文件访问被拒

优先检查：

- Effective Project Workspace
- `tools.restrictToWorkspace`
- `tools.exec.sandbox`

不要第一反应关闭安全边界。

### 问题 5：WebUI 可以打开，但 Chat App 不工作

Chat Apps 要由 Gateway 长期运行；使用：

```powershell
nanobot channels status
nanobot gateway --verbose
```

排查 channel config、optional plugin、pairing/allowFrom。

### 问题 6：教程与本机行为不同

本仓库以 2026-09-24 current-source 为基线。先比较：

```
nanobot --version
git rev-parse HEAD
```

## 6.10 实战练习

### 练习 1：创建一个翻译助手

```bash
# 1. 创建项目目录
mkdir translator-agent && cd translator-agent

# 2. 初始化配置
nanobot onboard

# 3. 创建 AGENTS.md
cat > AGENTS.md << 'EOF'
# 翻译助手

你是一个专业的中英互译助手。

## 规则
- 中文输入 → 翻译为英文
- 英文输入 → 翻译为中文
- 保持原文的语气和风格
- 专业术语提供注释
EOF

# 4. 运行
nanobot
```

### 练习 2：创建一个代码审查助手

```bash
mkdir code-reviewer && cd code-reviewer
nanobot onboard
```

编写 AGENTS.md：

```markdown
# 代码审查助手

你是一位资深的代码审查专家。

## 职责
1. 审查用户提供的代码
2. 指出潜在的 Bug 和安全隐患
3. 提供优化建议
4. 检查代码风格一致性

## 审查流程
1. 先用 `read_file` 读取代码文件
2. 分析代码结构和逻辑
3. 逐一列出发现的问题
4. 给出改进后的代码示例

## 输出格式
- 🔴 严重问题（必须修复）
- 🟡 警告（建议修复）
- 🟢 建议（可选优化）
```

### 练习 3：观察记忆系统

```bash
# 1. 启动 Agent，进行几轮对话
nanobot

# 2. 对话内容示例：
# You: 我叫张三，是一名后端开发工程师
# You: 我最近在学习 Kubernetes
# You: 请记住我喜欢用 Python

# 3. 退出后检查记忆文件
cat memory/MEMORY.md
cat memory/HISTORY.md

# 4. 重新启动，验证 Agent 是否记住了你的信息
nanobot
# You: 我叫什么名字？
# Agent 应该能回答：你叫张三
```

---

## 6.11 面试话术

### 话术 1：描述你如何搭建 current-source

> “我学习的是 Nanobot main，所以不是只安装旧 stable 包。我先 clone 仓库，用 Python 3.11+ 建独立 venv，再 `pip install -e .` 做 editable install；随后用 `nanobot onboard --wizard` 或 WebUI 配 Provider，并用 `nanobot status` 确认实际 config/workspace/model。最后分别用 one-shot CLI、Terminal Agent 和 WebUI 做 Smoke Test，并记录 `git rev-parse HEAD` 保证源码结论可复现。”

### 话术 2：Config、Workspace、Session 怎么区分？

> “Config 默认在 `~/.nanobot/config.json`，描述 Provider、Model、Tool、Channel 和 Gateway；Agent Workspace 保存 SOUL/USER/Memory/Skills/Plugins；Session Store 位于 config data directory 下，保存 conversation/runtime state；WebUI 还可以选择 Effective Project Workspace，文件和 Shell 的相对路径跟 Project 走，但 Agent Memory 仍属于 Agent Workspace。”

### 话术 3：遇到文件访问失败怎么排查？

> “先确认 effective project workspace，再看 `tools.restrictToWorkspace` 和 `tools.exec.sandbox`。我不会为了调通直接关闭安全边界，而是先判断请求是否越出了当前 Project Scope。”

---

## 6.12 本章小结

| 知识点 | current-source 要点 |
|---|---|
| Python | 3.11+ |
| 源码安装 | 推荐 editable install：`pip install -e .` |
| 配置 | `~/.nanobot/config.json` |
| Agent Workspace | `~/.nanobot/workspace/` |
| Session | `<config-dir>/sessions/<workspace-id>/` |
| Bootstrap | AGENTS.md / SOUL.md / USER.md |
| Long-term History | `memory/history.jsonl`，不是旧 HISTORY.md 主路径 |
| Runtime 入口 | agent / webui / gateway / serve |
| 安全 | `tools.restrictToWorkspace` + 可选 exec sandbox |

真正的完成标准不是“命令跑起来”，而是你能指出当前实例实际使用的 Config、Workspace、Project Scope 和 Session Store，并知道它们为什么分开。
