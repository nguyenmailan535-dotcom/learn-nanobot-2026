# Project 01 — Runtime Trace Lab

目标：把一次包含 tool call 的 turn 追到底。

## Deliverables

- `trace.md`：源码调用链；
- `breakpoints.md`：建议断点/日志点；
- `diagram.md`：一张 Mermaid；
- `notes.md`：3 个 current-source vs old tutorial 差异。

## 必追字段

```text
InboundMessage
session_key
workspace_scope
initial_messages
AgentRunSpec
ToolRegistry
AgentRunResult
OutboundMessage
```

项目完成后不要写“阅读源码”，而写“追踪了什么链路”。
