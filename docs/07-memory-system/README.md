# 07 - 记忆系统实战

> **阅读时间**：约 2 小时  
> **2026 current-source 说明**：本章直接沿用原版 learn-nanobot 的章节结构与主体内容；凡涉及 Nanobot 具体源码、配置、路径、记忆、并发、MCP 生命周期等实现细节，均按 HKUDS/nanobot main @ 2026-09-24 (source trace snapshot around 62aa6ba6a33790a656b952ef150517bd70d6eb30) 修订。

> **前置知识**：[06 - 安装与上手](../06-install-and-hands-on/README.md)  
> **学习目标**：深入理解 Nanobot 的双层记忆架构、Consolidator 压缩机制、会话管理，掌握面试高频考点

---

![记忆系统漫画](../../comics/04-memory-system.png)

*Nanobot 双层记忆：MEMORY.md（记忆面包 = 长期记忆）+ memory/history.jsonl（历史时间线）*

## 目录

- [7.1 为什么 Agent 需要记忆](#71-为什么-agent-需要记忆)
- [7.2 记忆系统的挑战](#72-记忆系统的挑战)
- [7.3 Nanobot 双层记忆架构](#73-nanobot-双层记忆架构)
- [7.4 MEMORY.md —— 长期记忆](#74-memorymd--长期记忆)
- [7.5 memory/history.jsonl —— 历史时间线](#75-historymd--历史时间线)
- [7.6 Consolidator 压缩机制](#76-memoryconsolidator-压缩机制)
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


## 7.3 Nanobot 双层记忆架构

原版的“双层记忆”框架需要升级为 current-source 的 **多阶段状态系统**：

~~~text
Current Model Context
        ↑
Session JSONL + provider state + summary
        ↓
AutoCompact / Consolidator
        ↓
memory/history.jsonl
        ↓
Dream
        ↓
SOUL.md / USER.md / memory/MEMORY.md
        ↓
下一轮 ContextBuilder
~~~

### 关键设计决策

1. **Session 与 Model Context 分开**：保存全部 replay 不等于每轮都注入全部历史。
2. **Compaction 与 Durable Memory 分开**：压缩会话主要解决 context 成本；Dream 才负责长期 curated state。
3. **History Archive 与 Memory 分开**：`history.jsonl` 是过去发生过什么，`MEMORY.md` 是现在值得长期记住什么。
4. **Dream 写入可审计**：通过 GitStore 跟踪 durable files，支持查看/恢复修改。


## 7.4 MEMORY.md —— 长期记忆

### 7.4.1 存储位置

~~~text
<agent-workspace>/memory/MEMORY.md
~~~

### 7.4.2 文件内容示例

~~~markdown
# Memory

## 项目上下文
- 正在构建 Research Agent
- Retrieval 服务要求返回 doc_id/page/chunk_id

## 重要决策
- evidence 不足时禁止补全
~~~

### 7.4.3 注入方式

current `MemoryStore.get_memory_context()` 将长期记忆构造成：

~~~text
## Long-term Memory
...
~~~

再由 ContextBuilder 注入本轮上下文。

### 7.4.4 为什么仍然用 Markdown

优点：
- 人类可读；
- 可直接审计；
- 易 Git diff；
- 适合稳定事实和行为偏好。

限制也要承认：
- 不适合海量语义检索；
- 冲突/过期信息需要 curation；
- Memory 越多不一定越好。

### 7.4.5 MEMORY.md 的大小控制

current 设计重点不是一个旧版固定字符阈值，而是：
- Dream 只提炼值得长期保留的信息；
- Session/History 不应全部搬进 MEMORY.md；
- 定期通过 Dream/audit 修正 stale/conflicting fact。


## 7.5 memory/history.jsonl —— 历史时间线

> **current-source 修订**：本节保留原版“历史时间线”的教学位置，但 current 主文件已经是 `memory/history.jsonl`；`memory/history.jsonl` 仅用于 legacy migration。

### 7.5.1 存储位置

~~~text
<agent-workspace>/memory/history.jsonl
~~~

### 7.5.2 文件内容示例

概念记录：

~~~json
{"cursor": 1, "timestamp": "2026-09-24 10:30", "content": "...", "session_key": "..."}
~~~

### 7.5.3 核心特性

- append-only；
- cursor 单调递增；
- 写入前清理内部 think/template 泄漏；
- 有 defensive size cap；
- 作为 Dream 的长期历史来源；
- 不会在每一轮全量注入模型。

### 7.5.4 MEMORY.md vs history.jsonl 对比

| 对比 | MEMORY.md | history.jsonl |
|---|---|---|
| 语义 | 当前长期事实/状态 | 过去会话的归档历史 |
| 写入 | Dream curation | Consolidation/archive |
| 读取 | ContextBuilder 可直接注入 | 主要供 Dream/历史维护 |
| 结构 | Markdown | JSONL |
| 是否每轮全量注入 | 可作为长期 memory context | 否 |


## 7.6 Consolidator / AutoCompact 压缩机制

### 7.6.1 触发条件

current `AutoCompact` 会周期检查 idle Session：
- session TTL 是否到期；
- 是否有 unarchived messages；
- 是否已有 compaction 在运行；
- 是否仍有 active turn。

满足条件后后台调用 Consolidator。

### 7.6.2 压缩流程详解

~~~text
Session 未归档消息
        ↓
Consolidator.compact_idle_session
        ↓
LLM 总结 transcript
        ↓
Session summary/checkpoint
        +
memory/history.jsonl archive
        ↓
下一次 ContextBuilder 使用 summary，而不是重放全部旧消息
~~~

### 7.6.3 长期记忆更新：Dream

旧版的 `Dream / MemoryStore` 虚拟工具已不是 current 主路径。现在 durable memory curation 主要由 Dream 完成：

~~~text
history.jsonl
→ Dream run
→ SOUL.md / USER.md / MEMORY.md
~~~

### 7.6.4 压缩 Prompt 的构造

Consolidator 复用 ContextBuilder message-building 和 Tool Definitions，使压缩模型能正确理解 Tool Call/Tool Result，而不是把历史当纯文本拼接。

### 7.6.5 鲁棒性设计

current 还需要考虑：
- malformed legacy history；
- oversized archive entry；
- stream timeout；
- provider state；
- process restart 后 summary recovery；
- compaction 失败不能破坏原 Session。

### 7.6.6 压缩前后对比示例

压缩前模型可能需要看到几十轮完整 transcript；压缩后：

~~~text
System / Memory / Skills
+ Session Summary
+ 最近必要的 Message Tail
+ Current User Input
~~~

从而降低 token、延迟和 prompt noise。


## 7.7 短期记忆：Session 会话历史

### 7.7.1 Session 的概念

Session 是结构化 conversation/runtime state，而不仅是短期“聊天文本”。

### 7.7.2 JSONL 格式

默认 Session Store 位于：

~~~text
<config-dir>/sessions/<workspace-id>/*.jsonl
~~~

而不是简单的 `<workspace>/sessions/`。

### 7.7.3 Persist Turn

current `AgentLoop` 把一次 Turn 拆成 restore/build/run/save/respond。persist stage 需要正确处理：
- early-persisted user input；
- Runner 新消息与旧 History 的边界；
- provider state；
- hidden metadata；
- automation/subagent marker；
- runtime checkpoint。

### 7.7.4 关键处理细节

UI 可见 History 与 LLM History 不必完全相同。例如 slash command 可持久化供 UI hydration，但带 `_command` 标记后可以不进入模型 replay。

### 7.7.5 Session 加载与恢复

current-source 支持：
- cache；
- provider conversation state；
- interruption/runtime checkpoint recovery；
- summary metadata；
- per-session model preset。

所以 Session 是 durability 层，不应被简化成一个 messages 数组。


## 7.8 记忆系统完整数据流

~~~text
用户 Turn
  ↓
Session JSONL
  ↓
ContextBuilder 选择历史进入 Model Context
  ↓
Session idle
  ↓
AutoCompact
  ↓
Consolidator
  ├── Session Summary / Checkpoint
  └── memory/history.jsonl
            ↓
          Dream
            ↓
  ┌─────────┼──────────┐
SOUL.md    USER.md   MEMORY.md
  └─────────┼──────────┘
            ↓
      下一轮 ContextBuilder
~~~

另外 durable memory 使用 GitStore 留存 audit/recovery 记录。

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

### 练习 1：观察 AutoCompact / Consolidation

1. 创建测试 Agent Workspace；
2. 设置较短的 session TTL / 使用手动 compact 命令辅助观察；
3. 连续产生多轮对话；
4. 对比 Session JSONL 的原始历史与 summary metadata；
5. 查看 `memory/history.jsonl` 是否产生 archive。

不要通过“把 context_window_tokens 设成 4000 后等 memory/history.jsonl 自动更新”来验证 current system。

### 练习 2：手动编辑长期记忆 + Dream

你仍可以手动编辑 MEMORY.md，但更重要的是：
1. 先在 Session 中建立稳定事实；
2. 触发 Dream；
3. 查看 USER.md / MEMORY.md diff；
4. 新建 Session 验证；
5. 用 dream log / restore 观察可审计性。

### 练习 3：分析 Session JSONL

统计：
- user/assistant/tool 消息；
- command marker；
- runtime metadata；
- summary/checkpoint；
- provider state 是否单独持久化。

### 练习 4：故意制造冲突 Memory

先让 Dream 保存“偏好 A”，后来用户改为“偏好 B”，观察 durable memory 如何更新。这个实验比只验证“记住了”更接近真实问题。


## 7.11 面试高频题

### 题目 1：Nanobot 的记忆系统是如何设计的？

> “current-source 是多阶段状态系统：Session JSONL 保存 conversation/runtime state；AutoCompact + Consolidator 对 idle history 做压缩归档并生成 summary；archive 进入 memory/history.jsonl；Dream 再从历史中整理 SOUL.md、USER.md、MEMORY.md。ContextBuilder 在下一轮选择性注入这些状态。”

### 题目 2：如何处理上下文窗口溢出？

> “不是直接删除旧 Session，而是通过 transcript compaction/session summary 降低下一轮上下文成本；Runner 还支持运行时 compaction。持久化历史和当前 model context 是两个不同问题。”

### 题目 3：长期记忆与短期记忆的区别？

- Session：某段 Conversation 的结构化 replay；
- History archive：压缩后的长期历史来源；
- Durable Memory：跨 Session 稳定事实；
- Current Context：本轮真正喂给模型的输入。

### 题目 4：为什么不用向量数据库？

Nanobot 的 durable profile/memory 规模较小、强调人类可读与可审计，Markdown 很合适；海量文档检索应由独立 RAG/MCP 服务承担，不应该硬塞进 USER/MEMORY。

### 题目 5：如果让你改进 Memory System？

可以讨论：
- conflict/staleness detection；
- evidence/provenance；
- per-memory confidence/TTL；
- structured facts + human review；
- sensitive-memory policy；
- retrieval layer 与 durable profile 分离。

## 7.12 本章小结

### 核心知识点

```
Nanobot 记忆系统 = Session + memory/history.jsonl + Dream-managed durable memory + Session JSONL

MEMORY.md（长期记忆）
├── 始终注入 System Prompt
├── Consolidator 整体重写
└── 关键事实、偏好、状态

memory/history.jsonl（历史时间线）
├── 仅追加模式
├── 不注入（节省 token）
└── 通过 read_file 按需检索

Session JSONL（短期记忆）
├── 完整对话记录
├── _save_turn() 持久化
└── 清理 thinking 标签 + 图片占位符

Consolidator（压缩器）
├── 触发：token 超过 context_window_tokens
├── 流程：构造 Prompt → Dream / MemoryStore 工具调用
└── 容错：tool_choice → auto → Raw Archive
```

### 面试记忆清单

| 考点 | 一句话回答 |
|------|-----------|
| 记忆架构 | 双层文件记忆 + 会话历史的三级架构 |
| MEMORY.md | 长期记忆，始终注入 System Prompt |
| memory/history.jsonl | 历史时间线，仅追加，按需检索 |
| 压缩触发 | token 数超过 context_window_tokens |
| 压缩工具 | Dream / MemoryStore 虚拟工具（history_entry + memory_update） |
| 容错机制 | tool_choice → auto → Raw Archive 三级回退 |
| 为什么用文件 | 零依赖、透明可编辑、Agent 原生理解 |

---

> **下一章**：[08 - 技能与工具](../08-skills-and-tools/README.md) —— 深入理解 Nanobot 的 Skill 系统和工具链