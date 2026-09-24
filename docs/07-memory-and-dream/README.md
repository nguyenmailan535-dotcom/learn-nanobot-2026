# 07 — Session / AutoCompact / Consolidation / Dream

## 先把“记忆”拆成四层

```text
1. Current live messages
2. Session JSONL
3. Consolidated history.jsonl
4. Dream-managed durable files
```

这比旧版“MEMORY.md + HISTORY.md”二分法准确得多。

## Session

近期结构化消息保存在：

```text
<config-dir>/sessions/<workspace-id>/*.jsonl
```

它是 conversation replay 的基础。

## AutoCompact

current config 典型字段：

```json
{
  "agents": {
    "defaults": {
      "idleCompactAfterMinutes": 15,
      "idleCompactCheckIntervalSeconds": 60
    }
  }
}
```

重点：AutoCompact 缩短送进模型的上下文，但**不等于删除完整 session history**。

## Consolidator

`nanobot/agent/memory.py` 中的 `Consolidator` 会把被 compact 的旧内容总结进：

```text
memory/history.jsonl
```

这份 archive 不应该默认整份塞回每次 prompt。

## Dream

Dream 用 accumulated history 去更新 curated durable files：

```text
SOUL.md
USER.md
memory/MEMORY.md
```

并使用 Git-backed change history 支撑查看/恢复。

常用命令：

```text
/dream
/dream-log
/dream-restore
/dream-prompt
```

## 必做实验

### Experiment A：跨 session 事实

Session A：告诉 Agent 3 个稳定事实。

运行 `/dream`。

Session B：重新询问其中 2 个事实，再问一个只属于偶发对话、不应成为 durable profile 的细节。

### Experiment B：查看文件

比较：

```text
session JSONL
memory/history.jsonl
USER.md
MEMORY.md
```

明确“哪个事实在哪一层”。

### Experiment C：bad memory

故意给出一个之后被纠正的事实，观察 Dream 下一次更新，练习 `/dream-log` 与 restore。

## 面试问题

- AutoCompact 与 Dream 的目标为什么不同？
- 为什么 history.jsonl 不直接全量注入 prompt？
- 为什么 durable memory 需要审计/恢复能力？
- Long-term memory 的问题为什么不是“加一个向量库”就结束？
