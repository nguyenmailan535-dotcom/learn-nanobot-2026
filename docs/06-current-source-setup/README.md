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

以 2026-09-24 current-source README 为准：

| 项目 | 要求 |
|---|---|
| Python | **3.11+** |
| 操作系统 | macOS / Linux / Windows |
| Git | Source install 需要 |
| Bun | Source checkout 的前端/TUI开发流程需要；发布 wheel 已包含 WebUI |
| LLM Credential | 至少一个可用 Provider/Model |

```powershell
python --version
git --version
bun --version
```

### 6.2.2 Python 环境配置

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

Linux/macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

### 6.2.3 LLM API Key 准备

Credential 建议放环境变量。current `config.json` 的字符串值支持 `${VAR_NAME}`：

```json
{
  "providers": {
    "groq": {
      "apiKey": "${GROQ_API_KEY}"
    }
  }
}
```

启动时会在内存中解析，解析后的 Secret 不会写回配置文件。

## 6.3 安装 Nanobot

### 6.3.1 方式一：pip 安装（通用）

```bash
python -m pip install nanobot-ai
nanobot --version
```

### 6.3.2 方式二：uv 工具安装

```bash
uv tool install nanobot-ai
nanobot --version
```

### 6.3.3 方式三：从源码安装（本教程推荐）

本教程学习的是 2026-09-24 的 current-source：

