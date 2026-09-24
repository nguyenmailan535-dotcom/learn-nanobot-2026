# 02 - Nanobot 2026 项目概览：不要再用“4000 行小框架”理解它

> 🎯 **本章目标**：建立 2026-09-24 current-source 的完整产品与源码地图，知道 WebUI、Gateway、AgentLoop、AgentRunner、Tools、Memory、Plugins、Channels、Automations 各自在什么位置。

---

## 目录

- [2.1 为什么必须重写旧版项目概览](#21-为什么必须重写旧版项目概览)
- [2.2 Nanobot 当前定位](#22-nanobot-当前定位)
- [2.3 五个主要使用入口](#23-五个主要使用入口)
- [2.4 Current-source 能力全景](#24-current-source-能力全景)
- [2.5 第一次应该看哪些源码](#25-第一次应该看哪些源码)
- [2.6 一条最重要的 Runtime 主链](#26-一条最重要的-runtime-主链)
- [2.7 Config、Workspace、Session](#27-configworkspacesession)
- [2.8 为什么 Nanobot 仍适合源码学习](#28-为什么-nanobot-仍适合源码学习)
- [2.9 旧教程与 current-source 的关键差异](#29-旧教程与-current-source-的关键差异)
- [2.10 第一次上手实验](#210-第一次上手实验)
- [2.11 面试话术](#211-面试话术)
- [2.12 本章总结](#212-本章总结)

---

## 2.1 为什么必须重写旧版项目概览

早期 Nanobot 经常被描述成：

~~~text
约 4000 行 Python
一个周末读完
MEMORY.md + HISTORY.md
一个简单 AgentLoop
~~~

这个描述已经不能代表 2026-09 的 current-source。

当前官方仓库已经包含：

- CLI / TUI；
- WebUI / WebSocket；
- Gateway；
- OpenAI-compatible API；
- Python SDK；
- Provider routing / model presets；
- Tool discovery；
- MCP；
- Agent Plugins v1；
- Skills progressive loading；
- Session / AutoCompact / Consolidation / Dream；
- Subagent；
- Cron / Trigger / Heartbeat；
- 多种 chat channels；
- workspace / project scope；
- sandbox / SSRF / pairing；
- hooks / runtime events / usage tracking。

因此现在再把它概括为“4000 行轻量框架”，反而会让你的面试回答显得过时。

更准确的学习定位是：

> **Nanobot 是一套仍然可读，但已经接近真实产品形态的 self-hosted Agent Runtime。**

---

## 2.2 Nanobot 当前定位

可以把项目分成四层：

~~~text
Product Surfaces
CLI / TUI / WebUI / Chat Apps / API / SDK
              ↓
Runtime Orchestration
Gateway / MessageBus / AgentLoop
              ↓
Model Execution
AgentRunner / Provider / Tools
              ↓
Persistent State
Session / Memory / Skills / Plugins / Cron
~~~

### 它为什么不是“聊天机器人”

如果只是问答：

~~~text
prompt → LLM → answer
~~~

完全不需要 SessionManager、Gateway、MCPProvider、CronService、ChannelManager 等模块。

这些模块存在说明项目真正解决的是：

> 一个 Agent 如何长期运行、接多个入口、执行真实工具、隔离会话、维护状态并控制安全边界。

---

## 2.3 五个主要使用入口

### 2.3.1 One-shot CLI

~~~powershell
nanobot agent -m "Hello!"
~~~

适合：

- smoke test；
- CI；
- 快速验证 provider/config；
- 自动脚本。

### 2.3.2 Terminal Agent

~~~powershell
nanobot agent
~~~

适合源码调试，因为 UI 噪声少。

### 2.3.3 WebUI

~~~powershell
nanobot webui
~~~

当前 WebUI 已经不只是聊天页面，还承担：

- conversation/workspace 管理；
- model selection；
- settings；
- Apps / MCP / Agent Plugins；
- channels 配置；
- session 管理。

### 2.3.4 Gateway

~~~powershell
nanobot gateway
~~~

Gateway 是长期运行场景的宿主。

官方 architecture 文档说明它承载：

~~~text
enabled chat channels
WebSocket / packaged WebUI
workspace-scoped cron
Dream system job
heartbeat system job
health endpoint
~~~

### 2.3.5 OpenAI-compatible API / Python SDK

~~~text
nanobot serve
Python SDK
~~~

说明同一 runtime 可以嵌入其他应用，而不是只能通过 Nanobot 自带 UI 使用。

---

## 2.4 Current-source 能力全景

| 能力 | 作用 | 关键入口 |
|---|---|---|
| Provider | 接不同模型后端 | nanobot/providers/ |
| Model Runtime | model/preset/context window | agent/model_runtime.py |
| AgentLoop | session-facing turn orchestration | agent/loop.py |
| AgentRunner | provider/tool loop | agent/runner.py |
| Context | prompt/messages 构造 | agent/context.py |
| Tools | Files/Shell/Web/MCP 等 | agent/tools/ |
| Skills | 工作方法/领域说明 | agent/skills.py |
| Plugins | Skill + MCP package | agent/plugins.py |
| Session | conversation persistence | session/manager.py |
| Memory | archive + durable memory | agent/memory.py |
| AutoCompact | idle session 压缩 | agent/autocompact.py |
| Subagent | 后台/内联子 Agent | agent/subagent.py |
| Channels | 外部消息平台 | channels/ |
| Cron | 定时任务 | cron/ |
| Local Trigger | 外部本地事件 | triggers/ |
| Security | path/network/sandbox | security/ |

---

## 2.5 第一次应该看哪些源码

不要一上来完整 tree 后逐个打开。

第一阶段只看：

~~~text
nanobot/
├── bus/
│   ├── events.py
│   └── queue.py
│
├── agent/
│   ├── loop.py
│   ├── runner.py
│   ├── context.py
│   ├── memory.py
│   ├── autocompact.py
│   ├── subagent.py
│   ├── skills.py
│   ├── plugins.py
│   └── tools/
│       ├── registry.py
│       ├── loader.py
│       ├── filesystem.py
│       ├── shell.py
│       ├── web.py
│       └── mcp.py
│
├── session/
│   └── manager.py
│
├── channels/
│   ├── base.py
│   └── manager.py
│
└── config/
    ├── schema.py
    ├── loader.py
    └── paths.py
~~~

第二阶段再看：

~~~text
webui/
api/
cron/
triggers/
security/
sdk/
~~~

### 为什么这样读

因为学习一个系统最先要知道：

~~~text
输入是什么
状态在哪里
核心执行器是谁
输出到哪里
~~~

而不是先钻进某个 Feishu SDK callback。

---

## 2.6 一条最重要的 Runtime 主链

官方 current architecture：

~~~mermaid
flowchart LR
    Channel["Channel<br/>CLI / WebUI / Chat Apps"]
    Bus["MessageBus<br/>InboundMessage"]
    Loop["AgentLoop<br/>session / workspace / context"]
    Runner["AgentRunner<br/>provider/tool loop"]
    Provider["Provider"]
    Tools["Tools"]
    State["Session / Memory / Skills"]
    Out["OutboundMessage"]

    Channel --> Bus --> Loop --> Runner
    Runner --> Provider --> Runner
    Runner --> Tools --> Runner
    Runner --> Loop --> Out --> Channel
    Loop -. reads/writes .-> State
~~~

这张图后面会反复出现。

### 为什么 MessageBus 在中间

Channel 不应该知道：

- Session 怎么存；
- Provider 怎么调；
- Tool 怎么执行。

Channel 只负责：

~~~text
platform-specific event
↔
InboundMessage / OutboundMessage
~~~

所以 Telegram、Feishu、WebSocket 都能复用同一 Agent Core。

---

## 2.7 Config、Workspace、Session

默认路径：

| 类型 | 默认位置 |
|---|---|
| Config | ~/.nanobot/config.json |
| Agent Workspace | ~/.nanobot/workspace/ |
| Sessions | config-dir/sessions/workspace-id/ |
| Memory | workspace/memory/ |
| Cron | workspace/cron/jobs.json |

### Config

存 runtime 配置：

- providers；
- models；
- channels；
- tools；
- security；
- gateway。

### Agent Workspace

存 Agent 拥有的长期状态：

~~~text
AGENTS.md
SOUL.md
USER.md
memory/
skills/
plugins/
cron/
~~~

### Session

存 conversation replay 和 metadata。

### Effective Project Workspace

WebUI 还允许一个对话选择另一个 project。

这时候：

| Concern | 跟谁走 |
|---|---|
| SOUL / USER / Memory | Agent Workspace |
| custom skills | Agent Workspace |
| project AGENTS.md | Project Workspace |
| relative file path | Project Workspace |
| shell cwd | Project Workspace |

所以以后遇到“为什么 Agent 记忆没跟着项目切换”，不是 bug，而是 ownership 设计。

---

## 2.8 为什么 Nanobot 仍适合源码学习

不是因为“只有几千行”。

### 1. Core Boundary 很清楚

你可以明确指出：

~~~text
AgentLoop
AgentRunner
ContextBuilder
ToolRegistry
SessionManager
MCPProvider
~~~

各自负责什么。

### 2. 能看到产品级问题

例如：

- per-session FIFO；
- mid-turn injection；
- recovery checkpoint；
- streaming delivery；
- automation routing；
- workspace sandbox；
- MCP lifecycle。

这些问题在教学 Demo 里基本看不到。

### 3. 可以做局部最小实验

你可以单独测试：

~~~text
context build
tool execute
session save
dream
subagent
MCP
~~~

而不必每次启动整套 UI。

---

## 2.9 旧教程与 current-source 的关键差异

| 旧教程常见说法 | Current-source |
|---|---|
| 一个简单 AgentLoop 包揽全部 | AgentLoop / AgentRunner 分层 |
| MEMORY.md + HISTORY.md | Session + history.jsonl + Dream durable files |
| 固定 global semaphore=3 | NANOBOT_MAX_CONCURRENT_REQUESTS，默认 unlimited |
| Subagent 固定较小迭代数 | 跟 current runtime/defaults 配置联动 |
| 飞书依赖公网 webhook/ngrok | current guide 支持 WebSocket long connection / QR login |
| MCP 是 Loop 内部附属 | MCPProvider 是 application-owned infrastructure |
| Skills 只有 workspace/builtin | workspace + Agent Plugin + built-in |
| 配置主要靠手改 | WebUI Settings + JSON schema + CLI |
| 只有对话入口 | Gateway / WebUI / API / SDK / Channels |

---

## 2.10 第一次上手实验

暂时不要接 MCP 和飞书。

### Step 1：查看状态

~~~powershell
nanobot status
~~~

记录：

- config path；
- workspace path；
- selected model。

### Step 2：One-shot

~~~powershell
nanobot agent -m "Reply only with current-runtime-ok"
~~~

### Step 3：WebUI

~~~powershell
nanobot webui
~~~

建立一个 session，连续问两轮。

### Step 4：看真实持久化

找到 session JSONL，对照 WebUI 两轮消息。

你的目标是把：

~~~text
界面中的 Conversation
↔
SessionManager 持久化的数据
~~~

对应起来。

---

## 2.11 面试话术

不要再说：

> Nanobot 是一个 4000 行轻量框架，我把全部源码读完了。

更可信的说法：

> 我用 Nanobot current-source 学习 Agent Runtime，重点追过 MessageBus → AgentLoop → AgentRunner → ToolRegistry → Session 的完整链路。新版已经包含 Gateway、WebUI、MCP、Dream、Subagent 和 Automations，所以我没有按旧教程背固定架构，而是按 current source 做最小实验验证各层边界。

---

## 2.12 本章总结

把 Nanobot 压缩成：

~~~text
Surfaces
   ↓
Gateway / MessageBus
   ↓
AgentLoop
   ↓
Context + Session
   ↓
AgentRunner
   ↔ Provider
   ↔ Tools
   ↓
Persistence / Delivery
~~~

下一章进入真正的架构深挖：**一个 Turn 为什么要拆成多个阶段，以及 AgentLoop 与 AgentRunner 到底如何协作。**
