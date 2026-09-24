# 13 — 面试题：以 current-source 为准

本章不提供 134 道需要死背的“标准答案”，而提供一组**必须能结合源码和项目回答**的高价值题。

## A. Agent Runtime

1. `AgentLoop` 和 `AgentRunner` 为什么拆开？
2. 一次 tool call 的 message flow 是什么？
3. Tool schema 为什么属于 model contract？
4. provider 返回 malformed/empty/length stop 时 runtime 怎么恢复？
5. Session lock 与全局并发限制分别解决什么？
6. 为什么 background trigger 不能直接注入正在执行的同一个 turn？

## B. Context / Session / Memory

7. Session history 和 long-term memory 有什么区别？
8. AutoCompact 做了什么，没做什么？
9. Consolidator 与 Dream 的职责如何区分？
10. `history.jsonl` 为什么不全量注入？
11. `SOUL.md` / `USER.md` / `MEMORY.md` 分别适合什么？
12. 为什么 memory update 需要 Git-backed audit/restore？
13. project workspace 切换后 memory 属于谁？

## C. Tool / Skill / Plugin / MCP

14. Tool、Skill、MCP server、Agent Plugin 分别是什么？
15. 为什么 Skill progressive loading 能降低 context bloat？
16. workspace skill 与 built-in skill 冲突怎么处理？
17. 为什么 MCP connection lifecycle 放在 composition root？
18. `enabledTools` 对 MCP 安全有什么意义？
19. local native Tool 与 remote MCP Tool 怎么选？
20. Agent Plugin 的 package immutability 有什么价值？

## D. Multi-agent / Automation

21. Subagent 适合哪些任务，不适合哪些任务？
22. `maxConcurrentSubagents` 与 `NANOBOT_MAX_CONCURRENT_REQUESTS` 有何区别？
23. Cron、local trigger、heartbeat 怎么选？
24. 为什么 automation 需要 linked topic/session？
25. at-least-once trigger delivery 对外部系统意味着什么？

## E. Security / Deploy

26. `restrictToWorkspace` 为什么不是 OS sandbox？
27. SSRF 在 Agent web/MCP 场景里为什么危险？
28. `allowFrom:["*"]` 的风险是什么？
29. 为什么 secret 不应放进 Agent workspace？
30. 暴露 OpenAI-compatible API 到公网前至少做什么？

## F. RAG / Research Agent

31. Dense retrieval 不命中，怎么判断 recall failure vs ranking failure？
32. chunk 越大为什么不一定 retrieval 越好？
33. 为什么 global chunk Top-K 会导致单篇论文霸榜？
34. document-aware retrieval 怎么缓解 source diversity 问题？
35. Answer 对，但 citation 不支持 claim，算成功吗？
36. 如何设计 unanswerable case？
37. Reranker 什么情况下根本救不了召回？
38. Eval set 太小会产生什么误导？
39. 你项目里真正测过哪些指标？
40. 给一个你遇到的 bad case，按 failure stage 诊断。

## G. Java 背景迁移

41. ToolRegistry 和 Spring Bean Registry 有什么相似/不同？
42. MessageBus 与 MQ / event bus 的区别？
43. Agent session 与 HTTP session 的异同？
44. 为什么 asyncio 并发不能简单类比 Java 多线程？
45. 如果把 Research MCP 做成 Java 服务，边界会怎么设计？

## 回答模板

每个源码题用：

```text
1. 先说责任边界
2. 再说 current-source 文件
3. 再说一次真实数据流
4. 最后说你做过的实验/bug
```

比背定义更可信。
