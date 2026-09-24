# 09 - 多平台接入

> **阅读时间**：约 2 小时  
> **2026 current-source 说明**：本章直接沿用原版 learn-nanobot 的章节结构与主体内容；凡涉及 Nanobot 具体源码、配置、路径、记忆、并发、MCP 生命周期等实现细节，均按 HKUDS/nanobot main @ 2026-09-24 (source trace snapshot around 62aa6ba6a33790a656b952ef150517bd70d6eb30) 修订。

> **前置知识**：[08 - 技能与工具](../08-skills-and-tools/README.md)  
> **学习目标**：理解 Nanobot 的 MessageBus 架构、ChannelManager 策略、BaseChannel 适配器模式，掌握多平台接入方法

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

原版观点仍成立：真实 Agent 不应该只存在于某个 Demo 页面，它往往需要接入用户已经在使用的聊天入口、WebUI 或 API。

current-source 进一步把这些 Surface 分为：

~~~text
CLI / TUI
WebUI / WebSocket
Chat Channels
OpenAI-compatible API
Python SDK
~~~

### 9.1.2 支持的平台列表

Channel 列表会持续变化，本仓库不再硬编码“8+”之类固定数量。以 current：

~~~text
nanobot/channels/
~~~

和官方 Channels 文档为准。

当前源码已经采用 self-contained Channel Package/Discovery 机制，因此新增/下线一个平台不需要修改 Agent Core。

### 9.1.3 核心设计理念

~~~text
Platform-specific Event
        ↓
Channel Runtime
        ↓
InboundMessage
        ↓
MessageBus
        ↓
AgentLoop / Session
        ↓
Outbound / Stream Events
        ↓
ChannelManager
        ↓
Platform API
~~~

核心仍然是 Adapter + Message Bus：模型执行层不依赖具体聊天 SDK。


## 9.2 MessageBus 架构详解

### 9.2.1 事件总线边界

原版“双队列”帮助理解 transport/core 解耦，但 current MessageBus 还承载 runtime event publication；不要把它只记成两个 Queue。

### 9.2.2 InboundMessage 数据结构

核心字段仍包括：
- channel；
- sender_id；
- chat_id；
- content；
- media；
- metadata；
- session key / override；
- user/system input 语义。

不同 Channel 的 thread/topic/project 信息可以进入 metadata，而不是污染 AgentRunner。

### 9.2.3 OutboundMessage 数据结构

OutboundMessage 负责用户可见最终消息；Streaming、Progress、Tool Hint、Turn state 等还有 typed event。

### 9.2.4 MessageBus API

理解四类动作即可：
1. Channel 发布 inbound；
2. AgentLoop 消费 inbound；
3. Runtime 发布 output/state event；
4. ChannelManager 路由到具体 Channel。

### 9.2.5 为什么用队列/事件而不是直接调用

- 隔离平台 SDK 与 Agent Core；
- 支持 streaming / progress；
- 支持后台 Automation / Subagent；
- 方便统一 retry / delivery；
- 测试时可用 fake bus 驱动 Core。


## 9.3 ChannelManager 出站策略

### 9.3.1 ChannelManager 的职责

current `nanobot/channels/manager.py` 负责：
- 发现/实例化 enabled Channel packages；
- 生命周期 start/stop；
- outbound dispatch；
- send retry；
- runtime status；
- streaming/reasoning/progress event routing；
- hot reload 相关状态处理。

### 9.3.2 Stream 事件处理

current Channel 可以按自身平台能力处理 stream delta/card update 等。不要假设所有平台都逐 token 推送；ChannelManager/Channel 会做平台适配和合并。

### 9.3.3 Progress / Tool Hint

Progress、Tool Hint 等 typed event 与普通最终文本不同，Channel 可以选择支持、过滤或降级展示。

### 9.3.4 发送失败与重试

current contract 要求 Channel `send()` 在真正无法投递时抛出异常，而不是“打日志后假装成功”，让 ChannelManager 有机会应用共享 retry policy。


## 9.4 BaseChannel 适配器模式

### 9.4.1 Adapter Pattern

不同平台差异：

