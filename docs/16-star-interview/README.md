# 16 — STAR 项目话术

## 3 分钟项目版本

### S — Situation

科研阅读场景里，单篇 PDF 问答很容易做成 Demo，但真实工作需要跨论文检索、可追溯引用、长期项目上下文和自动化任务；同时我希望真正理解 Agent runtime，而不是只调 LangChain API。

### T — Task

我的目标是：基于 Nanobot current-source 做一个 Research Agent，把已有 Multi-paper RAG 作为工具能力接入，并做到可以定位 retrieval / tool / generation / citation failure。

### A — Action

按真实完成情况讲：

1. source trace：`AgentLoop` / `AgentRunner` / `ToolRegistry`；
2. RAG：Parsing / Chunk / BGE / document-aware retrieval；
3. MCP/Plugin：把 retrieval service 暴露给 Agent；
4. Citation：保留 doc/page/chunk provenance；
5. Memory：Session/AutoCompact/Dream；
6. Eval：构造 multi-paper eval set 与 bad cases；
7. Security/Deploy：workspace、enabledTools、Gateway。

### R — Result

只说实测数据：

```text
[N] papers
[M] chunks
Document Recall@5 = ...
Evidence Recall@5 = ...
Citation Support = ...
Unanswerable Accuracy = ...
P50/P95 latency = ...
```

## 高频追问

### 为什么不用 LangChain？

不要回答“LangChain 太重”。

回答方向：这个项目主要目标之一是理解 runtime ownership 和状态边界，Nanobot current-source 的 loop/runner/tool/session/memory 分层便于 source-level tracing；如果业务生态要求 LangChain/LangGraph，也可以替换 orchestration 层。

### 为什么 MCP？

因为希望 Research retrieval service 与 Agent runtime 解耦，保持 schema、process/lifecycle 和最小权限边界；不是因为“现在 MCP 热”。

### 最大 bad case？

准备一个真实案例。例如：global chunk retrieval 的 Top-5 全被 HLL 占据，导致 corpus-level query 无法看到 ULL/DREX；定位为 source-diversity/document-selection 问题，而不是 LLM generation 问题。

### 为什么不直接上 Hybrid / Reranker？

因为小样本调参容易过拟合；先用诊断实验确认瓶颈，再在更大的 multi-paper eval set 上比较。
