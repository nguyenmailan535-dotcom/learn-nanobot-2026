# 17 — Learning Resources

## 一级：Nanobot current source

- https://github.com/HKUDS/nanobot
- https://github.com/HKUDS/nanobot/blob/main/docs/concepts.md
- https://github.com/HKUDS/nanobot/blob/main/docs/architecture.md
- https://github.com/HKUDS/nanobot/blob/main/docs/configuration.md
- https://github.com/HKUDS/nanobot/blob/main/docs/quick-start.md
- https://github.com/HKUDS/nanobot/blob/main/docs/automations.md
- https://github.com/HKUDS/nanobot/blob/main/docs/deployment.md
- https://github.com/HKUDS/nanobot/blob/main/docs/python-sdk.md
- https://github.com/HKUDS/nanobot/blob/main/docs/openai-api.md

## 二级：关键源码

```text
nanobot/agent/loop.py
nanobot/agent/runner.py
nanobot/agent/context.py
nanobot/agent/memory.py
nanobot/agent/subagent.py
nanobot/agent/skills.py
nanobot/agent/tools/registry.py
nanobot/agent/tools/mcp.py
nanobot/session/manager.py
nanobot/security/
```

## MCP

优先读官方 Model Context Protocol specification，再结合 Nanobot adapter；不要只看二手文章。

## RAG / Eval

学习重点：

- embedding / dense retrieval；
- sparse retrieval / hybrid 的适用边界；
- reranking；
- retrieval evaluation；
- groundedness / citation support；
- unanswerable cases；
- bad case taxonomy。

## Source reading 工具

推荐组合：

```text
IDEA/PyCharm/VS Code
ripgrep (rg)
Git blame/log
Codex / ChatGPT
pytest
```

AI 的作用是“帮你定位和解释”，不是替你拥有理解。

## 旧 learn-nanobot 如何使用

保留价值：

- 课程组织；
- Agent/MCP 基础概念；
- 求职视角；
- STAR/简历写作思路。

必须重新核对：

- Nanobot source paths；
- Memory；
- concurrency；
- Channels；
- MCP integration；
- Subagent / Automation；
- install/config/deploy 命令；
- 所有“固定数字”。