~~~text
Telegram Update
Discord Event
Feishu Event
WeCom WebSocket Frame
...
~~~

统一为：

~~~text
InboundMessage / OutboundMessage
~~~

### 9.4.2 BaseChannel 抽象基类

BaseChannel 定义生命周期、send、access/pairing 等通用 contract；平台-specific 逻辑放在各自 package 中。

### 9.4.3 Telegram Channel 实现示例

重点不要背 SDK API，而要观察：
1. receive/update queue；
2. sender/chat/thread metadata；
3. media download；
4. InboundMessage 构造；
5. outbound send/retry；
6. allowFrom/pairing policy。

### 9.4.4 添加新平台的步骤

current 推荐使用 self-contained Channel Package：
1. 在 `nanobot/channels/<channel>/` 实现 package；
2. 导出 ChannelPlugin descriptor；
3. 定义 config schema/setup surface；
4. runtime 继承/遵循 BaseChannel；
5. 写 lifecycle/message/retry tests；
6. 让 ChannelManager discovery 自动发现。

不要再按旧版“修改一个中央 ChannelManager 注册表”作为唯一方式。


## 9.5 各平台接入指南

> 平台控制台和 SDK 经常变化。本节保留原版“逐平台接入”的结构，但只写 current 稳定原则；具体按钮/字段以 Nanobot current Channel 文档和平台官方控制台为准。

### 9.5.1 Telegram 接入

典型步骤：
1. 创建 Bot / 获取 Token；
2. 在 WebUI Settings 或 `config.json` 启用 Telegram Channel；
3. 配置 allowFrom / pairing；
4. 启动 `nanobot gateway`；
5. 用真实消息验证 inbound + outbound。

### 9.5.2 飞书（Feishu/Lark）接入

**旧教程“必须公网 平台连接/事件入口 + current long-connection / gateway setup”已经不再是 current 唯一路径。**

current Feishu package 支持更现代的连接/setup 流程，包括长连接相关实现。优先按 WebUI/官方 current Feishu Channel Guide 完成连接，而不是先搭反向代理。

学习源码时重点看：

~~~text
nanobot/channels/feishu/
├── connect.py
├── runtime...
└── websocket...
~~~

### 9.5.3 钉钉等平台

如果 current repo 仍提供对应 package，就按 package config schema 启用；若 current main 已移除/重构某平台，不要因为旧教程列过它就假设仍存在。

### 9.5.4 Discord

同样按 current package/config 运行，重点验证 thread/guild/chat metadata 如何映射到 Session。

### 9.5.5 其他平台

current Channel package 可能包含 WeCom、Weixin、WhatsApp、Matrix、Slack 等不同实现。平台数量不是面试重点，**统一消息模型和 lifecycle contract** 才是。

### 9.5.6 多平台同时接入

Gateway 可以同时启动多个 enabled Channels。不同平台消息统一进入 MessageBus，但默认 Session identity 通常仍按 Channel/Chat 维度隔离；只有显式 unified session / override 才会改变这一语义。


## 9.6 session_key 会话隔离机制

### 9.6.1 session_key 的构成

默认 User Turn 通常由 Channel + Chat/Topic 语义形成 Session Key，具体 Channel 可以通过 metadata/override 提供 thread/topic 级隔离。

### 9.6.2 session_key 的作用

Session Key 决定：
- SessionManager namespace；
- per-session pending queue / lock；
- provider state；
- model preset；
- runtime checkpoint；
- route metadata；
- Subagent/Automation ownership。

### 9.6.3 unified session / override

current-source 支持 unified session 和 explicit session key override。它们是产品语义，不应该由 AgentRunner 自己判断。

另外 Session 文件默认位于：

~~~text
<config-dir>/sessions/<workspace-id>/
~~~

不是直接把冒号形式的 key 当文件名放在 Project Workspace。

## 9.7 多平台消息流完整链路

### 9.7.1 完整消息处理流程

以 Telegram 用户发送消息为例：

