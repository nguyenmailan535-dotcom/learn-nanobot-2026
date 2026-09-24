# 08 — Tools / Skills / Agent Plugins

## 三个概念先分开

### Tool

模型能够实际执行的 capability，有参数 schema 和返回值。

### Skill

给 Agent 的工作方法/领域指导，本质是 context/instruction capability；current source 支持 progressive loading 和 `$skill-name` 显式调用。

### Agent Plugin

安装/激活边界，可以把 Skill 与 MCP server 打包在一起。

## Skill progressive loading

合理的 Skill 不应该把几千行说明永久塞 system prompt。

current 思路：

```text
metadata summary     常驻/可发现
SKILL.md body        触发或显式调用后加载
bundled resources    真需要时再读/执行
```

## Precedence

学习时记住：workspace 定义可以覆盖低层来源；Plugin 和 built-in 也参与发现。遇到冲突时必须查 current loader，而不是靠旧笔记。

## Agent Plugins v1

典型结构：

```text
<workspace>/plugins/research-agent/
├── plugin.json
├── mcp.json
└── skills/
    └── literature-analysis/
        └── SKILL.md
```

启用与管理优先通过 Apps。

## 必做实验 1：Skill

写一个 `literature-analysis` Skill，只教 Agent：

1. 先明确 research question；
2. 再调用检索工具；
3. answer 必须带 evidence；
4. evidence 不足就说不足。

不要在 Skill 里实现 retrieval。

## 必做实验 2：Plugin

把上面的 Skill 与后续 Chapter 09 的 Research MCP 打成一个 Plugin。

## 面试自测

- Skill 和 Tool 为什么不能互相替代？
- 为什么 Plugin 只是 activation/package boundary，不应该被描述为“新的一类 Agent”？
- progressive disclosure 解决的主要是 context cost 还是 execution isolation？
- untrusted Skill 为什么也有供应链风险？
