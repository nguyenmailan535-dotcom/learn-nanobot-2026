# 08 - 技能与工具

> **阅读时间**：约 2 小时  
> **前置知识**：[07 - 记忆系统实战](../07-memory-and-dream/README.md)  
> **学习目标**：掌握 Nanobot 的 Skill 系统、内置工具体系、MCP 工具集成，能够自定义 Skill

---

## 目录

- [8.1 Skills 系统概述](#81-skills-系统概述)
- [8.2 SKILL.md 格式规范](#82-skillmd-格式规范)
- [8.3 YAML Frontmatter 字段详解](#83-yaml-frontmatter-字段详解)
- [8.4 技能发现机制](#84-技能发现机制)
- [8.5 渐进披露（Progressive Disclosure）](#85-渐进披露progressive-disclosure)
- [8.6 内置技能列表](#86-内置技能列表)
- [8.7 内置工具完整列表](#87-内置工具完整列表)
- [8.8 ToolRegistry 统一注册与执行机制](#88-toolregistry-统一注册与执行机制)
- [8.9 MCP 工具集成](#89-mcp-工具集成)
- [8.10 自定义 Skill 编写实战](#810-自定义-skill-编写实战)
- [8.11 工具安全机制](#811-工具安全机制)
- [8.12 面试高频题](#812-面试高频题)
- [8.13 本章小结](#813-本章小结)

---

## 8.1 Skills 系统概述

### 8.1.1 什么是 Skill？

在 Nanobot 中，**Skill（技能）** 是一种可插拔的能力扩展机制。你可以把它理解为"给 Agent 添加的专业模块"：

```
Agent 基础能力            Agent + Skills
┌──────────────┐        ┌──────────────┐
│ · 对话       │        │ · 对话       │
│ · 文件操作   │   →    │ · 文件操作   │
│ · Shell命令  │        │ · Shell命令  │
└──────────────┘        │ · GitHub管理 │  ← Skill
                        │ · 天气查询   │  ← Skill
                        │ · 内容总结   │  ← Skill
                        │ · 代码部署   │  ← Skill
                        └──────────────┘
```

### 8.1.2 Skill vs Tool 的区别

这是面试中容易混淆的概念：

| 维度 | Skill（技能） | Tool（工具） |
|------|-------------|-------------|
| 粒度 | 粗粒度（一个完整能力） | 细粒度（一个具体操作） |
| 定义方式 | Markdown 文件（SKILL.md） | Python 代码注册 |
| 包含内容 | 指令 + 脚本 + 参考资料 | 函数签名 + 执行逻辑 |
| 注入方式 | System Prompt | Tool Definition |
| 类比 | 一门专业课程 | 一个具体工具 |

**关系**：一个 Skill 可以**教会** Agent 如何更好地使用多个 Tool。

```
Skill: GitHub 管理
├── 知道如何创建 PR（指令）
├── 知道代码审查流程（知识）
└── 会使用以下 Tools：
    ├── exec（运行 git 命令）
    ├── read_file（读取代码）
    └── web_fetch（查看 GitHub API）
```

---

## 8.2 SKILL.md 格式规范

### 8.2.1 目录结构

每个 Skill 是一个独立的目录：

```
skill-name/
├── SKILL.md        # 技能定义文件（必需）
├── scripts/        # 可选：辅助脚本
│   ├── deploy.sh
│   └── check.py
├── references/     # 可选：参考资料
│   ├── api-docs.md
│   └── examples.md
└── assets/         # 可选：资源文件
    ├── template.json
    └── config.yaml
```

### 8.2.2 SKILL.md 文件格式

SKILL.md 由两部分组成：**YAML Frontmatter** + **Markdown 正文**。

```markdown
---
name: github
description: "GitHub 仓库管理、PR 创建与代码审查"
always: false
metadata: '{"nanobot.requires.bins": ["git", "gh"], "nanobot.requires.env": ["GITHUB_TOKEN"]}'
---

# GitHub 管理技能

## 能力

你可以帮助用户管理 GitHub 仓库，包括：

1. **创建和管理 Pull Request**
   - 创建 PR 并添加描述
   - 审查代码变更
   - 合并 PR

2. **Issue 管理**
   - 创建 Issue
   - 标签分类
   - 分配负责人

## 使用步骤

### 创建 PR

1. 先用 `exec` 运行 `git status` 检查当前状态
2. 确认所有变更已提交
3. 使用 `exec` 运行 `gh pr create --title "标题" --body "描述"`

### 代码审查

1. 用 `exec` 运行 `gh pr diff <PR号>`
2. 用 `read_file` 查看关键变更文件
3. 给出审查意见

## 注意事项

- 创建 PR 前确保分支已推送到远程
- 大型 PR 建议拆分为多个小 PR
- 代码审查时关注安全和性能问题

## 参考资料

更多细节请查看 `references/` 目录中的文档。
```

---

## 8.3 YAML Frontmatter 字段详解

### 8.3.1 必填字段

current `SkillsLoader` 会验证 Agent Skills identity：

| 字段 | 说明 |
|---|---|
| `name` | 必须与 Skill 目录名一致，满足命名规则 |
| `description` | 1-1024 字符，用于 Skill Summary / Discovery |

最小示例：

```yaml
---
name: literature-analysis
description: Analyze research papers with evidence-first retrieval and citations.
---
```

### 8.3.2 可选字段

current-source 支持 Nanobot/OpenClaw compatibility metadata。例如：

```yaml
---
name: github
description: Interact with GitHub using the gh CLI.
metadata:
  nanobot:
    emoji: "🐙"
    requires:
      bins: ["gh"]
      env: []
---
```

常见 metadata：

- `requires.bins`：依赖的本地命令；
- `requires.env`：依赖的环境变量；
- `always`：Nanobot-specific always-active 语义；
- 安装提示 / emoji 等 UI metadata。

### 8.3.3 always 字段详解

current loader 为兼容旧 Skill，同时识别：

```yaml
always: true
```

以及：

```yaml
metadata:
  nanobot:
    always: true
```

但不要滥用。

```text
always=true
→ Full Skill Instructions 每轮活跃
→ Context token 增长
→ Instruction collision 风险增长
```

大多数 Skill 更适合默认按需加载。

### 8.3.4 metadata 与依赖检查

`SkillsLoader` 会读取 `metadata.nanobot.requires`，检查：

```text
bins → shutil.which()
env  → os.environ
```

依赖不满足的 Skill 可以出现在 Summary 中，但标记 unavailable，使 Agent 知道为什么当前不能用。

---

## 8.4 技能发现机制

### 8.4.1 搜索路径

current-source 有三类来源：

```text
<workspace>/skills/             # Workspace Skills
<workspace>/plugins/*/skills/   # Enabled Agent Plugin Skills
nanobot/skills/                 # Built-in Skills
```

### 8.4.2 发现流程

```text
Workspace Skills
    ↓
Enabled Agent Plugin Skills
    ↓
Built-in Skills
    ↓
disabledSkills filter
    ↓
requirements filter
    ↓
Skills Summary / Active Skills
```

### 8.4.3 覆盖机制

current `list_skills()` 使用 `seen_names`，所以优先级可理解为：

```text
Workspace > Enabled Plugin > Built-in
```

这允许你在 Workspace 中用同名 Skill 覆盖系统默认，而不用修改安装包源码。

### 8.4.4 Agent Plugin 是 current 新边界

current `nanobot/agent/plugins.py` 支持 Agent Plugins v1。

典型：

```text
workspace/plugins/research-agent/
├── plugin.json
├── mcp.json
└── skills/
    └── literature-analysis/
        └── SKILL.md
```

Plugin 可以把：

```text
Skill instructions
+
MCP capabilities
```

一起安装和启用。

current loader 还会：

- 校验 manifest/schema；
- 做 path containment；
- 对 package 内容做 fingerprint；
- 区分 installed 与 enabled。

> 💡 **安全思想**：用户授权的是某个被审查过的 capability package，不是“这个目录名以后无论被替换成什么都继续信任”。

---

## 8.5 渐进披露（Progressive Disclosure）

### 8.5.1 为什么需要渐进披露

如果 30 个 Skill 每个几千字全部进入 System Prompt：

```text
大量 Token
+ 无关指令干扰
+ Prompt Cache 失效概率上升
```

所以 current-source 默认先使用 Summary。

### 8.5.2 三层渐进披露设计

可以继续沿用原教程的三层理解，但 current 实现更具体：

**Level 1：Discovery Metadata**

`build_skills_summary()` 给出：

```text
name
description
safe display path
availability
```

**Level 2：Active / Explicit Skill Body**

用户可以显式：

```text
$literature-analysis
```

`SkillsLoader.build_explicit_skill_runtime_context()` 会把完整 Skill Body 作为本 Turn 的 RuntimeContextBlock 注入。

**Level 3：Skill References / Bundled Resources**

复杂 Skill 可以把详细材料放在 references/scripts/assets 中，SKILL.md 保持核心工作流简洁，并在需要时让 Agent 读取对应文件。

### 8.5.3 always: true 的特殊处理

`get_always_skills()` 会在满足 requirements 时返回 always Skill。

适合：

- 每轮都必须遵守的极少量工作协议；
- 极短、稳定的核心约束。

不适合：

- 长文档；
- 偶尔使用的工具教程；
- 大量领域知识。

### 8.5.4 显式 Skill 调用

current-source 支持 `$skill-name`。

例如：

```text
Use $literature-analysis to compare these three papers.
```

相比让模型自己猜 Skill，这种方式：

- 可控；
- 方便测试；
- 适合做 A/B Eval。

## 8.6 内置技能列表

Built-in Skills 会随 current-source 演进，不建议背一个固定“完整列表”。

2026-09-24 源码中可见的代表包括：

| Skill | 用途 |
|---|---|
| `cron` | 定时提醒/任务 |
| `github` | 使用 `gh` CLI |
| `memory` | 搜索 history log |
| `image-generation` | 图像生成工作流 |
| `skill-creator` | 创建/维护 Agent Skills |
| `summarize` | URL/文件/视频摘要 |
| `clawhub` | 搜索/安装公共 Skill |
| `my` | Runtime 自检/自省 |

真正运行时请用：

```text
/skill
```

或 `SkillsLoader.list_skills()` 查看当前安装版本。

---

## 8.7 内置工具完整列表

### 8.7.1 工具总览

current Tool 同样是 discovery-driven，不要把教程中的表当永久闭集。

主要类别：

```text
Filesystem
Shell
Search / Web
MCP
Cron / Automations
Subagent
Long-running Task / Goal
Image Generation
Notebook / Patch
Runtime Self-inspection
Message / Delivery
```

### 8.7.2 文件操作工具

重点不是名字，而是理解安全边界：

- effective Project Workspace；
- `tools.restrictToWorkspace`；
- file state tracking；
- read/write/edit/patch/search 各自 contract。

### 8.7.3 Shell 执行工具

Shell Tool 受：

- enable/disable；
- Working Directory；
- Restrict-to-Workspace guard；
- dangerous pattern checks；
- optional OS sandbox；
- allowed env keys；

共同治理。

### 8.7.4 Web 工具

Web Search / Fetch 还受：

- provider config；
- URL policy；
- SSRF guard；
- private address whitelist；

约束。

### 8.7.5 通信工具

普通最终回复通过 TurnDelivery/Channel；Message Tool 用于需要显式发送某些消息或媒体的场景。

### 8.7.6 调度工具

current `cron` Tool 支持 reminder/task/one-time 等模式，底层是 workspace-scoped `CronService`。

Heartbeat 是 Gateway 管理的 protected system cron job，不是普通用户 Cron 的别名。

### 8.7.7 并发工具

Subagent Tool 通过 `SubagentManager` 创建 background/inline execution；current 默认最大并发 Subagent 数为 4，可配置。

---

## 8.8 ToolRegistry 统一注册与执行机制

### 8.8.1 ToolRegistry 架构

```text
Tool Sources
├── Built-in ToolLoader
├── Plugin Entry Points
└── MCPProvider
        ↓
   ToolRegistry
        ↓
get_definitions()
        ↓
AgentRunner / Provider
        ↓
Tool Call
        ↓
execute(name, args)
```

### 8.8.2 注册流程

AgentLoop 的默认 Tool 通过：

```text
ToolContext
→ ToolLoader.load()
→ ToolRegistry.register()
```

MCP Tool 则由 application-owned `MCPProvider` 连接后动态注册到同一个 Registry。

### 8.8.3 执行流程

AgentRunner 不需要知道能力来自哪一层：

```text
tool_call.name
→ ToolRegistry lookup
→ validation / execution
→ result governance
→ Tool Result Message
→ Provider next iteration
```

### 8.8.4 工具定义的 JSON Schema 格式

模型看到的是稳定的 Tool Contract：

```json
{
  "name": "search_papers",
  "description": "Search the indexed paper corpus.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "top_k": {"type": "integer"}
    },
    "required": ["query"]
  }
}
```

Tool Schema 是 model-facing API，改字段名/描述也可能改变模型 Tool Selection。

---

## 8.9 MCP 工具集成

### 8.9.1 MCPProvider

current-source 的连接 owner 是 `MCPProvider`，不是旧教程中 AgentLoop 内部固定的 MCP wrapper list。

```text
Config / Agent Plugin
→ MCPProvider.connect()
→ discover tools/resources/prompts
→ enabledTools filter
→ wrappers
→ shared ToolRegistry
```

### 8.9.2 转换过程

MCP Tool 的 JSON Schema 会经过 adapter 变成 Nanobot Tool contract，最终对 AgentRunner 与 Native Tool 保持统一。

### 8.9.3 MCP 工具的命名规范

Server capability 会映射为避免冲突的 wrapped name。实际名字应以连接日志和 ToolRegistry 为准，不要依赖旧教程中固定拼接规则。

### 8.9.4 配置 MCP Server

current `~/.nanobot/config.json`：

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

WebUI 也可以在 Apps 页面添加 MCP。

### 8.9.5 Agent Plugin：Skill + MCP 打包

对 ResearchPilot，推荐最终结构：

```text
research-plugin/
├── plugin.json
├── mcp.json
└── skills/
    └── literature-analysis/
        └── SKILL.md
```

Skill 进入 Context，MCP Tool 进入 ToolRegistry；Plugin 只是二者的安装/授权边界。

## 8.10 自定义 Skill 编写实战

### 8.10.1 实战：创建一个"代码分析"技能

**Step 1：创建技能目录**

```bash
mkdir -p skills/code-analyzer
```

**Step 2：编写 SKILL.md**

```markdown
---
name: code-analyzer
description: "Python 代码质量分析与优化建议"
always: false
metadata: '{"nanobot.requires.bins": ["python3"]}'
---

# 代码分析师技能

你是一名资深的 Python 代码分析师。当用户请求代码分析时，按以下流程操作。

## 分析维度

1. **代码规范**：PEP 8 合规性、命名规范
2. **安全性**：SQL 注入、路径遍历、硬编码密钥
3. **性能**：算法复杂度、不必要的计算、N+1 查询
4. **可维护性**：函数长度、圈复杂度、耦合度
5. **测试覆盖**：关键路径是否有测试

## 分析流程

### Step 1: 收集代码

```
使用 list_dir 查看项目结构
使用 read_file 读取关键文件
```

### Step 2: 运行静态分析

```
使用 exec 运行以下命令（如果工具可用）：
- python3 -m py_compile <file>  # 语法检查
- python3 -m pylint <file>      # 代码质量
- python3 -m bandit <file>      # 安全扫描
```

### Step 3: 生成报告

按以下格式生成分析报告：

## 报告模板

### 📊 总体评分: X/10

### 🔴 严重问题
(列出所有严重问题)

### 🟡 改进建议
(列出所有改进建议)

### 🟢 优秀实践
(列出代码中做得好的地方)

### 📝 重构建议
(给出具体的重构方案)
```

**Step 3：添加参考资料（可选）**

```bash
mkdir -p skills/code-analyzer/references
```

```markdown
<!-- skills/code-analyzer/references/security-checklist.md -->
# Python 安全检查清单

## 常见安全漏洞

1. SQL 注入：使用参数化查询而非字符串拼接
2. 路径遍历：验证用户输入的文件路径
3. 命令注入：避免 os.system()，使用 subprocess
4. 硬编码密钥：使用环境变量或密钥管理服务
5. 不安全的反序列化：避免 pickle.loads() 处理不信任数据
```

**Step 4：添加辅助脚本（可选）**

```bash
mkdir -p skills/code-analyzer/scripts
```

```python
#!/usr/bin/env python3
# skills/code-analyzer/scripts/complexity.py
"""计算 Python 文件的圈复杂度"""
import ast
import sys

def calculate_complexity(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For,
                                     ast.ExceptHandler, ast.With,
                                     ast.BoolOp)):
                    complexity += 1
            print(f"{node.name}: complexity = {complexity}")

if __name__ == "__main__":
    calculate_complexity(sys.argv[1])
```

**Step 5：测试技能**

```bash
# 启动 Agent
nanobot

# 测试对话：
# You: 请分析一下 src/main.py 的代码质量
# Agent 应该会读取 SKILL.md，然后按照分析流程执行
```

### 8.10.2 实战：创建一个"面试教练"技能

```markdown
---
name: interview-coach
description: "AI Agent 方向的面试训练和评估"
always: false
---

# 面试教练技能

## 模式

### 模式 1: 知识测验
随机从知识库中抽取问题，评估用户的回答。

### 模式 2: 模拟面试
模拟真实面试场景，包括追问和压力测试。

### 模式 3: 答案优化
帮助用户优化已有的面试回答。

## 评分标准

- 技术准确性 (40%)
- 表达清晰度 (20%)
- 深度和广度 (20%)
- 实际经验体现 (20%)

## 知识库主题

1. AI Agent 基础概念
2. 框架架构设计
3. 记忆系统
4. 工具与技能系统
5. 多平台部署
6. 安全与生产环境

## 反馈格式

### 评分: X/10

**优点**：
- ...

**不足**：
- ...

**改进建议**：
- ...

**参考答案**：
(给出一个更完善的回答示例)
```

---

## 8.11 工具安全机制

### 8.11.1 restrictToWorkspace

current config：

```text
tools.restrictToWorkspace
```

这是 **application-level workspace guard**，限制文件 Tool 与 Shell Working Directory 等访问边界。

它不是 OS sandbox。

### 8.11.2 exec 工具的安全层

current 推荐生产环境叠加：

```text
tools.restrictToWorkspace = true
+
tools.exec.sandbox = "bwrap"     # Linux
或 "seatbelt"                    # macOS
```

Windows 没有 bwrap；应保持 Workspace Restriction，并谨慎决定是否开放 Shell。

### 8.11.3 web_fetch / HTTP MCP 的 SSRF 防护

HTTP Web Fetch 与 HTTP/SSE MCP 都使用 SSRF 防护。

私有地址如果确实需要访问，只加入窄范围：

```text
tools.ssrfWhitelist
```

不要为了调通直接放开整个私网段。

### 8.11.4 最小工具权限

MCP Server 使用 `enabledTools`；Session 也可以有 disabled tools policy。

原则：

> Server/Runtime “能提供”什么，不等于某个 Agent/Session “应该拥有”什么。

## 8.12 面试高频题

### 题目 1：Nanobot 的工具系统是如何设计的？

> **参考回答**：
>
> "Nanobot 的工具系统基于 **ToolRegistry 统一注册机制**。所有工具——无论是内置工具（read_file、exec 等）还是 MCP 外部工具——都通过 ToolRegistry 统一注册和执行。
>
> 每个工具包含三部分：**工具定义**（JSON Schema 格式，描述参数）、**执行函数**（实际的业务逻辑）、**安全约束**（权限检查、路径限制等）。
>
> 工具定义会作为 Tool Definition 发送给 LLM，LLM 决定何时调用什么工具。调用请求返回后，ToolRegistry 根据工具名找到对应的 handler 执行，并将结果以 tool message 返回给 LLM。
>
> 对于 MCP 外部工具，通过 MCPToolWrapper 将 MCP 协议的工具格式转换为内置格式，然后统一注册到 ToolRegistry。这样 Agent 无需区分工具来源，使用方式完全一致。"

### 题目 2：Skill 和 Tool 的区别是什么？

> **参考回答**：
>
> "Skill 和 Tool 在 Nanobot 中是两个不同层次的概念。
>
> **Tool 是细粒度的原子操作**，比如 read_file 读文件、exec 执行命令、web_search 搜索网页。每个 Tool 有明确的参数定义和执行逻辑，通过 ToolRegistry 注册，以 JSON Schema 格式暴露给 LLM。
>
> **Skill 是粗粒度的能力模块**，本质上是一个 Markdown 文件（SKILL.md），告诉 Agent'你能做什么、怎么做'。一个 Skill 通常会教 Agent 如何组合使用多个 Tool 来完成复杂任务。比如 GitHub Skill 教 Agent 如何组合使用 exec（运行 git 命令）和 read_file（读取代码）来完成代码审查。
>
> 简单类比：Tool 是锤子、螺丝刀这些工具，Skill 是'如何组装家具'的说明书。"

### 题目 3：什么是渐进披露？在 Nanobot 中如何应用？

> **参考回答**：
>
> "渐进披露（Progressive Disclosure）是 UI/UX 设计中的经典原则——先展示概要，让用户按需深入细节。Nanobot 将这个原则创造性地应用到了 Agent 的 Prompt 管理中。
>
> 具体实现是三层结构：
>
> **Tier 1**：所有技能的 name 和 description 组成一个摘要列表，始终注入 System Prompt，大约消耗 100-500 tokens。Agent 通过摘要知道自己有哪些能力。
>
> **Tier 2**：当 Agent 判断某个技能与当前任务相关时，主动调用 read_file 读取完整的 SKILL.md，获取详细的使用说明。
>
> **Tier 3**：如果需要更深入的信息（参考文档、辅助脚本），Agent 继续访问 references/ 和 scripts/ 目录。
>
> 唯一的例外是标记了 `always: true` 的技能，它们跳过渐进披露，全文注入 System Prompt。
>
> 这种设计的价值在于 token 管理——如果有 20 个技能全部注入，可能消耗 1 万 token；使用渐进披露后，常态只消耗 300 token，按需加载时才产生额外消耗。"

### 题目 4：如何为 Nanobot 添加一个新的工具？

> **参考回答**：
>
> "有三种方式：
>
> 第一种是**写 Skill**——不需要写代码，只需创建一个 SKILL.md 文件，用 Markdown 描述这个能力的使用方式。Agent 会基于已有的 Tool（exec、web_fetch 等）来执行。这适合流程性、指导性的扩展。
>
> 第二种是**接入 MCP Server**——如果需要专用的 API 调用或复杂逻辑，可以开发一个 MCP Server，Nanobot 通过 MCPToolWrapper 自动将其工具转换为内置格式注册到 ToolRegistry。
>
> 第三种是**修改源码**——在 ToolRegistry 中直接注册新的工具函数。这种方式最灵活但需要修改框架代码，不太适合分发。
>
> 推荐优先级：Skill > MCP Server > 源码修改。Skill 是最轻量的方式，MCP Server 提供了标准化的扩展接口。"

---

## 8.13 本章小结

### 核心架构图

```
┌────────────────────────────────────────────────────────────┐
│                    Nanobot 工具与技能体系                    │
│                                                            │
│  ┌─── Skills 层 ───────────────────────────────────────┐   │
│  │  SKILL.md × N                                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │   │
│  │  │ github   │ │ weather  │ │ 自定义    │ ...        │   │
│  │  └──────────┘ └──────────┘ └──────────┘            │   │
│  │  渐进披露：Tier1(摘要) → Tier2(全文) → Tier3(脚本)  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌─── ToolRegistry ───────────────────────────────────┐   │
│  │                                                     │   │
│  │  内置工具              MCP 工具                     │   │
│  │  ┌─────────┐          ┌──────────────┐             │   │
│  │  │read_file│          │MCPToolWrapper│             │   │
│  │  │exec     │          │  mcp_xxx     │             │   │
│  │  │web_*    │          │  mcp_yyy     │             │   │
│  │  │message  │          └──────────────┘             │   │
│  │  │cron     │                                       │   │
│  │  │spawn    │                                       │   │
│  │  └─────────┘                                       │   │
│  │                                                     │   │
│  │  统一接口: register() / get_definitions() / execute()│  │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### 面试记忆清单

| 考点 | 一句话回答 |
|------|-----------|
| Skill vs Tool | Skill 是能力说明书（Markdown），Tool 是具体操作（代码） |
| SKILL.md 格式 | YAML Frontmatter + Markdown 正文 |
| 渐进披露 | 三层：摘要目录 → 全文读取 → 脚本/参考 |
| 技能发现 | workspace/skills/ 优先，同名覆盖内置 |
| ToolRegistry | 统一注册与执行所有工具（内置 + MCP） |
| MCPToolWrapper | 将 MCP 工具转换为内置格式 |
| 安全机制 | restrict_to_workspace + 危险命令拒绝 + SSRF 防护 |
| always 字段 | true=全文注入，false=仅摘要（默认） |

---

> **下一章**：[09 - 多平台接入](../09-mcp-integration/README.md) —— 了解 Nanobot 如何同时接入 Telegram、Discord、飞书、钉钉等 8+ 平台