```
Step 1: 用户在 Telegram 发送 "帮我查天气"
            │
            ▼
Step 2: Telegram API 推送 Update 到 Bot
            │
            ▼
Step 3: TelegramChannel.on_message()
        ├── 解析 Telegram Update 格式
        ├── 构建 InboundMessage:
        │     channel: "telegram"
        │     sender_id: "123456"
        │     chat_id: "123456"
        │     content: "帮我查天气"
        │     session_key: "telegram:123456"
        └── 发布到 MessageBus Inbound Queue
            │
            ▼
Step 4: Agent 从 Inbound Queue 消费消息
        ├── 加载 session "telegram:123456" 的历史
        ├── 加载 MEMORY.md
        ├── 构建完整 Prompt
        └── 调用 LLM API
            │
            ▼
Step 5: LLM 返回工具调用 → Agent 执行
        ├── 调用 web_search("北京天气")
        ├── 获取搜索结果
        └── LLM 基于结果生成回复
            │
            ▼
Step 6: Agent 创建 OutboundMessage
        ├── channel: "telegram"
        ├── chat_id: "123456"
        ├── content: "北京今天晴，气温 25°C..."
        └── 发布到 MessageBus Outbound Queue
            │
            ▼
Step 7: ChannelManager 从 Outbound Queue 消费
        ├── 路由到 TelegramChannel
        ├── _stream_delta 合并（如果是流式输出）
        └── 调用 TelegramChannel.send()
            │
            ▼
Step 8: TelegramChannel.send()
        ├── 调用 Telegram Bot API
        └── 用户在 Telegram 看到回复
```

### 9.7.2 跨平台场景

同一个 Agent 可以同时处理来自不同平台的消息：

```
时间线：
t=0s  Telegram用户A: "你好"
t=1s  Discord用户B: "帮我写代码"
t=2s  Agent 处理 A 的消息
t=3s  Agent 处理 B 的消息
t=4s  回复发送到 Telegram（给A）
t=5s  回复发送到 Discord（给B）

关键：A 和 B 的会话完全独立
session_key_A = "telegram:user_A"
session_key_B = "discord:guild_1:user_B"
```

---


## 9.8 实战练习

### 练习 1：接入一个平台

优先选 Telegram 或你方便使用的 current Channel：
1. 配置 credential；
2. 收窄 allowFrom/pairing；
3. 启动 `nanobot gateway --verbose`；
4. 发送文本 + 一条媒体消息；
5. 查日志中的 InboundMessage/session key。

### 练习 2：多平台同时接入

同时启用两个 Channel，验证：
- ChannelManager 都启动；
- 两边都能投递；
- Tool/Memory Core 共享；
- Session 默认隔离。

### 练习 3：观察 Session 隔离

不要只“找一个 sessions 目录看文件名”。用 `nanobot status` 找 current config/data path，再对比：
- Platform A Chat；
- Platform B Chat；
- WebUI Topic；
- unified session 开/关。

### 练习 4：模拟 Delivery Failure

让一个 Channel 临时断网或提供 fake send error，观察 ChannelManager retry/failure event。这个实验更能体现后端/Agent 工程价值。

## 9.9 面试高频题

### 题目 1：如何设计一个支持多平台的 Agent 系统？

> **参考回答**：
>
> "我会采用 Nanobot 的架构思路，核心是**三层解耦设计**：
>
> **第一层是 Agent 核心**，只处理业务逻辑——接收统一格式的消息、调用 LLM、执行工具、生成回复。它完全不知道消息来自哪个平台。
>
> **第二层是 MessageBus 消息总线**，采用双队列架构——Inbound Queue 收集所有平台的入站消息，Outbound Queue 收集 Agent 的出站回复。队列实现生产者/消费者解耦，天然支持异步和背压。
>
> **第三层是 Channel 适配器**，每个平台一个 Channel 实现，继承统一的 BaseChannel 抽象类。Channel 负责两件事：一是将平台特定的消息格式转换为统一的 InboundMessage，二是将 OutboundMessage 转换为平台特定的 API 调用。
>
> 添加新平台只需实现一个新的 Channel 类，不需要修改 Agent 和 MessageBus 代码，符合开闭原则。
>
> 会话隔离通过 `session_key`（格式 `{channel}:{chat_id}`）实现，每个 session_key 对应独立的对话历史和状态。
>
> 出站优化方面，ChannelManager 负责流式输出的降频合并（避免平台 API 限流）和发送失败的指数退避重试。"

