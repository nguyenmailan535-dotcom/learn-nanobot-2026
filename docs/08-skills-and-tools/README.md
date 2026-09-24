# 08 - 技能与工具

> **阅读时间**：约 2 小时  
> **2026 current-source 说明**：本章直接沿用原版 learn-nanobot 的章节结构与主体内容；凡涉及 Nanobot 具体源码、配置、路径、记忆、并发、MCP 生命周期等实现细节，均按 HKUDS/nanobot main @ 2026-09-24 (source trace snapshot around 62aa6ba6a33790a656b952ef150517bd70d6eb30) 修订。

> **前置知识**：[07 - 记忆系统实战](../07-memory-system/README.md)  
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

current SkillsLoader 会发现：
- `<workspace>/skills/<name>/SKILL.md`；
- enabled Agent Plugin 中的 `skills/<name>/SKILL.md`；
- built-in skills。

典型：

~~~text
skills/
└── github-manager/
    ├── SKILL.md
    └── scripts/
~~~

### 8.2.2 SKILL.md 文件格式

~~~markdown
---
name: github-manager
description: Manage GitHub repositories, issues, and pull requests safely.
---

# GitHub 管理技能

## 能力
- 阅读仓库
- 分析 Issue / PR

## 使用步骤
1. 先确认目标仓库
2. 读取相关上下文
3. 执行动作前检查权限

## 注意事项
- 不在日志输出 token
- 写操作前确认作用范围
~~~

current source 会验证：
- YAML frontmatter 可解析；
- `name` 与目录 identity 合法；
- description 非空且长度合法。


## 8.3 YAML Frontmatter 字段详解

### 8.3.1 必填字段

current Agent Skills identity contract 至少要求：
- `name`；
- `description`。

`name` 要满足 current 命名正则、长度限制，并与 Skill identity 一致。

### 8.3.2 可选字段

Nanobot-specific metadata 可以表达：
- always；
- requirements；
- 其他 current runtime hint。

具体字段以 current SkillsLoader 和 built-in Skill 示例为准，不要依赖旧教程中未被源码验证的字段。

### 8.3.3 always 字段详解

current `get_always_skills()` 仍会识别 always skill，并由 ContextBuilder 作为 active instruction 注入。

但不建议大量使用：

~~~text
always Skill 太多
→ System Context 变长
→ Instruction Collision 增加
~~~

### 8.3.4 requirements / metadata

current source 会检查 requirement：
- `bins`：本机是否存在所需可执行文件；
- `env`：所需环境变量是否存在。

未满足 requirement 的 Skill 可以出现在 summary 中，但标记 unavailable，并不会当成可正常使用的 Skill。


## 8.4 技能发现机制

### 8.4.1 搜索路径

current 顺序可以理解为：

~~~text
Workspace Skills
   ↓
Enabled Agent Plugin Skills
   ↓
Built-in Skills
~~~

### 8.4.2 发现流程

~~~text
list_skills()
→ scan workspace
→ discover enabled plugin skills
→ append built-in skills not shadowed
→ apply disabledSkills / aliases
→ validate requirements
~~~

### 8.4.3 覆盖机制

current 使用 `seen_names`，因此优先级：

~~~text
workspace > plugin > built-in
~~~

这使本地定制可以覆盖系统默认 Skill，而不需要 fork Nanobot。


## 8.5 渐进披露（Progressive Disclosure）

### 8.5.1 为什么需要渐进披露

假设 50 个 Skill，每个 1000 字，全部注入会制造巨大的 prompt。

### 8.5.2 current 三层思路

~~~text
1. Skill Discovery Summary
   name + description + path + availability

2. Explicit / Always Activation
   $skill-name 或 always skill

3. Full Body
   真正需要时 read/load SKILL.md
~~~

`build_skills_summary()` 会构造 summary，`build_explicit_skill_runtime_context()` 会把显式 Skill 包装成当前 Turn 的 RuntimeContextBlock。

### 8.5.3 always: true 的特殊处理

Always Skill 不需要用户显式 `$name` 就进入 active instructions；因此应该谨慎使用，避免长期 Context Pollution。


## 8.6 内置技能列表

内置 Skill 列表属于快速变化的 current-source 内容，本仓库不再硬编码一个可能过期的完整表。

直接查看：

~~~text
nanobot/skills/
~~~

或在运行时用 SkillsLoader/WebUI 获取：
- name；
- description；
- availability；
- source。

学习时更重要的是掌握 **Skill discovery contract**，而不是背当前恰好有几个内置 Skill。


## 8.7 内置工具完整列表

### 8.7.1 工具总览

current Tool 采用 discovery/loader 机制，完整列表会随配置、Platform、Plugin 和 build 变化。重点类别：

| 类别 | 典型能力 |
|---|---|
| Filesystem | read/write/edit/search |
| Shell | exec / long-running session |
| Web | search / fetch |
| Messaging | 向 Channel 发送消息 |
| Automation | cron / trigger-related capability |
| Subagent | spawn / long task |
| Runtime | goal/runtime control、自省 |
| MCP | dynamic external tools |
| Media | image generation 等可选能力 |

### 8.7.2 文件操作工具

