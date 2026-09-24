# 07 - 记忆系统实战

> **阅读时间**：约 2 小时  
> **前置知识**：[06 - 安装与上手](../06-install-and-hands-on/README.md)  
> **学习目标**：深入理解 Nanobot 的双层记忆架构、MemoryConsolidator 压缩机制、会话管理，掌握面试高频考点

---

![记忆系统漫画](../../comics/04-memory-system.png)

*Nanobot 双层记忆：MEMORY.md（记忆面包 = 长期记忆）+ HISTORY.md（历史时间线）*

## 目录

- [7.1 为什么 Agent 需要记忆](#71-为什么-agent-需要记忆)
- [7.2 记忆系统的挑战](#72-记忆系统的挑战)
- [7.3 Nanobot 双层记忆架构](#73-nanobot-双层记忆架构)
- [7.4 MEMORY.md —— 长期记忆](#74-memorymd--长期记忆)
- [7.5 HISTORY.md —— 历史时间线](#75-historymd--历史时间线)
- [7.6 MemoryConsolidator 压缩机制](#76-memoryconsolidator-压缩机制)
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

## 7.3 Nanobot current-source 记忆架构

原版“MEMORY.md + HISTORY.md 双层记忆”是旧版实现。2026-09-24 current-source 应该分成四层：

```
Current Model Context
        ↑
Session JSONL
        ↓
AutoCompact / Consolidator
        ↓
memory/history.jsonl
        ↓
Dream
        ↓
SOUL.md / USER.md / memory/MEMORY.md
        ↓
下一次 ContextBuilder
```

核心区别：

- **Context**：这一轮模型真正看到什么
- **Session**：某个 conversation 的结构化 replay
- **history.jsonl**：压缩后的长期历史来源
- **SOUL/USER/MEMORY**：Dream 管理的 durable memory

---

## 7.4 MEMORY.md —— 长期记忆

### 7.4.1 存储位置

```
<agent-workspace>/memory/MEMORY.md
```

### 7.4.2 作用

保存跨 Session 有价值的长期事实，例如：

- 稳定项目背景
- 重要长期决策
- 持久约束
- 需要长期保留的知识

### 7.4.3 注入方式

`MemoryStore.get_memory_context()` 将内容包装为 Long-term Memory Context，由 `ContextBuilder` 在后续 Turn 构造 Context。

### 7.4.4 为什么仍然使用可读文件

优点仍然和原版教程相同：

- 透明
- 可编辑
- 可版本化
- 无额外向量数据库依赖

但 current-source 又额外引入 GitStore，使 Dream 的自动修改可以审计和恢复。

---

## 7.5 history.jsonl —— Consolidated History

### 7.5.1 存储位置

```
<agent-workspace>/memory/history.jsonl
```

### 7.5.2 数据形态

append-only JSONL，记录可包含：

```
cursor
timestamp
content
session_key
```

### 7.5.3 与旧 HISTORY.md 的关系

`HISTORY.md` 仍能在源码中看到，但主要用于 one-time legacy migration：

```
legacy HISTORY.md
→ parse
→ history.jsonl
→ backup HISTORY.md
```

因此 current 不能再把 HISTORY.md 当成主长期历史文件。

### 7.5.4 MEMORY.md vs history.jsonl

| 对比项 | MEMORY.md | history.jsonl |
|---|---|---|
| 语义 | 当前应长期记住什么 | 过去发生过什么的压缩历史 |
| 组织 | 人类可读 Markdown | append-only JSONL |
| 主要消费者 | ContextBuilder | Dream / Consolidation |
| 是否每轮全量注入 | 可选择性注入 | 否 |
| 是否直接编辑 | 可以谨慎编辑 | 通常不手工维护 |

---

## 7.6 Consolidator 与 AutoCompact

### 7.6.1 AutoCompact

`nanobot/agent/autocompact.py` 检查 idle Session：

```
idle?
+ 有 unarchived message?
+ 没有 active turn?
→ schedule compact
```

目的主要是 Context 管理，而不是删除完整 Session。

### 7.6.2 Consolidator

`nanobot/agent/memory.py` 中的 Consolidator 复用：

- SessionManager
- ContextBuilder.build_messages
- Tool Definitions
- Prompt Context Resolver

把较旧 conversation 总结/归档，并生成 Session Summary Checkpoint。

### 7.6.3 current 不再以 save_memory 虚拟工具为核心

旧版 `save_memory` 机制不应继续作为新版面试答案。current 主链是：

```
Session
→ Consolidation
→ history.jsonl
→ Dream
→ durable files
```

---

## 7.7 短期记忆：Session 会话历史

### 7.7.1 current Session

Session 不只是 user/assistant 文本，还可保存：

- Tool Call / Tool Result
- Metadata
- Provider Conversation State
- Summary Checkpoint
- Runtime Recovery State
- Model Selection
- Route

### 7.7.2 默认路径

```
<config-dir>/sessions/<workspace-id>/*.jsonl
```

### 7.7.3 为什么 Session 与 Workspace Memory 分开

Session 是 runtime conversation data；SOUL/USER/MEMORY 是 Agent-owned durable state。两者生命周期与访问边界不同。

---

## 7.8 Dream 与完整数据流

### 7.8.1 Dream 做什么

Dream 从新的 history archive 中整理长期信息，并更新：

```
SOUL.md
USER.md
memory/MEMORY.md
```

### 7.8.2 Dream Cursor

`.dream_cursor` 记录已处理历史位置，避免每次从头回放全部长期 archive。

### 7.8.3 GitStore

Dream 更新的 durable files 有版本记录，可以通过 current Dream commands 查看和恢复。

### 7.8.4 完整数据流

```
用户 Turn
  ↓
Session JSONL
  ↓
AutoCompact / Consolidator
  ↓
history.jsonl
  ↓
Dream
  ↓
SOUL / USER / MEMORY
  ↓
ContextBuilder
  ↓
新的 Model Context
```

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

### 练习 1：观察 Session 与 Context 压缩

1. 在同一 Session 连续对话多轮。
2. 打开 verbose 日志。
3. 观察 Session JSONL。
4. 等待/触发 compact。
5. 检查 Session metadata/summary 与 `memory/history.jsonl`。

目标：理解“压缩模型 Context”与“删除原始持久化数据”不是一回事。

### 练习 2：跨 Session Dream

Session A 输入稳定信息：

```
我主要研究网络测量。
论文回答时优先给证据与出处。
```

执行 current Dream 命令后，新建 Session B，验证是否可以从 USER/MEMORY 中恢复长期信息。

### 练习 3：错误长期记忆与恢复

故意加入一条错误稳定事实：

1. 运行 Dream；
2. 查看 Dream Log / Git Diff；
3. 修正或 Restore；
4. 再次验证 Context。

目标：理解为什么模型驱动的长期写入必须可审计。

## 7.11 面试高频题

### 题目 1：Nanobot 的 current Memory System 怎么设计？

> 四层：Current Context、Session、Consolidated history.jsonl、Dream-managed durable files。Session 负责 conversation replay，Consolidator/AutoCompact 负责旧上下文归档，Dream 负责长期 curated memory，ContextBuilder 再把需要的信息放回模型。

### 题目 2：AutoCompact 与 Dream 有什么区别？

> AutoCompact 主要解决 Session Context 太长；Dream 主要解决跨 Session 长期记忆整理。前者偏 Context Management，后者偏 Durable Memory Curation。

### 题目 3：为什么 history.jsonl 不直接全部放进 Prompt？

> 它会持续增长，而且“发生过”不等于“当前相关”。全量注入会增加 Token、延迟和干扰。

### 题目 4：HISTORY.md 现在还有什么作用？

> current-source 中主要是 legacy migration 输入；新的长期历史主文件是 `memory/history.jsonl`。

### 题目 5：为什么 Dream 使用 GitStore？

> 自动模型写入长期状态存在误改和幻觉风险，需要 Diff、审计和恢复。

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

> **下一章**：[08 - 技能与工具](../08-skills-and-tools/README.md) —— 深入理解 Nanobot 的 Skill 系统和工具链