```bash
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

editable install 让 checkout 中源码修改直接被当前环境使用，适合下断点和跑测试。

### 6.3.4 安装后验证

```bash
nanobot --version
nanobot status
nanobot --help
git rev-parse HEAD
```

遇到教程与行为不一致，先比较版本和 commit。

## 6.4 配置向导 nanobot onboard

### 6.4.1 运行配置向导

current-source 仍支持：

```bash
nanobot onboard --wizard
```

本地桌面首次使用也可以直接：

```bash
nanobot webui
```

然后在 **Settings → Models** 配置首个 Provider / Model。

### 6.4.2 向导流程详解

核心是生成或更新：

```text
~/.nanobot/config.json
```

通常需要确定 Provider、Model/Model Preset、Credential、Workspace，以及可选的 Channel/MCP/Security 配置。

### 6.4.3 向导生成的文件

默认 Agent Workspace：

```text
~/.nanobot/workspace/
├── AGENTS.md
├── SOUL.md
├── USER.md
├── HEARTBEAT.md
├── memory/
├── skills/
├── plugins/
└── cron/
```

Session 默认在 Runtime data directory 的：

```text
sessions/<workspace-id>/*.jsonl
```

而不是简单放在 Workspace 根目录。

## 6.5 config.json 配置详解

### 6.5.1 current 配置结构

current-source 使用 **JSON + Pydantic Schema**。主要区域：

```text
agents.defaults
modelPresets
providers
channels
tools
gateway
transcription
```

简化示例：

```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.nanobot/workspace",
      "modelPreset": "primary"
    }
  },
  "providers": {
    "groq": {
      "apiKey": "${GROQ_API_KEY}"
    }
  },
  "modelPresets": {
    "primary": {
      "provider": "groq",
      "model": "YOUR_MODEL"
    }
  },
  "tools": {
    "restrictToWorkspace": true
  }
}
```

具体 Provider/Model 名以当前 catalog 和账号为准。

### 6.5.2 agents.defaults 字段详解

current snapshot 中值得记住：

| 字段 | 默认值/含义 |
|---|---|
| `contextWindowTokens` | 200000 |
| `temperature` | 0.1 |
| `maxToolIterations` | 200 |
| `maxConcurrentSubagents` | 4 |
| `maxToolResultChars` | 16000 |
| `providerRetryMode` | standard |
| `idleCompactAfterMinutes` | 15 分钟 |
| `idleCompactCheckIntervalSeconds` | 60 秒 |
| `unifiedSession` | 是否跨 Channel 共用 Session |
| `disabledSkills` | 禁用 Skill |
| `dream` | Dream 长期记忆配置 |

### 6.5.3 providers 配置

Provider Credential 与 `modelPresets` 分离，使一个 Provider 可服务多个模型配置，并允许 Session 选择不同 Preset。

### 6.5.4 channels 配置

生产使用除 Token/Secret 外，还要关注 `allowFrom` / pairing、group policy、streaming 等访问控制。

### 6.5.5 tools 配置

重点字段：

```text
tools.restrictToWorkspace
tools.exec.enable
tools.exec.sandbox
tools.ssrfWhitelist
tools.mcpServers
tools.web
```

MCP 示例：

```json
{
  "tools": {
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/safe/path"],
        "enabledTools": ["read_file"]
      }
    }
  }
}
```

### 6.5.6 配置文件查找与环境变量

默认配置是 `~/.nanobot/config.json`。字符串值可使用 `${VAR_NAME}`；缺失变量会 fail fast 并指出具体字段。

多实例使用不同 Config / Workspace / Port，参见 current `docs/multiple-instances.md`。

## 6.6 第一次运行：交互模式

### 6.6.1 启动 Agent

Native Terminal：

```bash
nanobot
```

兼容形式：

```bash
nanobot agent
```

One-shot：

```bash
nanobot agent -m "Reply only with setup-ok"
```

WebUI：

```bash
nanobot webui
```

长期 Gateway：

```bash
nanobot gateway --background
nanobot gateway status
nanobot gateway logs
nanobot gateway restart
nanobot gateway stop
```

### 6.6.2 交互界面

WebUI 还提供 persistent topics、temporary chats、Workspace、Models、Apps/MCP、Skills、Automations 与 Settings。

### 6.6.3 常用交互命令

以 current `docs/chat-commands.md` 为准。源码学习建议重点试：

```text
/model
/skill
/compact
/dream
/dream-log
/trigger
/pairing
```

### 6.6.4 观察 Agent 的行为

至少观察：

```text
Session JSONL
Tool Call / Tool Result
Turn Stage Log
effective Workspace
selected Model / Preset
```

打开 verbose Gateway 时，还能观察 Channel/MCP 的启动和 Tool Registration。

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

### 6.8.1 SOUL.md —— 全局人格

`SOUL.md` 属于 Agent Workspace，是 current `ContextBuilder.BOOTSTRAP_FILES` 之一。适合保存稳定人格、沟通风格、长期行为规则；Dream 可以更新它。

### 6.8.2 USER.md —— 用户画像

`USER.md` 记录跨 Session 稳定的用户信息和偏好，也属于 Agent Workspace。

### 6.8.3 TOOLS.md —— current-source 中不再是固定 Bootstrap

旧教程把 `TOOLS.md` 当作固定引导文件。current-source 的定义是：

```python
BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md"]
```

Tool 能力主要来自 ToolLoader/ToolRegistry、Tool Schema、Skills、MCP 和 Agent Plugins。

如果自行创建 `TOOLS.md`，不要假设它会自动进入每轮 Context，除非通过其他机制显式加载。

### 6.8.4 文件优先级与覆盖关系

current-source 还区分 Agent Workspace 与 Effective Project Workspace：

| 状态 | Owner |
|---|---|
| SOUL.md / USER.md / memory/ | Agent Workspace |
| Workspace Skills / Plugins | Agent Workspace |
| Project AGENTS.md | Project Workspace |
| 相对文件路径 / Shell cwd | Project Workspace |
| Session JSONL | Runtime data directory / workspace namespace |

这是多 Project 场景下理解 Context 与文件权限的基础。

## 6.9 常见问题排错

### 6.9.1 安装问题

**问题 1：`nanobot: command not found`**

```bash
# 原因：安装路径不在 PATH 中
# 解决方案 1：检查 pip 安装路径
pip show nanobot-ai | grep Location

# 解决方案 2：使用 python -m
python -m nanobot

# 解决方案 3：使用 uv 重新安装
uv tool install nanobot-ai
```

**问题 2：Python 版本不兼容**

```bash
# 报错：requires Python >= 3.10
# 解决：升级 Python
pyenv install 3.12.0
pyenv global 3.12.0

# 或使用 conda
conda create -n nanobot python=3.12 -y
```

**问题 3：依赖冲突**

```bash
# 使用虚拟环境隔离
python -m venv nanobot-env
source nanobot-env/bin/activate
pip install nanobot-ai
```

### 6.9.2 配置问题

**问题 4：API Key 无效**

```bash
# 报错：Authentication failed / Invalid API key
# 排查步骤：
# 1. 确认 key 是否正确复制（无多余空格）
# 2. 确认 provider 与 key 匹配
# 3. 测试 key 是否有效
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-xxx"
```

**问题 5：模型不存在**

```bash
# 报错：Model not found
# 原因：model 字段与 provider 不匹配
# 例如：provider 设置为 deepseek，但 model 设置为 gpt-4o

# 正确配置：
# provider: "deepseek" → model: "deepseek-chat"
# provider: "openai"   → model: "gpt-4o"
```

**问题 6：连接超时**

```bash
# 国内用户常见问题
# 解决方案 1：使用代理
export https_proxy=http://127.0.0.1:7890

# 解决方案 2：使用国内 Provider
# 配置 DeepSeek 或其他国内模型服务

# 解决方案 3：使用 api_base 指向代理地址
{
  "providers": {
    "openai": {
      "api_key": "sk-xxx",
      "api_base": "https://your-proxy.example.com/v1"
    }
  }
}
```

### 6.9.3 运行时问题

**问题 7：记忆文件找不到**

```bash
# 确认 workspace 配置是否正确
cat config.json | python -m json.tool | grep workspace

# 手动创建记忆目录
mkdir -p memory
```

**问题 8：工具调用失败**

```bash
# 常见原因：
# 1. restrict_to_workspace 限制了文件访问范围
# 2. exec 工具被禁用
# 3. web_search 没有配置 API Key

# 检查工具配置
cat config.json | python -m json.tool | grep -A 5 tools
```

---

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

### 话术 1：描述你如何搭建 Nanobot 环境

> **面试官**：你有使用过 AI Agent 框架吗？能描述一下搭建过程吗？
>
> **参考回答**：
>
> "有的，我深入学习并使用过 HKUDS/nanobot 框架。搭建过程主要分几步：
>
> 首先是环境准备，Nanobot 要求 Python 3.10 以上，我用的是 uv 来安装，因为它比 pip 快很多。安装命令是 `uv tool install nanobot-ai`，这样会创建独立的虚拟环境，不污染全局。
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
> 另一个是 context_window_tokens 的设置问题。一开始我设得比较大，结果发现记忆压缩一直不触发，对话越来越长导致 API 费用很高。后来理解了这个参数的作用——当 `estimate_prompt_tokens_chain` 超过这个值时才会触发 MemoryConsolidator——就把它调到了一个合理的范围。
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

> **下一章**：[07 - 记忆系统实战](../07-memory-and-dream/README.md) —— 深入理解 Nanobot 的双层记忆架构