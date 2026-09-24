# 15 — 简历模板：只写你真的做过的内容

## 原则

简历 bullet = **动作 + 技术机制 + 结果/证据**。

不允许：

- “深入掌握”；
- “熟练使用”但没有产物；
- 抄教程示例指标；
- 固定写“Nanobot 4000 行源码”；
- 写已经过时的 `MemoryConsolidator 双层 MEMORY/HISTORY` 叙事；
- 写 `_concurrency_gate(3)`。

## 项目名建议

**ResearchPilot Agent：基于 Nanobot 的科研文献智能体**

技术栈根据你最终真实实现选择：

```text
Python / Nanobot / MCP / PyMuPDF4LLM / BGE / NumPy
Docker / Langfuse / Feishu ...（做了再写）
```

## 简历 bullet v1

> 下面所有 `[YOUR_METRIC]` 必须自己测。

```text
• 基于 HKUDS/nanobot current-source 构建科研文献 Agent，沿
  MessageBus → AgentLoop → AgentRunner → ToolRegistry 完成源码级调用链
  追踪，并将多论文检索能力封装为 MCP/Agent Plugin 接入运行时。

• 实现 PDF Parsing → sentence-aware chunking → BGE embedding →
  document-aware retrieval → grounded generation → citation 的多论文 RAG
  链路，在自建 [N]-query eval set 上取得 Document Recall@5=[YOUR_METRIC]、
  Citation Support=[YOUR_METRIC]。

• 针对 global chunk Top-K 的单文档候选挤占问题，引入 document-level
  aggregation 与 per-document passage selection，并通过 Bad Case 分析比较
  调整前后 [YOUR_METRIC] 的变化。

• 基于 Nanobot Skill progressive loading 与 MCP tool schema 设计科研工作流，
  保留 doc_id/page/chunk_id provenance；对无证据问题加入拒答规则并测试
  unanswerable accuracy=[YOUR_METRIC]。

• 使用 Session / AutoCompact / Dream 管理近期上下文与长期研究偏好；结合
  Subagent/Automation 实现 [你真实做过的并行论文分析/定期任务]，并完成
  workspace restriction、channel access control 与 Docker/Gateway 部署。
```

## 如果项目还没做到后半段

就只写前两条，不要为了“看起来丰满”写未来计划。

## 源码研究如何写

不要写：

```text
阅读 Nanobot 4000 行源码，掌握 Agent 框架
```

更好：

```text
追踪 current-source 中一次 tool-using turn 从 InboundMessage、ContextBuilder、
AgentRunSpec 到 AgentRunner/ToolRegistry 和 Session 持久化的完整链路，整理
可复现 source trace 与最小实验，并基于该运行时完成自定义能力扩展。
```

## 面试风险检查

简历每个名词都必须能回答：

- 我为什么用了它？
- 源码/实现入口在哪里？
- 我改了哪部分？
- 一个失败案例是什么？
- 指标怎么算？
