# 10 - 子 Agent、Cron 与 Heartbeat

> **阅读时间**：约 2 小时  
> **前置知识**：[09 - 多平台接入](../09-mcp-integration/README.md)  
> **学习目标**：沿用原版章节组织，以 **2026-09-24 HKUDS/nanobot main** 为准理解 SubagentManager、CronService、Local Trigger 与 Gateway Heartbeat 的真实职责和协作关系。

---

## 目录

- [10.1 为什么需要子Agent和定时任务](#101-为什么需要子agent和定时任务)
- [10.2 子Agent（SubAgent）系统](#102-子agentsubagent系统)
- [10.3 定时任务（Cron）系统](#103-定时任务cron系统)
- [10.4 Heartbeat 心跳任务](#104-heartbeat-心跳任务)
- [10.5 三者的协作关系](#105-三者的协作关系)
- [10.6 实战练习](#106-实战练习)
- [10.7 面试高频题](#107-面试高频题)
- [10.8 本章小结](#108-本章小结)

---

## 10.1 为什么需要子Agent和定时任务

### 10.1.1 主Agent的局限

一个用户 Turn 可以很长，但不是所有任务都适合塞进主 Agent 的单线程决策链。

典型问题：

- 多个独立子任务天然可以并行；
- 某些工作需要后台继续；
- 某些任务需要未来某个时间执行；
- 某些周期检查没有变化时不应该打扰用户；
- CI/脚本等本地系统需要主动触发 Agent。

### 10.1.2 解决方案

current-source 把这些需求拆开：

```text
Subagent
→ 当前目标中的并行/隔离子任务

Cron
→ 某个明确时间或周期的 Session-bound Scheduled Turn

Local Trigger
→ CI / Shell / 外部本地流程显式触发一个 Turn

Heartbeat
→ 周期后台检查；没重要变化时静默
```

不要把“后台工作”全部叫 Cron，也不要为了并行就无脑 Spawn 多 Agent。

---

## 10.2 子Agent（SubAgent）系统

### 10.2.1 SpawnTool 启动子代理

模型通过 Spawn 类 Tool 把一个任务委托给 `SubagentManager`。

概念流程：

```text
Main Agent
   ↓ spawn(task)
SubagentManager
   ↓
Task ID + SubagentStatus
   ↓
AgentRunner / AgentRunSpec
   ↓
Scoped ToolRegistry
   ↓
Result
   ↓
父 Session 注入 / 通知
```

### 10.2.2 SubagentManager 管理

源码：

```text
nanobot/agent/subagent.py
```

current-source 的关键点：

- `spawn()`：后台运行；
- `run_inline()`：同步等待结果；
- 记录 `task_id` / label / started_at；
- 维护 running task map；
- 维护 Session → Subagent task 关系；
- 结束后清理状态；
- 支持父 Session 继续接收结果。

### 10.2.3 SubAgent 与主Agent的区别

current Subagent **不需要再构造一个完整 AgentLoop**。

它复用：

```text
AgentRunner
AgentRunSpec
```

并构造更聚焦的：

- System Prompt；
- Project Workspace；
- Tool Scope；
- Runtime。

这正是 AgentLoop / AgentRunner 分层的价值。

### 10.2.4 为什么限制工具集

Subagent 的 ToolRegistry 通过：

```text
ToolLoader(..., scope="subagent")
```

构造。

目的：

1. 减少无关 Tool；
2. 降低误操作；
3. 防止子任务获得不需要的高权限；
4. 减少 Tool Selection 噪声。

这是一种 Least Privilege，而不是单纯“为了 Prompt 短”。

### 10.2.5 迭代限制的设计思考

旧教程写“主 Agent 40、子 Agent 15”已经过时。

current snapshot：

```text
agents.defaults.maxToolIterations = 200
```

SubagentManager 默认也从当前 AgentDefaults / Runtime Limit 继承。

真正重要的不是某个数字，而是为什么需要上限：

- 防止 Tool Loop；
- 限制成本；
- 防止异常 Provider/Tool 无限重试；
- 给系统一个可解释的 Stop Reason。

### 10.2.6 并发限制

current：

```text
agents.defaults.maxConcurrentSubagents = 4
```

额外任务等待 capacity。

这个限制和：

```text
NANOBOT_MAX_CONCURRENT_REQUESTS
```

不是同一件事：

- 前者限制 Subagent；
- 后者限制 inbound Agent Requests。

### 10.2.7 结果回报机制

主 Session 正在运行时，Subagent result 可以作为 pending input 在 Runner 的 injection boundary 被观察。

current AgentLoop 甚至会在准备退出时等待同 Session 的运行中 Subagent 一段时间，使结果有机会进入当前长 Turn。

### 10.2.8 使用场景

**适合：**

```text
论文 A → Method 分析
论文 B → Evaluation 分析
论文 C → Limitations 分析
主 Agent → 综合
```

**不适合：**

```text
任务本来 1 次 Tool Call 就能做
却 Spawn 5 个 Subagent
```

多 Agent 的收益必须大于额外 Token、延迟与调试成本。

---

## 10.3 定时任务（Cron）系统

### 10.3.1 CronService：current 自有 Scheduler

旧教程写“基于 APScheduler”已经不适用。

current：

```text
nanobot/cron/service.py
```

使用自有 `CronService`，通过 `croniter` 计算 Cron Schedule，并把 Job 持久化到：

```text
<workspace>/cron/jobs.json
```

### 10.3.2 cron 工具的三种典型模式

current Built-in Cron Skill 将常见使用概括为：

1. **Reminder**：到时直接提醒；
2. **Task**：到时让 Agent 执行任务并返回结果；
3. **One-time**：某个确定时间只运行一次。

底层 Schedule 支持：

```text
at
every
cron expression + timezone
```

### 10.3.3 调度配置方式

用户通常直接自然语言要求：

```text
每天 9 点提醒我查看实验
每周一汇总本周任务
30 分钟后提醒我
```

模型通过 `cron` Tool 构造 Schedule。

### 10.3.4 定时任务的执行流程

```text
cron(action=add)
   ↓
CronService
   ↓
jobs.json
   ↓
到期
   ↓
Bound Cron Agent / CronTurnCoordinator
   ↓
origin Session Scheduled Turn
   ↓
AgentLoop
   ↓
执行并向原 Channel/Session 交付结果
```

current-source 会强制 User Cron Job 绑定可路由的 Session Context；不完整的 Legacy Job 会被迁移或禁用，而不是静默乱发消息。

### 10.3.5 Local Trigger

current Automations 还有一种原版教程没有覆盖的重要能力：

```text
Local Trigger
```

用途：

- CI Job 完成；
- 本地脚本生成报告；
- 文件处理完成；
- 外部 Webhook 被你转换成本地命令。

流程：

```text
/trigger <name>
→ 创建 Trigger
→ nanobot trigger <id> "payload"
→ 对应 Session 产生一个 Agent Turn
```

这比用 Cron 轮询某个本地状态更直接。

### 10.3.6 防递归与可靠性

Scheduled Turn 与普通用户输入走不同 automation metadata / coordinator 路径。

设计重点不是“靠 Prompt 告诉模型不要递归”，而是：

- Job 有明确 origin Session；
- Automation Turn 有独立 metadata；
- 相同 Session 仍使用 FIFO admission；
- 系统 Job 和 User Job 有不同 ownership；
- Cron Store 损坏会保留 corrupt backup，避免直接覆盖丢数据。

---

## 10.4 Heartbeat 心跳任务

### 10.4.1 什么是 Heartbeat

current Heartbeat **不是独立旧服务**。

Gateway 启动时，如果：

```text
gateway.heartbeat.enabled = true
```

会注册一个受保护的 System Cron Job。

### 10.4.2 配置方式

current defaults：

```text
gateway.heartbeat.enabled = true
gateway.heartbeat.intervalS = 1800
gateway.heartbeat.keepRecentMessages = 8
```

即默认约每 30 分钟检查一次。

工作清单：

```text
<workspace>/HEARTBEAT.md
```

在：

```markdown
## Active Tasks
- Check ...
```

下放需要周期检查的任务。

### 10.4.3 心跳触发机制

```text
Gateway
  ↓
Protected Heartbeat Cron Job
  ↓
读取 HEARTBEAT.md
  ↓
有 Active Tasks?
  ├─ 否 → silent
  └─ 是 → Agent 执行
            ↓
         Notification Gate
            ↓
        有有用/可行动结果?
        ├─ 否 → silent
        └─ 是 → 最近活跃 Chat Target
```

### 10.4.4 Heartbeat 的使用场景

适合：

- 每隔一段时间检查项目状态；
- 检查“是否有异常/新变化”；
- 没变化就不要通知。

不适合：

- 用户明确要求“每天 9 点一定发一条提醒”；
- 一次性未来事件。

这些更适合 Cron。

### 10.4.5 keepRecentMessages 的作用

Heartbeat 有自己的维护 Session/运行历史。保留有限近期消息可以防止后台检查无限增长，同时给后续检查保留必要上下文。

---

## 10.5 三者的协作关系

### 10.5.1 SubAgent、Cron、Heartbeat 对比

| 机制 | 解决的问题 | 触发方式 | 默认是否总通知 |
|---|---|---|---|
| Subagent | 当前目标中的并行/隔离工作 | 主 Agent Tool Call | 结果回父任务 |
| Cron | 确定时间/周期任务 | 时间 | 通常是 |
| Local Trigger | 外部本地事件 | 显式 trigger command | 作为 Session Turn |
| Heartbeat | 周期检查但无事不扰 | Protected Cron | 否，有 Notification Gate |

### 10.5.2 协作场景示例

ResearchPilot：

```text
Cron：每周一固定做一次 Corpus Report
      ↓
Main Agent
      ↓
Spawn Subagents 并行分析新论文
      ↓
综合结果
      ↓
发送报告

Heartbeat：每 30 分钟检查是否有 Index/Rebuild 异常
      ↓
无异常 → 静默
有异常 → 通知

Local Trigger：Index Build 脚本完成
      ↓
触发 Agent 验证新增论文
```

### 10.5.3 设计模式分析

- Subagent：Task Decomposition / Worker；
- Cron：Persistent Scheduler；
- Local Trigger：Event-driven Integration；
- Heartbeat：Periodic Polling + Notification Gate；
- AgentLoop Session Queue：Serialization / Admission Control。

---

## 10.6 实战练习

### 练习 1：使用 SubAgent 并行处理

让主 Agent：

```text
对 3 篇论文分别分析 Method/Evaluation/Limitations，
每篇独立处理，最后主 Agent 汇总。
```

记录：

- Spawn 数量；
- Running Count；
- 总 Tool Calls；
- Wall-clock Latency；
- 与单 Agent 串行结果对比。

### 练习 2：创建定时任务

创建：

```text
10 分钟后提醒我检查 Nanobot 学习进度
```

然后：

1. `cron(action=list)`；
2. 查看 `cron/jobs.json`；
3. 验证 Job 是否绑定当前 Session；
4. 到期观察 Delivery。

### 练习 3：配置 Heartbeat

在 `HEARTBEAT.md` 添加：

```markdown
## Active Tasks
- Check whether the ResearchPilot index build has failed. Only report failures.
```

实验时可临时缩短 interval。

重点观察：

- 正常状态是否静默；
- 异常是否通知；
- Gateway 停止后 Heartbeat 是否停止。

### 练习 4：Local Trigger

创建 Trigger 后，从脚本：

```bash
nanobot trigger <trigger-id> "Index rebuild completed"
```

观察它如何进入原 Session。

---

## 10.7 面试高频题

### 题目 1：Nanobot 的 SubAgent 系统是怎么设计的？

> "SubagentManager 不再启动完整 AgentLoop，而是复用 AgentRunner/AgentRunSpec，给子任务构造 Focused Prompt 和 Scoped ToolRegistry。它支持 Background Spawn 与 Inline Run，维护 Task Status 和 Session Ownership。current 默认最多并发 4 个 Subagent，并继承统一 Tool Iteration Limit。"

### 题目 2：如何防止 Agent 系统中的递归/爆炸？

> "我会从 Capability Scope、Concurrency、Iteration、Cost 和 Ownership 五层限制。Subagent 只拿需要的 Tool Scope；并发受 maxConcurrentSubagents 控制；每个 Runner 有 maxToolIterations；父子结果有明确 Session/Task ID；再通过 Trace/Eval 判断并行是否真的值得，而不是只靠 Prompt 说‘不要递归’。"

### 题目 3：Cron 和 Heartbeat 有什么区别？

> "Cron 是用户创建的明确 Scheduled Turn，通常每次运行都会回到原 Session；Heartbeat 是 Gateway 管理的 protected System Cron Job，周期读取 HEARTBEAT.md，并通过 Notification Gate 抑制‘没变化’结果。一个强调按时执行，一个强调有事才打扰。"

### 题目 4：如果让你设计一个并行任务系统，你会注意什么？

重点：

- Task Identity；
- Concurrency Limit；
- Timeout/Cancel；
- Side-effect Ordering；
- Result Correlation；
- Parent Failure；
- Retry Idempotency；
- Trace；
- Cost Budget。

---

## 10.8 本章小结

```text
Subagent = 当前任务分解
Cron = 未来时间执行
Local Trigger = 外部事件驱动
Heartbeat = 周期检查 + 无变化静默
```

四者最终都要回到同一件事：

> **把任务正确地纳入 Session、Tool、Delivery 和 Runtime 生命周期，而不是额外开几个异步函数就算完成。**

---

## 下一章

➡️ [11 - 安全与部署](../11-security-deploy-observability/README.md)
