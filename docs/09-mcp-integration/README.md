# 09 - 多平台接入

> **阅读时间**：约 2 小时  
> **前置知识**：[08 - 技能与工具](../08-skills-tools-plugins/README.md)  
> **学习目标**：沿用原版多平台章节结构，以 **2026-09-24 HKUDS/nanobot main** 为准理解 MessageBus、ChannelManager、Channel Package、Pairing 和 Session 隔离。

---

## 目录

- [9.1 多平台支持概述](#91-多平台支持概述)
- [9.2 MessageBus 架构详解](#92-messagebus-架构详解)
- [9.3 ChannelManager 出站策略](#93-channelmanager-出站策略)
- [9.4 BaseChannel 适配器模式](#94-basechannel-适配器模式)
- [9.5 各平台接入指南](#95-各平台接入指南)
- [9.6 session_key 会话隔离机制](#96-session_key-会话隔离机制)
- [9.7 多平台消息流完整链路](#97-多平台消息流完整链路)
- [9.8 实战练习](#98-实战练习)
- [9.9 面试高频题](#99-面试高频题)
- [9.10 本章小结](#910-本章小结)

---

## 9.1 多平台支持概述

### 9.1.1 为什么需要多平台支持

Agent Core 不应该和某一个聊天 SDK 绑定：

```text
Telegram ─┐
Discord  ─┤
Feishu   ─┤
WeChat   ─┼→ Channel Layer → MessageBus → AgentLoop
WebUI    ─┤
Email    ─┤
...      ─┘
```

多平台支持的核心不是“多写几个 Bot”，而是建立 **Platform Protocol ↔ Unified Runtime Message** 的稳定 Adapter Boundary。

### 9.1.2 支持的平台列表

2026-09-24 current-source 的 Channel Packages 包括代表性的：

| 平台 | current package |
|---|---|
| Telegram | `telegram` |
| Discord | `discord` |
| Slack | `slack` |
| 飞书/Lark | `feishu` |
| 钉钉 | `dingtalk` |
| 微信 | `weixin` |
| 企业微信 | `wecom` |
| WhatsApp | `whatsapp` |
| QQ | `qq` |
| NapCat | `napcat` |
| Matrix | `matrix` |
| Mattermost | `mattermost` |
| Microsoft Teams | `msteams` |
| Signal | `signal` |
| Email | `email` |
| Linear | `linear` |
| MoChat | `mochat` |
| WebUI/WebSocket | `websocket` |

列表会继续变化，因此面试时不要死背“8+ 平台”。

### 9.1.3 核心设计理念

```text
层 1：Agent Core
- 只看 InboundMessage / OutboundMessage / AgentEvent

层 2：MessageBus / TurnDelivery
- 统一消息和 Runtime Event 路由

层 3：Channel Package
- 平台鉴权、接收、发送、Streaming、媒体、Thread

层 4：ChannelManager
- discovery、lifecycle、routing、retry、状态管理
```

---

## 9.2 MessageBus 架构详解

### 9.2.1 不只是“双队列”

原版教程把 MessageBus 描述成 Inbound Queue + Outbound Queue，这个心智模型仍有用，但 current-source 已扩展到：

- Inbound Message；
- Outbound Message；
- Stream Delta / Stream End；
- Reasoning / Progress Event；
- Runtime Model / Goal State Event；
- Channel Delivery。

更准确地说：

```text
MessageBus = Runtime message/event boundary
```

### 9.2.2 InboundMessage 数据结构

源码：

```text
nanobot/bus/events.py
```

核心字段包括 channel、sender_id、chat_id、content、media、metadata、session key/override，以及 user/system 语义。

不要在 Agent Core 中依赖 Telegram Update、Feishu Event 等 SDK 类型。

### 9.2.3 OutboundMessage 数据结构

普通最终回复链路：

```text
AgentRunResult
→ AgentLoop
→ TurnDelivery
→ OutboundMessage / AgentEvent
→ Channel
```

### 9.2.4 MessageBus API

源码学习重点是：

```text
publish inbound
consume inbound
publish outbound / event
channel-side delivery
```

不要把教程里的简化伪类签名当成 current API。

### 9.2.5 为什么用消息边界而不是直接调用

1. Channel/Core 解耦；
2. Channel 可独立 Retry/Recovery；
3. Streaming/Event 可统一路由；
4. AgentLoop 可复用于 CLI/WebUI/Chat Apps；
5. 测试可以替换 Fake Bus / Fake Channel。

---

## 9.3 ChannelManager 出站策略

### 9.3.1 ChannelManager 的职责

current `nanobot/channels/manager.py` 负责：

- Channel package discovery；
- 根据 Config 启用/禁用；
- start/stop lifecycle；
- Outbound routing；
- retry；
- Runtime status；
- 部分 Hot Reload 行为。

### 9.3.2 Streaming 合并与平台差异

不同平台对 Streaming 的能力不同。Channel Adapter 可以做平台特定 buffering/coalescing，但 AgentRunner 不需要知道这些细节。

### 9.3.3 Progress / Tool Hint

Progress、Tool Hint、Reasoning 等属于 Runtime Event。是否展示、怎样展示，由 Channel/UI capability 决定。

### 9.3.4 发送失败与 Retry

current Channel Contract 的重要原则：

> 平台发送失败要向 Manager 抛出异常，而不是只记录日志后假装成功。

因为：

```text
Agent 做完了
≠
用户一定收到了
```

Delivery Reliability 是独立工程问题。

---

## 9.4 BaseChannel 适配器模式

### 9.4.1 Adapter Pattern

```text
Platform Event
    ↓
Channel Adapter
    ↓
InboundMessage

OutboundMessage / AgentEvent
    ↓
Channel Adapter
    ↓
Platform API
```

### 9.4.2 BaseChannel 与 Channel Package

current-source 已经强调 self-contained Channel Package。新增平台优先参考：

```text
docs/channel-package-guide.md
nanobot/channels/plugin.py
nanobot/channels/<channel>/
```

### 9.4.3 Telegram Channel 实现示例

读 Telegram 时只追：

1. SDK Update 在哪里进入；
2. sender/chat/thread 如何映射；
3. InboundMessage 在哪里构造；
4. Outbound/Streaming 怎么发送；
5. allowFrom/pairing 在哪里检查。

### 9.4.4 添加新平台的步骤

1. 创建 Channel Package；
2. 实现 Runtime Adapter；
3. 提供 Config/Validation/Plugin Descriptor；
4. 外部事件转 InboundMessage；
5. 实现 Outbound/Event Delivery；
6. 增加 Access Policy；
7. 增加 Channel Tests；
8. 通过 Gateway 验证 Lifecycle。

---

## 9.5 各平台接入指南

### 9.5.1 Telegram

current 官方 Guide 支持 Pairing。很多 DM-capable Channel 在省略 `allowFrom` 时进入 pairing-only mode：

```text
新用户 DM
→ 收到 Pairing Code
→ WebUI 或 /pairing approve
→ 获得正常访问
```

静态 Allowlist 示例：

```json
{
  "channels": {
    "telegram": {
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

不要在公网 Bot 上随意使用 `"allowFrom": ["*"]`。

### 9.5.2 飞书（Feishu/Lark）

current-source 包含 Feishu connection/runtime 与 WebSocket 支持，因此旧版“必须准备公网 Webhook + ngrok 才能接入飞书”已经不是唯一模式。

学习时以 current `docs/guides/feishu-ai-agent.md` 为准，完成 Credential、事件权限、Connection Setup、Pairing，并由 Gateway 长期运行。

### 9.5.3 钉钉（DingTalk）

重点学习 Credential、Message/Event Translation、sender access policy、Streaming 能力与 reconnect/error handling。

### 9.5.4 Discord

除了 DM access，还要关注 server/channel allowlist、mention policy、thread/session mapping 和 Bot permissions/scopes。

### 9.5.5 其他平台

不建议为了“平台数量”全部配置。本教程至少实际跑：

1. WebUI/CLI；
2. 一个真实 Chat App。

然后从源码比较另一个 Channel 的 Adapter 差异。

### 9.5.6 多平台同时接入

长期多平台运行的宿主：

```bash
nanobot gateway --background
```

Gateway 负责保持 Channels、WebSocket、Automations、Dream、Heartbeat 等在线。

---

## 9.6 session_key 会话隔离机制

### 9.6.1 session_key 的构成

默认情况下，会话身份通常由 Channel + Chat/Thread 等路由信息形成，具体逻辑以 current `session/keys.py` 与 Channel metadata 为准。

不要在业务逻辑里自己硬拼 `channel + ":" + user_id`。

### 9.6.2 session_key 的作用

它影响：

- Session persistence namespace；
- per-session pending queue；
- FIFO worker；
- provider state；
- Tool file-state tracking；
- Model Preset selection；
- Automation routing。

### 9.6.3 session_key_override：线程/子会话隔离

current-source 支持显式 override，也支持：

```text
agents.defaults.unifiedSession
```

Unified Session 适合单用户、多设备/多 Channel 共享 Conversation Context，不适合无脑用于多人 Bot。

### 9.6.4 Project Workspace 不等于 Session Key

WebUI Chat 可以选择 Effective Project Workspace：

```text
Conversation Identity
≠
Project Filesystem Scope
```

这两种状态必须分别管理。

---

## 9.7 多平台消息流完整链路

### 9.7.1 完整消息处理流程

```text
Telegram / Feishu / WebUI
        ↓
Channel Runtime
        ↓
Access Policy / Pairing
        ↓
InboundMessage
        ↓
MessageBus
        ↓
AgentLoop.run()
        ↓
effective session key
        ↓
per-session pending queue / worker
        ↓
Turn Pipeline
        ↓
AgentRunner
        ↓
Tool / Provider
        ↓
AgentRunResult
        ↓
TurnDelivery / MessageBus
        ↓
ChannelManager
        ↓
Platform API
```

### 9.7.2 跨平台场景

不开 Unified Session 时，Telegram Chat、Feishu Chat、WebUI Chat 默认是不同 Conversation State。

开启 Unified Session 后要特别注意：

- Access Control；
- Last Active Delivery Route；
- 多 Channel 同时输入顺序；
- 单用户假设。

---

## 9.8 实战练习

### 练习 1：接入一个真实 Chat App

选择 Telegram / Feishu 任意一个：

1. Gateway 启动；
2. 先走 Pairing；
3. DM Bot；
4. 获取 Pairing Code；
5. Approve；
6. 发一个触发 Tool 的问题；
7. 看 Gateway Log。

### 练习 2：多平台同时接入

WebUI + Chat App 同时使用，观察：

- 是否不同 Session；
- Tool Runtime 是否共享；
- Memory 是否来自同一 Agent Workspace；
- Project Scope 是否一致。

### 练习 3：观察 session 隔离

两个 Channel 分别说不同临时事实，再互相询问；然后开启/关闭 `unifiedSession` 做对比。

---

## 9.9 面试高频题

### 题目 1：如何设计一个支持多平台的 Agent 系统？

> "平台协议限制在 Channel Adapter 层。外部事件转成 InboundMessage，通过 MessageBus 进入 AgentLoop；Agent Core 不依赖具体 SDK。出站消息和 Runtime Event 再由 ChannelManager 路由到具体 Channel。Access Control、Streaming、Media 和 Retry 都按平台能力处理。"

### 题目 2：MessageBus 和直接调用有什么区别？

> "MessageBus 建立异步消息/事件边界，降低 Channel 与 Core 耦合，支持多个入口、Streaming、Retry、Testing 和长期 Gateway。代价是 Ordering、Identity、Delivery Failure 都必须显式管理。"

### 题目 3：如何处理不同平台的消息格式差异？

> "在 Channel Package 内做协议转换，只把平台无关字段与必要 Metadata 放入 InboundMessage，不让 Telegram/Feishu SDK 类型泄漏到 AgentLoop。"

### 题目 4：如何避免公网 Bot 被陌生人调用 Shell/Files？

> "第一层用 Pairing/allowFrom 控制谁能进入；第二层用 Session/Tool Policy 限制能力；第三层用 restrictToWorkspace、Exec Sandbox、SSRF Guard 做 Tool Boundary。身份控制与 Tool Sandbox 不能互相替代。"

---

## 9.10 本章小结

```text
多平台不是“写很多 Bot”
        ↓
Channel Adapter
        ↓
Unified Message/Event Contract
        ↓
MessageBus
        ↓
Agent Runtime
```

必须记住三个 current-source 重点：

1. Channel 是 self-contained package/discovery；
2. Pairing/Allowlist 是生产访问边界；
3. Session Identity 与 Project Workspace Scope 是两个概念。

---

## 下一章

➡️ [10 - 子Agent与定时任务](../10-channels-subagents-automations/README.md)
