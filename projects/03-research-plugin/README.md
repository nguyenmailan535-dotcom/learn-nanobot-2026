# Project 03 — Research Agent Plugin

目标：把已有 Multi-paper Retrieval 变成 Nanobot 的可安装能力。

## 目录

```text
research-agent/
├── plugin.json
├── mcp.json
└── skills/
    └── literature-analysis/
        └── SKILL.md
```

本目录给出一个**骨架**。实际 `mcp.json` 的 command/path 要按你的本地环境改。

## Tool contract 建议

### `search_papers`

输入：

```json
{"query":"...","top_k":5}
```

输出保留：

```text
doc_id
filename
page
chunk_id
score
text
```

不要在 MCP 层把来源 metadata 丢掉。

## 下一步

把 `E:\ResearchPilot` 中已经跑通的 retrieval 代码抽成一个独立 service，再接 MCP；不要复制 07A/07C 的所有实验脚本到 server。
