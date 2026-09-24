# 08 - Tools、Skills 与 Agent Plugins：能力、方法和安装边界

> 🎯 **本章目标**：从 current-source 理解 Tool、Skill、Agent Plugin 三种不同抽象；读懂 SkillsLoader 的 discovery、precedence、progressive loading；理解 Plugin 为什么同时解决 capability packaging 和 activation boundary。

---

## 目录

- [8.1 为什么 Tool 不应该解决所有问题](#81-为什么-tool-不应该解决所有问题)
- [8.2 Tool：可执行能力](#82-tool可执行能力)
- [8.3 Skill：给 Agent 的工作方法](#83-skill给-agent-的工作方法)
- [8.4 SKILL.md 格式](#84-skillmd-格式)
- [8.5 SkillsLoader 源码](#85-skillsloader-源码)
- [8.6 Skill Discovery 与优先级](#86-skill-discovery-与优先级)
- [8.7 Progressive Loading](#87-progressive-loading)
- [8.8 Explicit Skill Invocation](#88-explicit-skill-invocation)
- [8.9 always Skill](#89-always-skill)
- [8.10 Agent Plugins v1](#810-agent-plugins-v1)
- [8.11 Plugin 源码中的安全设计](#811-plugin-源码中的安全设计)
- [8.12 ToolLoader / ToolRegistry 再看一遍](#812-toolloader--toolregistry-再看一遍)
- [8.13 Research Agent Skill 实战](#813-research-agent-skill-实战)
- [8.14 常见设计错误](#814-常见设计错误)
- [8.15 面试高频题](#815-面试高频题)
- [8.16 本章总结](#816-本章总结)

---

## 8.1 为什么 Tool 不应该解决所有问题

假设希望 Research Agent 遵守：

~~~text
1. 先检索证据；
2. 不够就说证据不足；
3. 跨论文问题看多个文档；
4. 回答保留 Citation。
~~~

这是一种工作方法。

如果做成：

~~~text
follow_research_rules()
~~~

模型调用一次并不能保证后续一直遵守。

因此：

~~~text
Tool = 做事情的能力
Skill = 做事情的方法
~~~

---

## 8.2 Tool：可执行能力

Tool 通常有：

~~~text
name
description
parameters
execute
result
~~~

例如：

~~~text
search_papers
read_file
web_fetch
spawn
cron
~~~

Tool 会对环境产生读取、写入或执行行为，并返回 Observation。

---

## 8.3 Skill：给 Agent 的工作方法

current：

~~~text
nanobot/agent/skills.py
~~~

SkillsLoader 注释：

> Skills are markdown files that teach the agent how to use specific tools or perform certain tasks.

Skill 可以告诉 Agent：

- 什么场景用某 Tool；
- 按什么步骤做任务；
- 哪些约束必须遵守；
- 什么结果算完成。

它不一定包含代码。

---

## 8.4 SKILL.md 格式

current source 会解析 YAML frontmatter。

最小例子：

~~~markdown
---
name: literature-analysis
description: Analyze research papers using evidence-first retrieval.
---

# Literature Analysis

1. Retrieve evidence first.
2. Preserve doc/page/chunk provenance.
3. If evidence is insufficient, say so.
~~~

current validation 会检查：

- metadata 是否可解析；
- name 是否与目录匹配；
- name 格式；
- description 是否存在且长度合法。

所以 Skill 不是随便丢一个 Markdown 文件。

---

## 8.5 SkillsLoader 源码

主要方法：

~~~text
list_skills
load_skill
load_skills_for_context
get_explicitly_invoked_skills
build_explicit_skill_runtime_context
build_skills_summary
get_always_skills
~~~

### list_skills

收集：

~~~text
workspace skills
enabled Agent Plugin skills
built-in skills
~~~

然后：

- 去重；
- 应用 disabled_skills；
- 检查 requirements。

### requirements

Skill metadata 可以依赖：

~~~text
bins
env
~~~

要求未满足时可以标记 unavailable。

说明 Skill Discovery 不只是 os.listdir。

---

## 8.6 Skill Discovery 与优先级

current list_skills 顺序：

~~~text
1. Workspace Skills
2. Enabled Agent Plugin Skills
3. Built-in Skills
~~~

通过 seen_names 防止低优先级覆盖高优先级。

概念上：

~~~text
workspace > plugin > built-in
~~~

### 为什么 Workspace 优先

本地用户定制应当覆盖系统默认。

你可以用同名 Workspace Skill 覆盖 Built-in，而不用修改 package source。

---

## 8.7 Progressive Loading

假设 50 个 Skill，每个 1000 字。

全部塞 System Prompt 会产生巨量：

~~~text
50 × 1000 chars
~~~

current build_skills_summary 只提供：

~~~text
Skill Name
Description
Path
Availability
~~~

真正需要时再读取完整 SKILL.md。

~~~text
Discovery Metadata
      ↓
模型知道有哪些 Skill
      ↓
真正需要
      ↓
加载完整 Skill Body
~~~

好处：

- 减少 Token；
- 降低 Instruction Collision；
- 扩展 Skill 数量；
- 按需加载。

---

## 8.8 Explicit Skill Invocation

current source 支持：

~~~text
$skill-name
~~~

例如：

~~~text
Use $literature-analysis to compare these papers.
~~~

SkillsLoader 解析后构造 RuntimeContextBlock：

~~~text
[Active Skills — instructions for this user turn]
...
[/Active Skills]
~~~

这与“所有 Skill body 永远在 Prompt”完全不同。

---

## 8.9 always Skill

current source 仍有：

~~~text
get_always_skills
~~~

ContextBuilder 会把 always Skills 作为 active instructions。

### 为什么不要滥用

大量 always Skill 会重新引入：

~~~text
Context Bloat
Instruction Collision
~~~

“重要”不等于“应该永远加载”。

---

## 8.10 Agent Plugins v1

current：

~~~text
nanobot/agent/plugins.py
~~~

典型结构：

~~~text
workspace/plugins/research-agent/
├── plugin.json
├── mcp.json
└── skills/
    └── literature-analysis/
        └── SKILL.md
~~~

current loader 使用 Agent Plugins v1 schema：

~~~text
https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
https://agent-plugins.org/schemas/1.0.0/mcp.schema.json
~~~

所以不要自己发明旧 manifest 字段。

### Plugin 的真实意义

不是“另一种 Agent”。

而是：

> 把一组能够共同安装、验证、启用、禁用的 capability 打包。

---

## 8.11 Plugin 源码中的安全设计

### Manifest Validation

不合法 Manifest 不应被直接激活。

### Path Containment

Plugin 内容必须被限制在合法 package root。

### Fingerprint

current source 对 package path/link/file content 做 fingerprint。

意义：

~~~text
用户授权 package A
↓
package 内容被替换
↓
不能默认继续继承旧授权
~~~

### Explicit Enable

~~~text
Installed
≠
Enabled
~~~

“文件存在”不等于“Agent 应立即获得能力”。

---

## 8.12 ToolLoader / ToolRegistry 再看一遍

### ToolLoader

负责：

~~~text
discover
check enabled/config/scope
construct
register
~~~

### ToolRegistry

负责：

~~~text
tool names
definitions
lookup
execute
runtime context providers
~~~

### Plugin 的两条支线

~~~text
Agent Plugin
├── Skill
│    ↓
│  SkillsLoader
│    ↓
│  ContextBuilder
│
└── MCP Server
     ↓
   MCPProvider
     ↓
   ToolRegistry
     ↓
   AgentRunner
~~~

一个进入 Context，一个进入 Execution。

---

## 8.13 Research Agent Skill 实战

仓库已有：

~~~text
projects/03-research-plugin/
└── skills/literature-analysis/SKILL.md
~~~

目标规则：

~~~text
1. 问题依赖论文时先检索；
2. 保留 doc_id/page/chunk_id；
3. 跨论文问题收集多个文档 Evidence；
4. Reference 中出现的论文不等于 Corpus Paper；
5. Evidence 不足就明确说明；
6. Quotation 保持短。
~~~

### 实验

同一个 Query：

~~~text
Which papers in the current corpus discuss cardinality estimation?
~~~

比较：

~~~text
无 Skill
vs
显式 $literature-analysis
~~~

观察：

- Tool Usage；
- Source Selection；
- Citation；
- Answer Verbosity。

不要只看最终答案，要看 Trace。

---

## 8.14 常见设计错误

### 错误 1：Skill 里塞业务数据

Skill 应该是方法，不是 20 篇论文原文。

### 错误 2：Tool Description 写成一篇教程

Tool Schema 越长不一定越好。

### 错误 3：所有 Skill always

会造成 Context Pollution。

### 错误 4：Plugin 安装即完全信任

current source 特意区分 Install、Enable、Fingerprint。

### 错误 5：把 MCP Tool 与 Skill 当成一回事

一个是 Execution Capability，一个是 Instruction Capability。

---

## 8.15 面试高频题

### Q1：Skill 与 Tool 的区别？

> Tool 是 executable capability；Skill 是 instruction capability。Tool 进入 ToolRegistry，Skill 进入 Context。Plugin 可以组合二者，但不应该混淆。

### Q2：Progressive Loading 为什么重要？

> Skill 数量增长时，完整 body 全量进入 System Prompt 会造成 Token 和 Instruction Interference。current Nanobot 先暴露 metadata summary，需要时再加载 Skill。

### Q3：Workspace、Plugin、Built-in Skill 冲突怎么办？

current loader 的优先级可理解为：

~~~text
workspace > plugin > built-in
~~~

### Q4：为什么 Agent Plugin 要做 Fingerprint？

> Capability Package 是安全边界。用户授权的是被审查过的 package 内容，之后被替换不应该静默继承信任。

---

## 8.16 本章总结

记住：

~~~text
Tool
= 能做什么

Skill
= 应该怎么做

Agent Plugin
= 这些能力如何被打包、安装、启用

MCP
= 外部能力如何通过标准协议接入
~~~

下一章不再接第三方 Demo，而是把你已经做过的 ResearchPilot Retrieval 真正封装成 Nanobot 可调用的 Research MCP。