### 题目 2：MessageBus 和直接调用有什么区别？

> **参考回答**：
>
> "直接调用意味着 Agent 直接引用并调用 Channel 的发送方法，这会导致紧耦合——Agent 需要知道所有平台的存在。每添加一个平台都要修改 Agent 代码。
>
> MessageBus 通过异步队列解耦了生产者和消费者。Channel 往 Inbound Queue 里放消息，Agent 从 Inbound Queue 取消息；Agent 往 Outbound Queue 里放回复，ChannelManager 从 Outbound Queue 取出后路由到对应 Channel。双方通过数据结构（InboundMessage/OutboundMessage）交互，互不依赖。
>
> 这种设计还带来了背压控制——如果 Agent 处理不过来，消息会在队列里排队，不会丢失。在测试时也更方便，可以直接向队列注入消息而不需要启动真实的平台连接。"

### 题目 3：如何处理不同平台的消息格式差异？

> **参考回答**：
>
> "通过适配器模式。定义一个统一的消息结构——InboundMessage 包含 channel、sender_id、chat_id、content、media、metadata 等字段。每个平台的 Channel 实现一个 `_convert_to_inbound` 方法，负责将平台特定格式（如 Telegram 的 Update、Discord 的 Message Event）映射到统一格式。
>
> 出站同理，OutboundMessage 是统一格式，Channel 的 send 方法负责转换为平台 API 调用。
>
> 对于平台特有的功能（如 Telegram 的 Inline Keyboard、Discord 的 Embed），可以放在 metadata 字段中传递，Channel 在发送时识别并使用。"

---

## 9.10 本章小结

### 核心架构图

```
┌──────────────────────────────────────────────────────────┐
│                   Nanobot 多平台架构                      │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │Telegram  │ │Discord   │ │Feishu    │ │DingTalk  │   │
│  │Channel   │ │Channel   │ │Channel   │ │Channel   │   │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘   │
│        │            │            │            │         │
│        └──────┬─────┴──────┬─────┴──────┬─────┘         │
│               │            │            │               │
│        ┌──────▼────────────▼────────────▼──────┐        │
│        │           MessageBus                   │        │
│        │  ┌──────────┐    ┌──────────────┐     │        │
│        │  │ Inbound  │    │ Outbound     │     │        │
│        │  │ Queue    │    │ Queue        │     │        │
│        │  └─────┬────┘    └──────▲───────┘     │        │
│        └────────┼───────────────┼──────────────┘        │
│                 │               │                       │
│        ┌────────▼───────────────┴──────────┐            │
│        │         Agent Core                │            │
│        │  ┌─────┐ ┌──────┐ ┌───────────┐  │            │
│        │  │ LLM │ │Tools │ │ Memory    │  │            │
│        │  └─────┘ └──────┘ └───────────┘  │            │
│        └───────────────────────────────────┘            │
│                                                          │
│  session_key = "{channel}:{chat_id}"                     │
│  每个 session_key 独立的对话历史和状态                      │
└──────────────────────────────────────────────────────────┘
```

### 面试记忆清单

| 考点 | 一句话回答 |
|------|-----------|
| 架构设计 | 三层解耦：Agent核心 + MessageBus + Channel适配器 |
| MessageBus | 异步双队列（Inbound + Outbound），解耦生产者/消费者 |
| InboundMessage | 统一入站消息：channel, sender_id, chat_id, content, media, metadata |
| OutboundMessage | 统一出站消息：channel, chat_id, content, reply_to, media |
| BaseChannel | 抽象基类，每个平台实现一个适配器（适配器模式） |
| session_key | `{channel}:{chat_id}`，实现会话隔离 |
| 流式优化 | _stream_delta 降频合并，间隔 300ms |
| 失败重试 | 指数退避：1s, 2s, 4s, 8s, 16s |
| 添加新平台 | 只需实现 BaseChannel 子类，开闭原则 |

---

> **下一章**：[10 - 子Agent与定时任务](../10-subagent-and-cron/README.md) —— 深入理解 SubAgent 后台任务和 Cron 定时调度