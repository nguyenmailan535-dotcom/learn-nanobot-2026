# 06 - Current-source 安装与第一次动手：Config / Workspace / Session

> 🎯 **本章目标**：不再按旧教程的安装命令操作，而是以 2026-09-24 current-source 为准完成 editable install，跑通 CLI/WebUI，并亲自确认 Config、Agent Workspace、Project Workspace、Session 的真实路径和职责。

---

## 目录

- [6.1 为什么这一章必须重写](#61-为什么这一章必须重写)
- [6.2 环境要求](#62-环境要求)
- [6.3 Stable Package 与 Current Source](#63-stable-package-与-current-source)
- [6.4 Windows 下安装 Current Source](#64-windows-下安装-current-source)
- [6.5 第一次配置 Provider](#65-第一次配置-provider)
- [6.6 五个 Runtime 入口](#66-五个-runtime-入口)
- [6.7 Config 目录](#67-config-目录)
- [6.8 Agent Workspace](#68-agent-workspace)
- [6.9 Project Workspace](#69-project-workspace)
- [6.10 Session 持久化](#610-session-持久化)
- [6.11 Bootstrap Files](#611-bootstrap-files)
- [6.12 最小验证实验](#612-最小验证实验)
- [6.13 常见问题](#613-常见问题)
- [6.14 面试高频题](#614-面试高频题)
- [6.15 本章总结](#615-本章总结)

---

## 6.1 为什么这一章必须重写

旧版教程中的 Python 版本、安装流程、Config Path、入口命令和 UI 使用方式已经发生明显变化。

current-source 学习必须先明确：

~~~text
你是在学 stable release
还是 current main？
~~~

本仓库目标是：

> **源码学习以 2026-09-24 的 main 为准。**

因此推荐 editable checkout。

---

## 6.2 环境要求

current source：

- Python 3.11+；
- Git；
- Bun：源码 checkout 中匹配的 TUI/Web 开发流程会用到；
- 一个可用 LLM Provider Credential。

检查：

~~~powershell
python --version
git --version
bun --version
~~~

如果 Python 仍是 3.10，不建议硬装 current source。

---

## 6.3 Stable Package 与 Current Source

### Stable Package

优点：

- 相对稳定；
- 安装快；
- 适合日常使用。

### Current Source

优点：

- 与 GitHub main 同步；
- 可以下断点；
- 可以追真实源码；
- 可以看到最新 architecture。

缺点：

- 文档可能领先 stable wheel；
- API 可能继续变化。

### 本课程规则

每次学习前记录：

~~~powershell
nanobot --version
git rev-parse HEAD
~~~

以后出现“为什么我的输出和教程不一样”，先判断版本。

---

## 6.4 Windows 下安装 Current Source

### Step 1：Clone

~~~powershell
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
~~~

### Step 2：虚拟环境

~~~powershell
python -m venv .venv
..venvScriptsActivate.ps1
~~~

### Step 3：Editable Install

~~~powershell
python -m pip install -U pip
python -m pip install -e .
~~~

为什么 editable？

~~~text
修改本地源码
→ 当前环境立即使用修改后的 package
~~~

非常适合 source trace。

### Step 4：验证

~~~powershell
nanobot --version
nanobot status
~~~

---

## 6.5 第一次配置 Provider

优先使用：

~~~powershell
nanobot onboard --wizard
~~~

或者 WebUI Settings → Models。

### 不要做

~~~text
API key 写进 GitHub
key 写进 AGENTS.md
key 写进 Skill
key 写进 MCP command args
~~~

### 要分清

~~~text
Provider
Model
API Base
Credential
~~~

OpenAI-compatible API 不代表 Provider 名一定是 OpenAI。

---

## 6.6 五个 Runtime 入口

### One-shot

~~~powershell
nanobot agent -m "Reply only with setup-ok"
~~~

### Terminal

~~~powershell
nanobot agent
~~~

### WebUI

~~~powershell
nanobot webui
~~~

### Gateway

~~~powershell
nanobot gateway
~~~

### OpenAI-compatible API

~~~powershell
nanobot serve
~~~

具体 API plugin/config 以 current docs 为准。

### 为什么要理解入口差异

它们不是五套 Agent，而是不同 Surface/Composition Root。

~~~text
不同入口
→ 组装同一核心 Runtime
→ 但额外 Infrastructure 不完全相同
~~~

Gateway 会额外承载 Channels / Automations 等长期服务。

---

## 6.7 Config 目录

默认：

~~~text
~/.nanobot/config.json
~~~

相关源码：

~~~text
nanobot/config/schema.py
nanobot/config/loader.py
nanobot/config/paths.py
~~~

Config 管：

- Providers；
- Model Presets；
- Tools；
- MCP；
- Channels；
- Gateway；
- Agent Defaults；
- Security。

### 值得看的源码点：Config Migration

current loader 包含旧配置迁移逻辑。

例如旧字段：

~~~text
tools.exec.restrictToWorkspace
~~~

迁移到 current：

~~~text
tools.restrictToWorkspace
~~~

这说明真实软件升级不仅是“增加新字段”，还要考虑旧用户配置。

---

## 6.8 Agent Workspace

默认：

~~~text
~/.nanobot/workspace/
~~~

这是 Agent-owned state。

可能包含：

~~~text
AGENTS.md
SOUL.md
USER.md
memory/
skills/
plugins/
cron/
~~~

### Workspace 不等于源码目录

即使 Nanobot clone 在：

~~~text
E:
anobot
~~~

Agent Workspace 也不自动等于这个 repo。

---

## 6.9 Project Workspace

WebUI 可以让某个 Chat 选择 Project Workspace。

此时：

~~~text
Agent Workspace
→ identity / memory / skills

Project Workspace
→ project AGENTS / relative files / shell cwd
~~~

### 实验

准备：

~~~text
project-A/AGENTS.md
project-B/AGENTS.md
~~~

写不同规则。

WebUI 切换 project 后问：

~~~text
What project instruction are you following?
~~~

同时确认 USER/MEMORY 没跟项目一起换掉。

---

## 6.10 Session 持久化

current default：

~~~text
<config-dir>/sessions/<workspace-id>/*.jsonl
~~~

相关源码：

~~~text
nanobot/session/manager.py
~~~

SessionManager 当前职责：

> Manage session identity, caching, retention, and persistence.

Session 不只是聊天文本，还可能含：

- metadata；
- provider state；
- summary；
- runtime checkpoint；
- routing 信息。

### 为什么不放普通 Workspace 文件区

Session 属于 Runtime Data，和用户让 Agent 编辑的项目文件不是同一类状态。

workspace-id 还能让不同 Agent Workspace 的 Session namespace 隔离。

---

## 6.11 Bootstrap Files

ContextBuilder 当前定义：

~~~python
BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md"]
~~~

### AGENTS.md

行为/项目指导。

### SOUL.md

长期 Agent personality/style，后续可由 Dream 管理。

### USER.md

用户稳定 profile/preferences，可由 Dream 更新。

### MEMORY.md

位于：

~~~text
memory/MEMORY.md
~~~

由 MemoryStore 提供 long-term memory context。

---

## 6.12 最小验证实验

### Experiment 06A：CLI → Session

1. 运行：

~~~powershell
nanobot agent
~~~

2. 连续两轮对话；
3. 找 Session JSONL；
4. 对照实际消息。

记录：

~~~text
session key
jsonl path
message count
metadata
~~~

### Experiment 06B：Project Scope

1. 建 project-A / project-B；
2. 各写 AGENTS；
3. WebUI 切 Project；
4. 让 read_file 读取相对路径；
5. 看实际作用目录。

### Experiment 06C：One-shot vs Gateway

分别跑：

~~~powershell
nanobot agent -m "..."
nanobot gateway
~~~

用日志观察 Composition Root 差异。

---

## 6.13 常见问题

### nanobot 命令找不到

~~~powershell
Get-Command python
Get-Command nanobot
~~~

确认当前 venv。

### 源码改了没生效

确认当前环境确实执行：

~~~text
pip install -e .
~~~

并检查 Python/Nanobot 路径。

### 项目文件访问被拒

优先检查：

~~~text
effective project workspace
tools.restrictToWorkspace
sandbox
~~~

不要先关安全配置。

### stable wheel 与 main 文档行为不同

这是可能的。记录版本和 git SHA 后，以你正在运行的源码为准。

---

## 6.14 面试高频题

### Q1：Editable Install 为什么适合源码学习？

> 环境直接引用 checkout 中源码，改代码、下断点、跑 Test 不需要每次重新打 Wheel。

### Q2：Config、Workspace、Session 有什么区别？

- Config：Runtime 配置；
- Workspace：Agent-owned durable state；
- Session：Conversation/runtime persistence；
- Project Workspace：当前项目文件和 Tool 工作边界。

### Q3：为什么 current source 要兼容旧 Config？

真实产品有升级路径；安全迁移已有配置本身就是工程能力。

---

## 6.15 本章总结

你应该真正区分：

~~~text
Source Checkout
≠
Config Dir
≠
Agent Workspace
≠
Project Workspace
≠
Session Store
~~~

下一章进入 current-source 变化最大的部分之一：Session、AutoCompact、Consolidation 和 Dream 如何组成新版 Memory System。
