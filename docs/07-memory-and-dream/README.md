# 07 - 记忆系统实战：Session、AutoCompact 与 Dream

> **阅读时间**：约 2 小时  
> **前置知识**：[06 - 安装与上手](../06-current-source-setup/README.md)  
> **学习目标**：深入理解 Nanobot 的双层记忆架构、MemoryConsolidator 压缩机制、会话管理，掌握面试高频考点

---

![记忆系统漫画](../../comics/04-memory-system.png)

*Nanobot 双层记忆：MEMORY.md（记忆面包 = 长期记忆）+ HISTORY.md（历史时间线）*

## 目录

- [7.1 为什么 Agent 需要记忆](#71-为什么-agent-需要记忆)
- [7.2 记忆系统的挑战](#72-记忆系统的挑战)
- [7.3 Nanobot 多层记忆架构](#73-nanobot-多层记忆架构)
- [7.4 MEMORY.md —— 长期记忆](#74-memorymd--长期记忆)
- [7.5 history.jsonl —— 历史时间线](#75-historyjsonl--历史时间线)
- [7.6 AutoCompact、Consolidator 与 Dream](#76-autocompactconsolidator-与-dream)
- [7.7 短期记忆：Session 会话历史](#77-短期记忆session-会话历史)
- [7.8 记忆系统完整数据流](#78-记忆系统完整数据流)
- [7.9 记忆系统与其他框架对比](#79-记忆系统与其他框架对比)
- [7.10 实战练习](#710-实战练习)
- [7.11 面试高频题](#711-面试高频题)
- [7.12 本章小结](#712-本章小结)

---

## 7.1 为什么 Agent 需要记忆

### 7.1.1 无记忆 Agent 的问题

想象一个没有记忆的助手：

```
对话 1:
You: 我叫张三，是一名后端工程师
Agent: 你好张三！很高兴认识你。

对话 2（新会话）:
You: 我之前说我叫什么名字？
Agent: 抱歉，我不知道你的名字，这是我们的第一次对话。
```

这就是纯 LLM 的局限 —— **没有跨会话记忆**。每次对话都是全新的开始。

### 7.1.2 记忆赋予 Agent 的能力

| 能力 | 无记忆 | 有记忆 |
|------|--------|--------|
| 跨会话延续 | 每次重新开始 | 记住之前的对话 |
| 用户偏好 | 每次重新询问 | 自动适应 |
| 任务延续 | 无法暂停继续 | 支持长期项目 |
| 知识积累 | 不积累 | 持续学习 |
| 上下文理解 | 仅当前对话 | 理解历史背景 |

### 7.1.3 记忆系统的核心矛盾

设计 Agent 记忆系统需要平衡三个矛盾：

```
      完整性               成本
   (记住所有)          (节省 token)
       │                   │
       └────── 矛盾 ──────┘
               │
            实时性
        (快速检索)
```

1. **完整性 vs 成本**：记住所有信息需要巨大的上下文窗口，费用高昂
2. **完整性 vs 实时性**：存储所有信息使检索变慢
3. **成本 vs 实时性**：压缩信息虽然省钱，但可能丢失重要细节

> 💡 **面试要点**：能分析记忆系统的设计权衡，比只描述实现更能打动面试官。

---

## 7.2 记忆系统的挑战

### 7.2.1 LLM 的上下文窗口限制

```
模型上下文窗口对比：
┌──────────────────┬──────────────┐
│ 模型             │ 上下文窗口    │
├──────────────────┼──────────────┤
│ GPT-3.5          │ 4K / 16K     │
│ GPT-4o           │ 128K         │
│ Claude 3.5       │ 200K         │
│ DeepSeek-V3      │ 128K         │
│ Gemini 1.5 Pro   │ 2M           │
└──────────────────┴──────────────┘

128K tokens ≈ 约 10 万字 ≈ 一本短篇小说
```

看似很大，但实际上：
- System Prompt 占用 2000-5000 tokens
- 工具定义占用 3000-8000 tokens
- 技能摘要占用 1000-3000 tokens
- 长期记忆占用 500-2000 tokens
- **留给对话历史的空间其实有限**

### 7.2.2 信息遗忘的代价

如果简单地"截断"旧对话来适应窗口：
- 可能丢失用户的关键偏好
- 可能遗忘重要的任务上下文
- 可能重复询问已知信息（用户体验差）

### 7.2.3 业界常见方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| 滑动窗口截断 | 实现简单 | 丢失早期信息 |
| 向量检索（RAG） | 精确检索 | 需要向量库，架构复杂 |
| 摘要压缩 | 保留关键信息 | 有信息损失 |
| 知识图谱 | 结构化存储 | 实现复杂，维护成本高 |
| **文件存储（Nanobot）** | **简单透明** | **依赖文件 I/O** |

---

## 7.3 Nanobot 多层记忆架构

原版教程使用“MEMORY.md + HISTORY.md 双层记忆”解释早期 Nanobot。以 2026-09-24 current-source 为准，记忆链路已经变成：

```text
┌────────────────────────────────────────────────────────────┐
│                 Current Model Context                      │
│  本次 Provider 真正看到的 System + History + Current Input │
└───────────────────────────▲────────────────────────────────┘
                            │ ContextBuilder
┌───────────────────────────┴────────────────────────────────┐
│                  Session JSONL                             │
│  结构化消息 / Tool Call / metadata / provider state         │
└───────────────────────────┬────────────────────────────────┘
                            │ AutoCompact / Consolidator
┌───────────────────────────▼────────────────────────────────┐
│              memory/history.jsonl                          │
│  append-only 压缩历史，带 cursor / timestamp / content      │
└───────────────────────────┬────────────────────────────────┘
                            │ Dream
┌───────────────────────────▼────────────────────────────────┐
│  SOUL.md      USER.md       memory/MEMORY.md               │
│  Agent规则     用户稳定信息      工作长期事实                │
└────────────────────────────────────────────────────────────┘
```

关键点：

- **Session** 不是 Long-term Memory，它首先服务 Conversation Replay 与 Recovery。
- **AutoCompact / Consolidator** 负责把旧 Conversation 压缩、归档。
- **history.jsonl** 保存“发生过什么”的长期来源，但不会每轮全量进入 Context。
- **Dream** 从 History 中整理“真正值得继续保留什么”。
- **SOUL / USER / MEMORY** 是经过整理的 durable state。

> 💡 **面试要点**：模型表现出“记得”并不意味着模型参数发生更新，而是 Runtime 在新的 Context 中重新注入了持久化信息。

### 关键设计决策

为什么要拆成多层？

```text
Session Replay
需要：结构完整、可恢复

History Archive
需要：便宜、追加、能长期积累

Durable Memory
需要：简洁、当前有效、可人工审计

Current Context
需要：只放当前任务真正有价值的信息
```

这四个目标冲突，所以不应该由一个无限增长的 MEMORY.md 解决全部问题。

---

## 7.4 MEMORY.md —— 工作长期记忆

### 7.4.1 存储位置

```text
<agent-workspace>/memory/MEMORY.md
```

### 7.4.2 文件内容适合什么

current official memory model 中：

- `USER.md`：用户是谁、稳定偏好是什么；
- `MEMORY.md`：关于工作/项目“现在仍然成立”的事实；
- `history.jsonl`：这些事情一路如何发生。

例如：

```markdown
# Long-term Memory

## ResearchPilot
- Corpus 采用 document-aware retrieval。
- Citation contract 必须保留 doc_id / page / chunk_id。
- 当前评测集以 multi-paper query 为主。
```

不应该把每一次 retrieval result、每一条临时 Query 都永久写入 MEMORY.md。

### 7.4.3 注入方式

`MemoryStore.get_memory_context()` 会把 MEMORY.md 转换为 Long-term Memory Context，ContextBuilder 决定何时加入模型输入。

因此：

```text
MEMORY.md
   ↓
MemoryStore
   ↓
ContextBuilder
   ↓
Provider Context
```

### 7.4.4 为什么仍然使用透明文件

优点仍然成立：

- 可读；
- 可编辑；
- 可 Diff；
- 易备份；
- 不需要额外数据库。

但 current-source 用文件并不等于“没有复杂状态”：Session、Provider State、History Archive、Dream Cursor 等仍然分别管理。

### 7.4.5 MEMORY.md 的大小控制

长期文件应该是 **curated state**，不是历史垃圾桶。

好的 Memory 更新会：

- 合并重复事实；
- 修正冲突；
- 删除已经失效的 ephemeral state；
- 保留 durable project decision。

---

## 7.5 history.jsonl —— 历史时间线

### 7.5.1 存储位置

```text
<agent-workspace>/memory/history.jsonl
```

旧 `HISTORY.md` 现在主要作为 legacy migration 输入存在。

### 7.5.2 JSONL 结构

MemoryStore 为历史记录维护：

```text
cursor
timestamp
content
session_key（可选）
```

概念示例：

```json
{"cursor": 17, "timestamp": "2026-09-24 10:30", "content": "...", "session_key": "websocket:..."}
```

### 7.5.3 核心特性

- append-only；
- cursor 自增；
- 写入前清理模型内部 Think/模板泄露；
- 对单条历史做 hard cap；
- Dream 通过 `.dream_cursor` 记录处理进度；
- 不会把完整 History 每轮塞给模型。

### 7.5.4 MEMORY.md vs history.jsonl

| 维度 | MEMORY.md | history.jsonl |
|---|---|---|
| 含义 | 当前仍值得长期保留的工作事实 | 历史发生过程的压缩归档 |
| 更新方式 | Dream 可重写/整理 | 追加 |
| 每轮 Context | 可作为 Long-term Memory 注入 | 不全量注入 |
| 可增长性 | 应保持精炼 | 可长期增长 |
| 用途 | 当前决策上下文 | Dream / 过去事件检索 |

---

## 7.6 AutoCompact、Consolidator 与 Dream

### 7.6.1 AutoCompact 触发

current `AgentDefaults`：

```text
idleCompactAfterMinutes = 15
idleCompactCheckIntervalSeconds = 60
```

AgentLoop 定期扫描 idle Session。满足：

- 已空闲达到 TTL；
- 有尚未归档的消息；
- 当前不是 active session；
- 没有正在进行的 archive；

才会 schedule background compaction。

### 7.6.2 Consolidator 做什么

`Consolidator` 接收：

- MemoryStore；
- SessionManager；
- ContextBuilder 的 message builder；
- Tool definitions；
- prompt context resolver。

它负责把旧 Transcript 总结为：

- Session summary/checkpoint；
- history archive entry；
- provider-compaction summary 等。

### 7.6.3 Dream 取代旧 save_memory 虚拟工具

旧教程描述：

```text
LLM 调 save_memory
→ AgentRunner 内部拦截
→ 写 MEMORY.md
```

这不再是 current-source 的主要长期记忆机制。

现在：

```text
Conversation
→ Consolidator / history.jsonl
→ Dream
→ SOUL.md / USER.md / MEMORY.md
```

Dream 可以由 Gateway system job 调度，也可以通过命令手动触发。

### 7.6.4 Dream 为什么需要 GitStore

MemoryStore 为 durable memory 使用 GitStore。

原因：

```text
自动模型写入
→ 可能写错
→ 必须能检查 Diff
→ 必须能恢复
```

所以 current command 提供 Dream history/restore 能力。

### 7.6.5 鲁棒性设计

current MemoryStore 包含多个防御点：

- legacy HISTORY.md migration 是 best-effort；
- cursor allocation 与 append 使用锁；
- oversized entry 截断；
- Think/internal marker 清理；
- durable file 使用原子写入；
- Dream 使用 cursor 防止重复处理完整历史。

### 7.6.6 压缩前后理解

压缩不是“删掉用户原话然后只剩一个摘要”。

正确理解：

```text
完整 Session persistence
        ↓
为了下一次模型 Context
生成更小的 Summary / Archive
        ↓
减少 Token 成本与延迟
```

Model Context Optimization 与 Durable History Retention 是两件事。

---

## 7.7 短期记忆：Session 会话历史

### 7.7.1 Session 的概念

Session 是 current-source 的近期 Conversation State。

默认位置：

```text
<config-dir>/sessions/<workspace-id>/*.jsonl
```

### 7.7.2 JSONL 格式

Session 不只保存 User/Assistant Text，还可能保存：

- Tool messages；
- hidden history metadata；
- automation marker；
- summary checkpoint；
- runtime checkpoint；
- model preset metadata。

### 7.7.3 _save_turn() / Persist Stage

Runner 返回的是完整执行结果，但 AgentLoop 保存时要维护 **save boundary**，避免把旧 History 再次重复 Append。

current Turn pipeline 中：

```text
run
→ save
→ respond
```

持久化与出站交付是独立阶段。

### 7.7.4 关键处理细节

current Session 还支持：

- provider conversation state；
- pending follow-up recovery；
- per-session FIFO；
- command messages 与 model-visible history 分离；
- temporary/ephemeral policy。

### 7.7.5 Session 加载与恢复

SessionManager 管：

- identity；
- cache；
- retention；
- persistence。

AgentLoop 的 restore stage 还可以恢复 runtime checkpoint 和 interrupted Turn。

所以 current Session 已经接近一个轻量 conversation state store，而不只是聊天日志。

---

## 7.8 记忆系统完整数据流

```text
用户消息
   ↓
AgentLoop / Session
   ↓
ContextBuilder
   ↓
AgentRunner
   ↓
Assistant / Tool messages
   ↓
Persist Session JSONL
   ↓
Session idle
   ↓
AutoCompact
   ↓
Consolidator
   ↓
memory/history.jsonl + Session Summary
   ↓
Dream
   ↓
SOUL.md / USER.md / MEMORY.md
   ↓
下一次 ContextBuilder 再注入
```

还有一个非常重要的分支：

```text
用户发现 Dream 写错
   ↓
/dream-log
   ↓
查看 Git history / Diff
   ↓
/dream-restore
```

这让自动长期记忆仍然保留人为控制。

## 7.9 记忆系统与其他框架对比

### 7.9.1 主流方案对比

| 框架/方案 | 存储方式 | 检索方式 | 压缩方式 | 透明度 | 复杂度 |
|-----------|---------|---------|---------|--------|--------|
| **Nanobot** | **Markdown 文件** | **全文注入 + 文件检索** | **LLM 摘要** | **高** | **低** |
| LangChain | 向量数据库 | 向量相似度 | 无/手动 | 低 | 中 |
| AutoGPT | JSON 文件 | 向量检索 | 无 | 中 | 中 |
| MemGPT | 虚拟分页 | 分页检索 | LLM 编辑 | 中 | 高 |
| CrewAI | 共享内存 | 直接访问 | 无 | 低 | 低 |

### 7.9.2 向量库 vs 文件存储 vs 知识图谱

**向量库方案（如 LangChain + Chroma/Pinecone）**

```
优点：
✅ 语义检索精确（"找关于数据库的讨论" 即使没有"数据库"关键词也能找到）
✅ 适合大量非结构化文档
✅ 检索速度快（O(log n)）

缺点：
❌ 需要外部依赖（向量数据库）
❌ 向量化过程有信息损失
❌ 更新不直观（需要重新 embedding）
❌ 调试困难（向量不可读）
```

**文件存储方案（Nanobot）**

```
优点：
✅ 零外部依赖
✅ 完全透明（人类可读可编辑）
✅ Agent 原生理解（Markdown）
✅ 版本控制友好（git 可追踪）
✅ 实现简单

缺点：
❌ 不支持语义检索（只能关键词匹配）
❌ 全文注入消耗 token
❌ 不适合超大规模记忆
```

**知识图谱方案（如 Neo4j + LLM）**

```
优点：
✅ 结构化存储关系
✅ 复杂推理能力（多跳查询）
✅ 知识去重

缺点：
❌ 实现极其复杂
❌ 需要实体抽取和关系建模
❌ 维护成本高
❌ 不适合轻量级 Agent
```

### 7.9.3 Nanobot 方案的适用场景

```
适合 Nanobot 文件记忆的场景：
✅ 个人助手（单用户，记忆量小）
✅ 轻量级 Agent（快速原型）
✅ 开发学习（透明可调试）
✅ 记忆内容结构化（事实列表）

不太适合的场景：
❌ 海量文档检索（1000+ 页）
❌ 多用户共享知识库
❌ 需要复杂关系推理
❌ 实时高并发场景
```

---

## 7.10 实战练习

### 练习 1：观察 Session → AutoCompact → History

1. 在一个 Session 连续进行多轮 Tool-using 对话；
2. 找到对应 Session JSONL；
3. 临时把 idle compact threshold 调低用于实验；
4. 保持 Gateway 运行；
5. 等 Session idle 后观察 summary 与 `memory/history.jsonl`；
6. 对比 compact 前后的下一次 Model Context。

记录：

```text
Session message count
history cursor
summary text
下一轮 prompt token
```

### 练习 2：Dream 跨 Session 记忆

Session A：

```text
我正在做 ResearchPilot。
论文回答必须保留 doc_id/page/chunk_id。
这是长期项目约束。
```

执行 Dream，然后检查：

```text
USER.md
memory/MEMORY.md
/dream-log
```

新建 Session B，确认模型能在合理场景下使用该长期信息。

### 练习 3：错误长期记忆与恢复

1. 故意让长期事实发生一次修改；
2. 运行 Dream；
3. 查看 Dream Git history；
4. 验证错误影响；
5. 用 restore 恢复；
6. 再次验证 Context。

> 这个实验比“能记住名字”更有面试价值，因为它展示了你理解自动记忆的审计与回滚。

## 7.11 面试高频题

### 题目 1：Nanobot 的记忆系统是如何设计的？

> "current-source 不是 MEMORY.md + HISTORY.md 双文件。近期状态在 Session JSONL；idle Session 会通过 AutoCompact/Consolidator 做 Summary 与 Archive，长期历史进入 memory/history.jsonl；Dream 再从历史中整理 SOUL.md、USER.md 和 memory/MEMORY.md。下一轮由 ContextBuilder 选择性注入。Durable Memory 还有 GitStore 做审计和恢复。"

### 题目 2：如何处理上下文窗口溢出？

> "不能只做尾部截断。current Nanobot 会区分 Session persistence 与 Current Context，并通过 Context Governance、Tool Result 上限、AutoCompact、Transcript Summary 等手段控制 Context。长期历史不会全量注入。"

### 题目 3：长期记忆与短期记忆的区别？

> "Session 追求可恢复的对话结构；Dream-managed USER/MEMORY 追求当前仍有效的稳定事实。History Archive 则处于中间层，保存过去发生过什么。"

### 题目 4：为什么不用向量数据库？

> "Nanobot 的 durable profile/work state 规模通常不大，透明 Markdown + History JSONL 易于审计和编辑。向量库更适合大规模外部知识检索，例如我的 ResearchPilot 论文 Corpus。两者解决的不是同一个问题。"

### 题目 5：如果让你改进 Nanobot 的记忆系统，你会怎么做？

可以从这些方向回答：

- Memory provenance：记录每条长期事实来源；
- Conflict detector：新旧事实冲突时要求显式 correction；
- Sensitive-data policy：避免凭据进入 durable memory；
- Eval：测跨 Session recall、stale-memory rate、false-memory rate；
- Retrieval：当 history 超大时，为 history search 增加更系统的索引，而不是把所有历史塞 Prompt。

## 7.12 本章小结

### 核心知识点

```
Nanobot 记忆系统 = MEMORY.md + HISTORY.md + Session JSONL

MEMORY.md（长期记忆）
├── 始终注入 System Prompt
├── MemoryConsolidator 整体重写
└── 关键事实、偏好、状态

HISTORY.md（历史时间线）
├── 仅追加模式
├── 不注入（节省 token）
└── 通过 read_file 按需检索

Session JSONL（短期记忆）
├── 完整对话记录
├── _save_turn() 持久化
└── 清理 thinking 标签 + 图片占位符

MemoryConsolidator（压缩器）
├── 触发：token 超过 context_window_tokens
├── 流程：构造 Prompt → save_memory 工具调用
└── 容错：tool_choice → auto → Raw Archive
```

### 面试记忆清单

| 考点 | 一句话回答 |
|------|-----------|
| 记忆架构 | 双层文件记忆 + 会话历史的三级架构 |
| MEMORY.md | 长期记忆，始终注入 System Prompt |
| HISTORY.md | 历史时间线，仅追加，按需检索 |
| 压缩触发 | token 数超过 context_window_tokens |
| 压缩工具 | save_memory 虚拟工具（history_entry + memory_update） |
| 容错机制 | tool_choice → auto → Raw Archive 三级回退 |
| 为什么用文件 | 零依赖、透明可编辑、Agent 原生理解 |

---

> **下一章**：[08 - 技能与工具](../08-skills-tools-plugins/README.md) —— 深入理解 Nanobot 的 Skill 系统和工具链