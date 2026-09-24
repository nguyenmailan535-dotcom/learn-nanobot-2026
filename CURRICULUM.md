# Personalized Curriculum

## 目标

目标岗位优先级：

```text
Agent 开发实习
AI 应用 / AI 平台研发实习
大模型应用后端
允许 Java 背景的 AI 后端 / 平台岗位
```

这份课程不以“学完 Nanobot”为终点，而以“能在面试里证明你理解 Agent runtime，并有一套真实可测的 Agent 项目”为终点。

## 已有能力如何复用

已有 Java 后端经验可以映射到：

| Java / Backend 心智模型 | Nanobot 对应 |
|---|---|
| Controller / transport | Channel |
| DTO / event | InboundMessage / OutboundMessage |
| Service orchestration | AgentLoop |
| while-loop + strategy | AgentRunner + Provider |
| Bean registry | ToolRegistry / Provider registry |
| Filter / Interceptor | hooks / runtime context / security boundaries |
| Session | Session JSONL |
| Cache/compaction | AutoCompact，但目的不是传统缓存 |
| Scheduled task | cron / heartbeat |
| plugin SPI | Agent Plugin / tool entry point |

RAG 已有经验映射到 Capstone：

```text
PDF parsing
→ sentence-aware chunking
→ BGE embedding
→ document-aware retrieval
→ grounded generation
→ citation
→ evaluation
```

不要重新做一套“教程 RAG”，直接把已经验证过的 pipeline 做成 Nanobot 的真实 capability。

## 每章完成标准

每一章必须至少留下一个可展示产物：

- source trace 笔记；
- 最小 runnable experiment；
- 测试输出；
- architecture diagram；
- bad case；
- README；
- 可复现命令。

如果一章只是“看完了”，默认没有完成。
