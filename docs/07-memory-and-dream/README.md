# 07 - Memory System 2.0：Session、AutoCompact、Consolidation 与 Dream

> 🎯 **本章目标**：彻底放弃旧版“MEMORY.md + HISTORY.md 双层记忆”的简化模型，按 current-source 理解短期会话、压缩归档和长期 curated memory 的完整链路，并亲自做一次跨 Session 的 Dream 实验。

---

## 目录

- [7.1 为什么 Agent 需要 Memory](#71-为什么-agent-需要-memory)
- [7.2 先区分四层状态](#72-先区分四层状态)
- [7.3 Session：结构化 Conversation Replay](#73-session结构化-conversation-replay)
- [7.4 AutoCompact：为什么不是删除历史](#74-autocompact为什么不是删除历史)
- [7.5 Consolidator：把旧对话变成可归档信息](#75-consolidator把旧对话变成可归档信息)
- [7.6 history.jsonl：长期历史来源，不是每轮 Prompt](#76-historyjsonl长期历史来源不是每轮-prompt)
- [7.7 Dream：从历史中整理 Durable Memory](#77-dream从历史中整理-durable-memory)
- [7.8 MemoryStore 源码](#78-memorystore-源码)
- [7.9 GitStore：为什么 Memory 需要可审计和恢复](#79-gitstore为什么-memory-需要可审计和恢复)
- [7.10 ContextBuilder 如何注入 Memory](#710-contextbuilder-如何注入-memory)
- [7.11 Legacy HISTORY.md 迁移](#711-legacy-historymd-迁移)
- [7.12 三个必做实验](#712-三个必做实验)
- [7.13 Memory 常见失败模式](#713-memory-常见失败模式)
- [7.14 面试高频题](#714-面试高频题)
- [7.15 本章总结](#715-本章总结)

---

## 7.1 为什么 Agent 需要 Memory

假设用户第一天说：

~~~text
我主要研究网络测量。
回答论文问题时要先给证据。
我的项目希望优先使用 Python。
~~~

第二天新开 Session：

~~~text
继续昨天的项目。
~~~

如果只有当前 Session，Agent 不知道“昨天”。

但把所有历史原样塞进每次 Prompt 也不现实：

- Token 无限增长；
- latency 上升；
- 成本上升；
- 旧信息干扰当前问题；
- 隐私与污染风险上升。

所以 Memory System 的核心不是：

> 怎么把所有东西都记住？

而是：

> **哪些状态短期保存，哪些归档，哪些提炼成长期稳定事实，以及什么时候重新注入模型。**

---

## 7.2 先区分四层状态

current mental model：

~~~text
1. Current Model Context
2. Session JSONL
3. memory/history.jsonl
4. Dream-managed durable files
~~~

关系：

~~~text
Current Model Context
      ↑
Session Replay / Summary
      ↑
Consolidated History Archive
      ↓
Dream
      ↓
SOUL / USER / MEMORY
~~~

| 层 | 目的 |
|---|---|
| Current Context | 这一次模型需要看什么 |
| Session | 恢复一段 Conversation |
| history.jsonl | 保存压缩后的长期历史来源 |
| Durable Files | 跨 Session 真正值得保留的稳定信息 |

---

## 7.3 Session：结构化 Conversation Replay

源码：

~~~text
nanobot/session/manager.py
~~~

SessionManager 当前职责：

> Manage session identity, caching, retention, and persistence.

Session 不只是 List<Message>。

还可能包含：

- metadata；
- provider state；
- summary checkpoint；
- policy；
- route；
- model preset selection；
- recovery state。

### 为什么必须结构化

如果只存：

~~~text
USER: ...
ASSISTANT: ...
~~~

就很难恢复：

- Tool Call；
- Tool Result；
- hidden runtime metadata；
- provider-specific conversation state；
- automation marker；
- recovery checkpoint。

---

## 7.4 AutoCompact：为什么不是删除历史

源码：

~~~text
nanobot/agent/autocompact.py
~~~

AutoCompact 周期检查：

~~~text
是否 idle？
是否有 unarchived messages？
是否正在 active turn？
是否已经 archiving？
~~~

满足条件：

~~~text
schedule background
→ compact_idle_session
~~~

### prepare_session

新 Turn 开始时：

~~~text
AutoCompact.prepare_session
~~~

会读取：

- in-memory summary；
- 或 persisted summary metadata。

### 核心理解

AutoCompact 的目标：

> **减少下一次模型调用携带的历史上下文。**

不等于：

> 删除完整 Session 历史。

~~~text
Model Context Optimization
≠
Durable Data Deletion
~~~

---

## 7.5 Consolidator：把旧对话变成可归档信息

源码：

~~~text
nanobot/agent/memory.py
~~~

AgentLoop 初始化时创建 Consolidator，并注入：

~~~text
MemoryStore
SessionManager
ContextBuilder.build_messages
ToolRegistry.get_definitions
Prompt Context Resolver
~~~

### 为什么复用 build_messages

Compaction 不应该自己发明另一种历史格式。

复用 ContextBuilder 的 message-building 语义能减少：

~~~text
正常聊天理解一种 transcript
压缩时又理解另一种 transcript
~~~

之间的偏差。

### 为什么需要 Tool Definitions

历史可能包含 Tool Call/Tool Result。

如果压缩模型完全不知道工具 contract，就可能错误总结执行过程。

---

## 7.6 history.jsonl：长期历史来源，不是每轮 Prompt

文件：

~~~text
workspace/memory/history.jsonl
~~~

它是 append-only archive。

记录可包含：

~~~text
cursor
timestamp
content
session_key
~~~

### 与 MEMORY.md 的差别

~~~text
history.jsonl
= 过去发生过什么的压缩历史

MEMORY.md
= 现在应该长期记住什么
~~~

两者不能等同。

### 为什么不全量注入 Prompt

它会不断增长：

~~~text
100 条
1000 条
10000 条
~~~

全量注入会重新制造 context explosion。

所以它更像 Dream 的长期 evidence/source。

---

## 7.7 Dream：从历史中整理 Durable Memory

Dream 的目标：

~~~text
history archive
      ↓
periodic / manual Dream
      ↓
curate durable knowledge
      ↓
SOUL.md
USER.md
memory/MEMORY.md
~~~

### SOUL.md

适合：

- Agent personality；
- style；
- 长期行为倾向。

### USER.md

适合：

- 用户稳定偏好；
- 长期背景；
- 持续 profile facts。

### MEMORY.md

适合：

- 项目长期事实；
- 持久状态；
- 有价值知识总结。

### 不应该存什么

不要把：

- 每次 Query；
- 一次性细节；
- 大段论文原文；
- 每个 Retrieval Result；

全部固化。

Memory 越多并不一定越好。

---

## 7.8 MemoryStore 源码

current class 注释：

~~~python
class MemoryStore:
    """Pure file I/O for memory files: MEMORY.md, history.jsonl, SOUL.md, USER.md."""
~~~

初始化管理：

~~~text
memory/MEMORY.md
memory/history.jsonl
legacy HISTORY.md
SOUL.md
USER.md
.cursor
.dream_cursor
GitStore
~~~

### get_memory_context

MemoryStore 有 get_memory_context，给 ContextBuilder 提供：

~~~text
## Long-term Memory
...
~~~

### append_history

写 History 前还会：

- strip internal think/template leak；
- truncate oversized content；
- 分配 cursor；
- append JSONL。

说明 Memory persistence 也需要数据治理。

---

## 7.9 GitStore：为什么 Memory 需要可审计和恢复

MemoryStore 初始化 GitStore，并跟踪：

~~~text
SOUL.md
USER.md
memory/MEMORY.md
memory/.dream_cursor
~~~

### 为什么使用 Git-backed History

Dream 是模型驱动的写入。

模型可能：

- 错误修改长期事实；
- 过度总结；
- 删除重要偏好；
- 把临时信息固化。

所以 Durable Memory 必须能：

~~~text
查看修改
审计修改
恢复修改
~~~

这就是 /dream-log、/dream-restore 背后的工程动机。

---

## 7.10 ContextBuilder 如何注入 Memory

文件：

~~~text
nanobot/agent/context.py
~~~

ContextBuilder 持有：

~~~text
MemoryStore
SkillsLoader
~~~

Context 大致组合：

~~~text
bootstrap identity
+ memory context
+ skills
+ project instructions
+ session history
+ current input
~~~

完整链路：

~~~text
Dream 修改 MEMORY.md
        ↓
下一次 ContextBuilder
        ↓
get_memory_context
        ↓
Current Prompt
        ↓
模型表现出“记得”
~~~

这不是模型参数更新。

---

## 7.11 Legacy HISTORY.md 迁移

current MemoryStore 仍有：

~~~text
legacy HISTORY.md
~~~

但用途是 migration。

检测到旧 HISTORY.md 且新 history.jsonl 尚未建立时：

~~~text
parse legacy
→ write JSONL
→ set cursor
→ backup HISTORY.md
~~~

所以：

> “源码还能搜到 HISTORY.md”不代表它仍是 current architecture 主路径。

兼容代码不等于当前设计。

---

## 7.12 三个必做实验

### Experiment A：跨 Session Durable Fact

Session A：

~~~text
我主要研究网络测量。
回答论文问题时希望先给证据。
我最近在做 Research Agent。
~~~

执行：

~~~text
/dream
~~~

Session B：

~~~text
我主要研究什么？
论文回答应该采用什么方式？
~~~

### Experiment B：比较四层文件

观察：

~~~text
Session JSONL
memory/history.jsonl
USER.md
memory/MEMORY.md
~~~

自己做表：

| 信息 | Session | history | USER | MEMORY |
|---|---:|---:|---:|---:|
| 临时问题 | ? | ? | ? | ? |
| 稳定偏好 | ? | ? | ? | ? |
| 项目事实 | ? | ? | ? | ? |

### Experiment C：错误 Memory + Restore

1. 输入一个错误长期事实；
2. Dream；
3. 查看 dream log；
4. 纠正；
5. 再 Dream；
6. 必要时 Restore。

目标不是看功能，而是理解为什么长期自动写入必须可审计。

---

## 7.13 Memory 常见失败模式

### Over-memory

把所有细节固化，Prompt 越来越脏。

### Stale Memory

用户偏好已经变化，但旧事实未更新。

### Conflicting Memory

USER 与 MEMORY 相互矛盾。

### Hallucinated Consolidation

压缩模型总结出历史中不存在的事实。

### Sensitive Persistence

Credential/private content 被错误写进 Workspace。

### Context Pollution

history archive 被错误全量注入 Context。

---

## 7.14 面试高频题

### Q1：Session 与 Memory 有什么区别？

> Session 负责某个 Conversation 的结构化 replay；Memory 是跨更长时间整理后的 durable knowledge。当前模型 Context 则是从这些状态中选择性构造的输入。

### Q2：AutoCompact 与 Dream 有什么区别？

> AutoCompact 主要优化 Session Context 和 idle history；Dream 从长期 archive 中整理 SOUL/USER/MEMORY。前者偏 context management，后者偏 durable memory curation。

### Q3：为什么 history.jsonl 不全量进 Prompt？

因为它持续增长，而且 Archive 的目标是保留历史来源，不代表每条都与当前任务相关。

### Q4：为什么使用 GitStore？

因为 Dream 是自动、模型驱动的长期写入，需要审计、Diff 和恢复。

---

## 7.15 本章总结

新版 Memory System：

~~~text
Live Turn
   ↓
Session JSONL
   ↓
AutoCompact / Consolidator
   ↓
memory/history.jsonl
   ↓
Dream
   ↓
SOUL.md / USER.md / MEMORY.md
   ↓
下一次 ContextBuilder
~~~

下一章继续进入另一个变化很大的部分：Tool、Skill、Agent Plugin 到底如何配合。
