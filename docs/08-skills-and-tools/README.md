# 08 - 技能与工具

> **阅读时间**：约 2 小时  
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

current `SkillsLoader` 会解析 SKILL.md 的 YAML Frontmatter，并至少校验：

- `name` 与 Skill 目录名一致
- name 符合格式与长度要求
- `description` 存在且长度合法

还可以通过 Nanobot metadata 表达：

- always
- requires.bins
- requires.env

> 原版教程中的字段概念可以继续使用，但应以 current `nanobot/agent/skills.py` 的 parser/validation 为准，不要把旧 schema 当成永久固定协议。

---

## 8.4 技能发现机制

### 8.4.1 current 搜索来源

```
1. Workspace Skills
2. Enabled Agent Plugin Skills
3. Built-in Skills
```

current loader 使用 seen_names 去重，因此概念优先级是：

```
workspace > plugin > built-in
```

### 8.4.2 Disabled Skills 与 Requirements

`disabled_skills` 会从可用集合移除 Skill；若 metadata 要求的 binary/env 不满足，Skill 可以显示为 unavailable。

### 8.4.3 Agent Plugin Skill

Plugin Skill 只有在 Plugin 被明确启用且 package 校验通过后才会进入 SkillsLoader。

---

## 8.5 渐进披露（Progressive Disclosure）

### 8.5.1 为什么需要

如果所有 SKILL.md 全文都进 System Prompt，会产生：

- Token 浪费
- Instruction Collision
- Prompt Cache 波动
- 无关能力干扰

### 8.5.2 current 实现

`build_skills_summary()` 默认只暴露：

```
name
description
path
availability
```

需要时再读取完整 SKILL.md。

### 8.5.3 Explicit Invocation

current 还支持用户文本中的：

```
$skill-name
```

`get_explicitly_invoked_skills()` 解析后，通过 RuntimeContextBlock 把完整 Skill Body 作为当前 Turn Active Skill 注入。

### 8.5.4 always Skill

`get_always_skills()` 仍会把 always Skill 直接作为 active instructions。不要滥用，否则又会造成 Context Bloat。

---

## 8.6 内置技能列表

内置 Skill 会随 current-source 变化，不应把某个固定列表背成永久事实。

源码入口：

```
nanobot/skills/
nanobot/agent/skills.py
```

面试更应该讲：

- Skill discovery
- progressive loading
- requirement checking
- workspace/plugin/builtin precedence

而不是背当前恰好有几个 Skill。

---

## 8.7 内置工具完整列表

Tool 也会随版本变化。current architecture 文档给出的主要 Tool Area 包括：

| Area | current-source |
|---|---|
| Filesystem | `agent/tools/filesystem.py` |
| Shell | `agent/tools/shell.py` |
| Web | `agent/tools/web.py` |
| MCP | `agent/tools/mcp.py` |
| Cron | `agent/tools/cron.py` |
| Image Generation | `agent/tools/image_generation.py` |
| Runtime Self-inspection | `agent/tools/self.py` |
| Spawn/Subagent | `agent/tools/spawn.py` |

实际可见 Tool 取决于：

- Config
- Plugin
- Session Policy
- Workspace Scope
- Runtime Capability

---

## 8.8 ToolRegistry 统一注册与执行机制

### 8.8.1 ToolRegistry

统一负责：

```
register
get
tool_names
get_definitions
execute
runtime context provider
```

### 8.8.2 ToolLoader

current default tools 通过：

```
ToolContext
→ ToolLoader
→ ToolRegistry
```

构造和注册。

### 8.8.3 Model-facing Contract

Tool Name、Description、JSON Schema、Error Message 都会影响模型决策，因此它们属于 model-facing API。

---

## 8.9 MCP 工具集成

current-source 不再只把 MCP 理解成一个静态 `MCPToolWrapper`。

### 8.9.1 MCPProvider

```
Application Composition Root
├── shared ToolRegistry
├── MCPProvider
└── AgentLoop
```

MCPProvider connect 后动态发现/注册 Tool，并在 shutdown 时 close connections。

### 8.9.2 enabledTools

MCPServerConfig 可以限制 Agent 实际可见 capability，实现最小权限。

### 8.9.3 Agent Plugin

Agent Plugin 可以同时打包：

```
Skill
+
MCP Server
```

Skill 进入 Context，MCP Tool 进入 ToolRegistry。两者是不同抽象。

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

current-source 的 Tool Security 不能只靠“Prompt 提醒模型不要乱做”。

### Workspace Boundary

```
tools.restrictToWorkspace
```

限制普通文件访问；effective Project Workspace 决定相对路径边界。

### Exec Sandbox

```
tools.exec.sandbox
```

current 支持 Linux `bwrap`、macOS `seatbelt` 等 OS 级隔离。Workspace Guard 是应用层边界，Sandbox 是进程级边界，两者可以叠加。

### SSRF

Web Fetch 与 HTTP/SSE MCP 使用网络安全检查；如确需访问私有目标，只应使用窄范围 `tools.ssrfWhitelist`。

### MCP 最小权限

通过 `enabledTools` 只暴露需要的 MCP Capability。

### Session Policy

某个 Session 还可以通过 disabled tools 得到受限 ToolRegistry。

## 8.12 面试高频题

### 题目 1：Skill 和 Tool 有什么区别？

> Tool 是可执行 Capability，进入 ToolRegistry；Skill 是行为/方法 Instruction，进入 Context。Agent Plugin 可以同时携带二者，但不应该混为一谈。

### 题目 2：Nanobot 如何做 Progressive Disclosure？

> 先通过 Skills Summary 暴露 name/description/path/availability，需要时再读取完整 SKILL.md；用户还可以用 `$skill-name` 显式激活当前 Turn。

### 题目 3：Skill 的优先级？

> current discovery 顺序可以理解为 Workspace > Enabled Plugin > Built-in，同名时更高优先级来源先占用。

### 题目 4：MCP Tool 如何进入 ToolRegistry？

> application-owned MCPProvider 使用 shared ToolRegistry，连接 Server 后动态注册；AgentRunner 只看统一 Tool Contract。

### 题目 5：为什么 Plugin 要显式 Enable 和 Fingerprint？

> Installed 不等于 Trusted。current Plugin Loader 会验证 Manifest、Containment 与 Package Fingerprint，避免 package 后续被替换却静默继承授权。

## 8.13 本章小结

| 考点 | current-source 要点 |
|---|---|
| Skill vs Tool | Skill 是 instruction capability；Tool 是 executable capability |
| SKILL.md | YAML Frontmatter + Markdown 正文 |
| Discovery | Workspace → Enabled Agent Plugin → Built-in |
| Progressive Loading | Summary 优先，按需加载全文；支持 `$skill-name` 显式激活 |
| ToolLoader | 发现/构造/注册 Tool |
| ToolRegistry | 统一 Definitions、Lookup、Execute |
| MCP | MCPProvider 动态注册到共享 ToolRegistry |
| Agent Plugin | 可打包 Skill + MCP，并要求显式 Enable / 校验 |
| 安全 | `tools.restrictToWorkspace`、exec sandbox、SSRF、MCP enabledTools |

---

> **下一章**：[09 - 多平台接入](../09-multi-platform/README.md)
