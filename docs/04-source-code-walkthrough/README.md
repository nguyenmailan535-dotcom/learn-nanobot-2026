# 04 — Current-source Walkthrough

## 本章打法

不要“从第一行读到最后一行”。使用 **一个输入追一条链**。

推荐问题：

```text
用户从 CLI 发送 "list files"
第一次进入 AgentRunner 之前，messages 和 tools 是怎么准备好的？
```

## Trace A：Inbound → Context

先定位：

```text
InboundMessage
session key
workspace scope
Session restore
ContextBuilder
initial_messages / AgentRunSpec
```

Codex 只允许回答这个范围，不要扩散到 memory/Dream。

## Trace B：Tool Call

第二轮再追：

```text
Provider response
→ parsed tool call
→ ToolRegistry
→ tool.execute(...)
→ ToolResult
→ append back to messages
→ next provider call
```

## Trace C：Final answer

最后追：

```text
AgentRunResult
→ AgentLoop post-run
→ Session persistence
→ OutboundMessage
```

## 推荐 grep 关键词

```text
AgentRunSpec(
initial_messages
tool_calls
execute(
ToolResult
AgentRunResult
publish_outbound
```

## 不要做什么

- 不要一次让 Codex“解释整个 nanobot”；
- 不要复制数百行源码到笔记；
- 不要只记类名，不记 input/output 数据结构；
- 不要把注释当最终事实，要看真实调用点。

## 你的源码笔记模板

```markdown
### 入口
file:function

### 输入
...

### 输出
...

### 下一跳
...

### 为什么放在这一层
...

### 我验证过的运行现象
...
```

## 完成标准

你能白板画出一次包含一个 tool call 的完整 turn，并指出至少 6 个 current-source 文件。