受 effective Project Workspace、`restrictToWorkspace` 和 workspace policy 约束；某些 agent-owned skill/history path 只有 capability-specific read access。

### 8.7.3 Shell 执行工具

current security 不只是字符串黑名单；生产部署应结合：
- `tools.restrictToWorkspace`；
- `tools.exec.sandbox`（Linux bwrap / macOS seatbelt）；
- 最小权限运行用户。

### 8.7.4 Web 工具

HTTP fetch/search 走 current network/SSRF protection；私网访问需要谨慎的 `ssrfWhitelist`。

### 8.7.5 通信工具

MessageTool 不直接依赖具体平台 SDK，而通过当前 request/delivery context 路由。

### 8.7.6 调度工具

CronTool 支持 one-time / interval / cron expression。用户创建 Job 与 system-managed Heartbeat/Dream 要区分。

### 8.7.7 并发工具

Subagent tool 由 SubagentManager 管理，具有独立 maxConcurrentSubagents 和 scoped Tool Set。


## 8.8 ToolRegistry 统一注册与执行机制

### 8.8.1 ToolRegistry 架构

~~~text
Tool Sources
├── built-in ToolLoader
├── Plugin entry points
└── MCPProvider
        ↓
   ToolRegistry
        ↓
AgentRunner
~~~

### 8.8.2 注册流程

AgentLoop 构造 `ToolContext` 后：

~~~text
ToolLoader().load(ctx, registry)
~~~

MCPProvider 连接后也把 dynamic tools 注册进**同一个 registry**。

### 8.8.3 执行流程

~~~text
Model Tool Call
→ AgentRunner
→ ToolRegistry lookup/execute
→ Tool Result
→ Runner governance
→ Provider next iteration
~~~

### 8.8.4 JSON Schema

Tool definition 是 model-facing contract。Schema 应：
- 参数类型明确；
- required 合理；
- description 说明何时使用，而不是堆一大篇教程；
- error/result contract 稳定。


## 8.9 MCP 工具集成

### 8.9.1 MCPProvider / Tool Adapter

current MCP 由 `MCPProvider` 拥有连接和 dynamic registration，而不是旧教程中由 AgentLoop 自己管理某个 MCP wrapper 列表。

### 8.9.2 转换过程

~~~text
MCP Server list_tools()
→ read input schema
→ apply enabledTools
→ wrap capability
→ ToolRegistry.register
→ AgentRunner sees normal Tool
~~~

### 8.9.3 MCP 工具命名

wrapped name 必须在 Host 内唯一。current `enabledTools` 可以匹配 raw 或 wrapped name。不要在业务代码里依赖旧版固定前缀。

### 8.9.4 配置 MCP Server

current 配置位于：

~~~text
~/.nanobot/config.json
→ tools.mcpServers
~~~

也可由 enabled Agent Plugin 提供 MCP server。连接 lifecycle：

~~~text
composition root
→ MCPProvider.connect()
→ Agent runtime
→ MCPProvider.aclose()
~~~

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

### 8.11.1 restrict_to_workspace

所有文件操作工具（read_file, write_file, edit_file, list_dir）都受 workspace 限制：

```python
def validate_path(path: str, workspace: str) -> str:
    """确保路径在 workspace 范围内"""
    abs_path = os.path.abspath(os.path.join(workspace, path))
    abs_workspace = os.path.abspath(workspace)
    
    if not abs_path.startswith(abs_workspace):
        raise PermissionError(
            f"Access denied: {path} is outside workspace"
        )
    
    return abs_path
```

### 8.11.2 exec 工具的安全层

```
用户命令 → 危险模式检测 → SSRF 检测 → 路径限制 → 执行
    │            │              │            │         │
    │         拒绝危险命令    拒绝内网访问   限制cwd   异步执行
    │         (rm -rf /)      (127.0.0.1)  (workspace)
    │
    └── 如果 exec.allowed = false，直接拒绝所有命令
```

### 8.11.3 web_fetch 的 SSRF 防护

```python
def is_ssrf_target(url: str) -> bool:
    """检查 URL 是否指向内网地址"""
    from urllib.parse import urlparse
    import ipaddress
    
    parsed = urlparse(url)
    hostname = parsed.hostname
    
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_reserved
    except ValueError:
        return hostname in ("localhost", "metadata.google.internal")
```

---

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
> 对于 MCP 外部工具，通过 MCP tool adapter 将 MCP 协议的工具格式转换为内置格式，然后统一注册到 ToolRegistry。这样 Agent 无需区分工具来源，使用方式完全一致。"

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
> 第二种是**接入 MCP Server**——如果需要专用的 API 调用或复杂逻辑，可以开发一个 MCP Server，Nanobot 通过 MCP tool adapter 自动将其工具转换为内置格式注册到 ToolRegistry。
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
│  │  │read_file│          │MCP tool adapter│             │   │
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
| MCP tool adapter | 将 MCP 工具转换为内置格式 |
| 安全机制 | restrict_to_workspace + 危险命令拒绝 + SSRF 防护 |
| always 字段 | true=全文注入，false=仅摘要（默认） |

---

> **下一章**：[09 - 多平台接入](../09-multi-platform/README.md) —— 了解 Nanobot 如何同时接入 Telegram、Discord、飞书、钉钉等 8+ 平台