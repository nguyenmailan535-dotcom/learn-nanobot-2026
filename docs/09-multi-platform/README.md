# 09 - 多平台接入

> **阅读时间**：约 2 小时  
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

原版这一部分的设计动机仍然成立：Agent Core 不应该绑定某个聊天平台。

### 9.1.2 current Surface / Channel

2026-09-24 current-source 除 CLI/WebUI/API/SDK 外，Chat Apps 当前文档覆盖 Telegram、Discord、WhatsApp、WeChat、Feishu、DingTalk、Slack、Matrix、Email、QQ、Napcat、WeCom、Microsoft Teams、Mochat、Signal、Linear 等能力；具体可用集合随 optional plugin 安装与版本变化。

### 9.1.3 current 设计

```
Platform Event
    ↓
Channel Package
    ↓
InboundMessage
    ↓
MessageBus
    ↓
AgentLoop
    ↓
OutboundMessage / Typed Event
    ↓
ChannelManager
    ↓
Platform
```

Channel 以自包含 package 位于：

```
nanobot/channels/<channel>/
```

由 ChannelManager 负责 discovery/lifecycle/routing。

## 9.2 MessageBus 架构详解

### 9.2.1 双队列架构

MessageBus 是 Nanobot 多平台通信的核心枢纽，采用**双队列设计**：

```
┌──────────────────────────────────────────────────────┐
│                    MessageBus                         │
│                                                      │
│  ┌─────────────────┐    ┌──────────────────────┐    │
│  │  Inbound Queue   │    │  Outbound Queue       │    │
│  │  (入站队列)       │    │  (出站队列)            │    │
│  │                  │    │                       │    │
│  │  Telegram消息 ──→│    │──→ Telegram回复        │    │
│  │  Discord消息  ──→│    │──→ Discord回复         │    │
│  │  飞书消息    ──→ │    │──→ 飞书回复            │    │
│  │  CLI消息     ──→ │    │──→ CLI输出             │    │
│  │                  │    │                       │    │
│  │ consume ─────────┼───→│ Agent处理             │    │
│  │                  │    │ ─────────→ publish    │    │
│  └─────────────────┘    └──────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

### 9.2.2 InboundMessage 数据结构

InboundMessage 表示从任何平台进入的用户消息：

```python
@dataclass
class InboundMessage:
    channel: str        # 来源通道标识，如 "telegram", "discord", "cli"
    sender_id: str      # 发送者 ID（平台内唯一标识）
    chat_id: str        # 会话 ID（群组 ID 或私聊 ID）
    content: str        # 文本内容
    media: list         # 媒体附件（图片、文件等）
    metadata: dict      # 平台特定的元数据
    session_key: str    # 会话键（用于会话隔离）
```

各字段详解：

| 字段 | 说明 | 示例 |
|------|------|------|
| `channel` | 消息来源平台 | `"telegram"`, `"discord"`, `"cli"` |
| `sender_id` | 发送者在该平台的唯一 ID | `"user_123456"` |
| `chat_id` | 会话标识（私聊或群组） | `"chat_789"`, `"group_456"` |
| `content` | 消息文本内容 | `"你好，请帮我查天气"` |
| `media` | 附件列表 | `[{"type": "image", "url": "..."}]` |
| `metadata` | 平台特定数据 | `{"message_id": "123", "reply_to": "456"}` |
| `session_key` | 会话隔离键 | `"telegram:chat_789"` |

### 9.2.3 OutboundMessage 数据结构

OutboundMessage 表示 Agent 要发出的回复消息：

```python
@dataclass
class OutboundMessage:
    channel: str        # 目标通道标识
    chat_id: str        # 目标会话 ID
    content: str        # 回复文本内容
    reply_to: str       # 回复的原消息 ID（可选）
    metadata: dict      # 平台特定的元数据
    media: list         # 媒体附件
```

### 9.2.4 MessageBus API

```python
class MessageBus:
    """异步消息总线"""
    
    def __init__(self):
        self._inbound_queue = asyncio.Queue()
        self._outbound_queue = asyncio.Queue()
    
    # ─── 入站 API ───
    
    async def publish_inbound(self, message: InboundMessage):
        """Channel 将用户消息发布到入站队列"""
        await self._inbound_queue.put(message)
    
    async def consume_inbound(self) -> InboundMessage:
        """Agent 从入站队列消费消息"""
        return await self._inbound_queue.get()
    
    # ─── 出站 API ───
    
    async def publish_outbound(self, message: OutboundMessage):
        """Agent 将回复消息发布到出站队列"""
        await self._outbound_queue.put(message)
    
    async def consume_outbound(self) -> OutboundMessage:
        """Channel 从出站队列消费消息并发送"""
        return await self._outbound_queue.get()
```

### 9.2.5 为什么用队列而不是直接调用

| 对比 | 直接调用 | 队列解耦 |
|------|---------|---------|
| 耦合度 | Agent 直接依赖 Channel | 完全解耦 |
| 并发 | 需要手动管理 | 队列天然支持 |
| 背压 | 无 | 队列满时自动等待 |
| 扩展性 | 添加平台需要修改 Agent | 只需添加 Channel |
| 测试 | 需要 Mock 平台 | 直接操作队列 |

---

## 9.3 ChannelManager 出站策略

### 9.3.1 ChannelManager 的职责

ChannelManager 是 MessageBus 和各 Channel 之间的管理层，负责：

1. 管理所有已注册的 Channel
2. 路由出站消息到正确的 Channel
3. 处理流式输出的合并和优化
4. 处理发送失败的重试

```
Agent ──→ MessageBus.outbound ──→ ChannelManager ──→ Channel.send()
                                       │
                                       ├── 流式合并
                                       ├── 降频优化
                                       ├── 失败重试
                                       └── 路由分发
```

### 9.3.2 _stream_delta 合并（降频优化）

LLM 的流式输出是逐 token 产生的，如果每个 token 都发送一条消息，会导致：

- Telegram/Discord 等平台的 API 限流
- 用户端消息闪烁
- 网络资源浪费

ChannelManager 通过 `_stream_delta` 合并机制优化：

```python
class ChannelManager:
    async def _stream_delta(self, channel: str, chat_id: str,
                           content_delta: str):
        """合并流式输出片段，降低发送频率"""
        key = f"{channel}:{chat_id}"
        
        # 将新片段追加到缓冲区
        if key not in self._buffer:
            self._buffer[key] = ""
        self._buffer[key] += content_delta
        
        # 检查是否应该发送
        now = time.time()
        last_send = self._last_send_time.get(key, 0)
        
        # 降频策略：至少间隔 300ms 才发送一次
        if now - last_send >= 0.3:
            await self._flush_buffer(key)
            self._last_send_time[key] = now
```

```
LLM 输出流：
t0: "你"
t1: "好"
t2: "！"
t3: "我"
t4: "是"
t5: "一"
t6: "个"
t7: "AI"

无降频（8次发送）：    "你" → "好" → "！" → "我" → "是" → "一" → "个" → "AI"

有降频（3次发送）：    "你好！" → "我是一" → "个AI"
                      ↑ 300ms后 ↑ 300ms后  ↑ 结束flush
```

### 9.3.3 _progress / _tool_hint 过滤

当 Agent 正在执行工具调用或内部推理时，会产生进度信息和工具提示。ChannelManager 会根据配置决定是否将这些信息展示给用户：

```python
async def _handle_progress(self, channel: str, chat_id: str,
                          progress_info: str):
    """处理进度信息"""
    channel_config = self._channels[channel]
    
    # 某些平台可能不展示进度（如 Email）
    if channel_config.get("show_progress", True):
        await self._send(channel, chat_id,
                        f"⏳ {progress_info}")

async def _handle_tool_hint(self, channel: str, chat_id: str,
                           tool_name: str):
    """处理工具调用提示"""
    channel_config = self._channels[channel]
    
    if channel_config.get("show_tool_hints", True):
        await self._send(channel, chat_id,
                        f"🔧 正在使用 {tool_name}...")
```

### 9.3.4 发送失败指数退避

当向平台发送消息失败时（网络问题、API 限流等），ChannelManager 使用指数退避策略重试：

```python
async def _send_with_retry(self, channel: str, chat_id: str,
                          content: str, max_retries: int = 5):
    """带指数退避的消息发送"""
    for attempt in range(max_retries):
        try:
            await self._channels[channel].send(chat_id, content)
            return  # 发送成功
        except Exception as e:
            if attempt < max_retries - 1:
                # 指数退避：1s, 2s, 4s, 8s, 16s
                wait_time = 2 ** attempt
                logger.warning(
                    f"Send failed (attempt {attempt + 1}), "
                    f"retrying in {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Send failed after {max_retries} attempts: {e}")
                raise
```

```
重试时间线：
失败 → 等待 1s → 重试
失败 → 等待 2s → 重试
失败 → 等待 4s → 重试
失败 → 等待 8s → 重试
失败 → 等待 16s → 重试
失败 → 放弃，记录错误日志
```

> 💡 **面试要点**：指数退避（Exponential Backoff）是分布式系统中处理瞬时故障的标准策略。配合最大重试次数和可选的抖动（jitter），可以有效避免"雷群效应"（Thundering Herd）。

---

## 9.4 BaseChannel 适配器模式

### 9.4.1 适配器模式（Adapter Pattern）

每个平台的 API 都不一样（Telegram 用 Bot API、Discord 用 Gateway、飞书用 Event API...），但 Nanobot 的 Agent 核心不应该关心这些差异。

BaseChannel 通过**适配器模式**解决这个问题：

```
┌───────────────────────────────────────────────────┐
│                   BaseChannel                      │
│              (统一抽象基类)                         │
│                                                   │
│  async def start()         # 启动通道连接          │
│  async def stop()          # 停止通道连接          │
│  async def send()          # 发送消息到平台        │
│  async def on_message()    # 平台消息转换后发布     │
│                                                   │
└───────────────────────────────────────────────────┘
         ▲           ▲           ▲           ▲
         │           │           │           │
┌────────┴┐  ┌──────┴───┐  ┌───┴────┐  ┌───┴────┐
│Telegram │  │ Discord   │  │ Feishu │  │ CLI    │
│Channel  │  │ Channel   │  │Channel │  │Channel │
└─────────┘  └──────────┘  └────────┘  └────────┘
```

### 9.4.2 BaseChannel 抽象基类

```python
from abc import ABC, abstractmethod

class BaseChannel(ABC):
    """所有平台通道的抽象基类"""
    
    def __init__(self, name: str, config: dict, message_bus: MessageBus):
        self.name = name
        self.config = config
        self.bus = message_bus
    
    @abstractmethod
    async def start(self):
        """启动通道（建立连接、注册 Webhook 等）"""
        pass
    
    @abstractmethod
    async def stop(self):
        """停止通道（断开连接、清理资源）"""
        pass
    
    @abstractmethod
    async def send(self, chat_id: str, content: str,
                  media: list = None):
        """发送消息到该平台"""
        pass
    
    async def on_message(self, platform_message: dict):
        """收到平台消息后，转换为 InboundMessage 并发布"""
        inbound = self._convert_to_inbound(platform_message)
        await self.bus.publish_inbound(inbound)
    
    @abstractmethod
    def _convert_to_inbound(self, platform_message: dict) -> InboundMessage:
        """将平台特定消息格式转换为统一的 InboundMessage"""
        pass
```

### 9.4.3 Telegram Channel 实现示例

```python
class TelegramChannel(BaseChannel):
    """Telegram 平台适配器"""
    
    def __init__(self, config: dict, message_bus: MessageBus):
        super().__init__("telegram", config, message_bus)
        self.bot_token = config["bot_token"]
        self.bot = None
    
    async def start(self):
        """启动 Telegram Bot"""
        from telegram import Bot
        self.bot = Bot(token=self.bot_token)
        # 注册消息处理回调
        # 开始轮询或 Webhook
    
    async def stop(self):
        """停止 Telegram Bot"""
        if self.bot:
            await self.bot.shutdown()
    
    async def send(self, chat_id: str, content: str,
                  media: list = None):
        """发送消息到 Telegram"""
        if media:
            for item in media:
                if item["type"] == "image":
                    await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=item["url"]
                    )
        
        if content:
            await self.bot.send_message(
                chat_id=chat_id,
                text=content,
                parse_mode="Markdown"
            )
    
    def _convert_to_inbound(self, update: dict) -> InboundMessage:
        """将 Telegram Update 转换为 InboundMessage"""
        message = update.get("message", {})
        return InboundMessage(
            channel="telegram",
            sender_id=str(message["from"]["id"]),
            chat_id=str(message["chat"]["id"]),
            content=message.get("text", ""),
            media=self._extract_media(message),
            metadata={
                "message_id": message["message_id"],
                "username": message["from"].get("username"),
            },
            session_key=f"telegram:{message['chat']['id']}"
        )
```

### 9.4.4 添加新平台的步骤

如果你要为 Nanobot 添加一个新平台（比如 Line），只需：

```python
# 1. 创建 Channel 类，继承 BaseChannel
class LineChannel(BaseChannel):
    def __init__(self, config, message_bus):
        super().__init__("line", config, message_bus)
    
    async def start(self):
        # 初始化 Line SDK，注册 Webhook
        pass
    
    async def stop(self):
        # 清理资源
        pass
    
    async def send(self, chat_id, content, media=None):
        # 调用 Line Messaging API 发送消息
        pass
    
    def _convert_to_inbound(self, event):
        # 将 Line Event 转换为 InboundMessage
        pass

# 2. 在 config.json 中添加配置
# {
#   "channels": {
#     "line": {
#       "channel_access_token": "xxx",
#       "channel_secret": "xxx"
#     }
#   }
# }

# 3. 注册到 ChannelManager
```

> 💡 **面试要点**：这种"面向接口编程"的适配器模式是设计模式的经典应用。添加新平台不需要修改 Agent 核心代码，符合**开闭原则**（对扩展开放，对修改关闭）。

---

## 9.5 各平台接入指南

### 9.5.1 推荐方式：WebUI

current 官方推荐本地普通用户：

1. `nanobot webui`
2. Settings → Channels
3. 选择平台
4. 按引导填 Credential / QR Login
5. 如缺 optional channel support，让本地 WebUI/CLI 安装
6. Restart Gateway
7. 先发 Private DM
8. 如收到 pairing code，在 WebUI 批准

### 9.5.2 CLI 状态与 Gateway

```powershell
nanobot channels status
nanobot gateway --verbose
```

Chat App 必须由 Gateway 长期运行。

### 9.5.3 Optional Channel Plugin

current-source 可使用：

```bash
nanobot plugins enable <channel>
nanobot plugins disable <channel>
```

例如：

```
telegram
feishu
weixin
wecom
qq
...
```

### 9.5.4 Pairing / allowFrom

对支持 DM Pairing 的 Channel，默认应保持访问范围收紧。

```
allowFrom: ["*"]
```

意味着绕过 Pairing，让任何能访问该 Channel 的用户都可与 Bot 对话，只有在明确需要 public access 时才使用。

### 9.5.5 Feishu current-source

Feishu 使用 **WebSocket Long Connection**，默认不需要公网 IP/ngrok。

快速方式：

```bash
nanobot plugins enable feishu
nanobot channels login feishu
nanobot gateway
```

也可手工配置 App ID/App Secret。

Streaming Reply 需要相应 CardKit Permission；如果没有，可以在 Channel Config 关闭 streaming。

### 9.5.6 WeChat / WhatsApp / WeCom

current docs 对部分平台提供 QR Login 或 Long Connection：

- WhatsApp：`nanobot channels login whatsapp`
- WeChat：`nanobot channels login weixin`
- WeCom：WebSocket Long Connection

因此“所有 Chat App 都需要 Webhook + 公网服务器”已经不成立。

### 9.5.7 需要公网 HTTPS 的平台

某些平台/集成（例如 current Microsoft Teams MVP、Linear OAuth/Webhook）仍可能需要 Public HTTPS Callback。应按具体 Channel Guide，而不是套用统一 ngrok 教程。

## 9.6 session_key 会话隔离机制

### 9.6.1 session_key 的构成

session_key 用于唯一标识一个"对话上下文"：

```python
session_key = f"{channel}:{chat_id}"
```

示例：

| 场景 | session_key | 说明 |
|------|-------------|------|
| CLI 默认 | `cli:default` | 命令行交互默认会话 |
| Telegram 私聊 | `telegram:123456` | 用户 ID 为 123456 |
| Telegram 群组 | `telegram:-100789` | 群组 ID |
| Discord 频道 | `discord:guild_1:chan_2` | 服务器1的频道2 |
| 飞书私聊 | `feishu:ou_xxx` | 飞书用户 |

### 9.6.2 session_key 的作用

```
session_key 决定了：

1. 会话历史隔离
   session_key → sessions/<session_key>.jsonl
   不同 key 的用户拥有独立的对话历史

2. 记忆隔离
   每个 session_key 独立的短期记忆
   但 MEMORY.md 是全局共享的

3. 流式输出路由
   Agent 生成的回复按 session_key 路由到正确的平台/会话
```

### 9.6.3 session_key_override：线程/子会话隔离

某些平台支持"线程"或"回复链"功能（如 Discord 线程、Slack 线程）。Nanobot 通过 `session_key_override` 实现线程级别的会话隔离：

```python
def build_session_key(message: InboundMessage) -> str:
    """构建 session_key，支持线程覆盖"""
    base_key = f"{message.channel}:{message.chat_id}"
    
    # 如果消息包含线程信息，使用线程级隔离
    thread_id = message.metadata.get("thread_id")
    if thread_id:
        return f"{base_key}:thread_{thread_id}"
    
    # 如果有显式的 session_key_override
    override = message.metadata.get("session_key_override")
    if override:
        return override
    
    return base_key
```

```
会话隔离层次：

├── telegram:123456          # Telegram 用户 123456 的主会话
│
├── discord:guild_1:chan_2   # Discord 频道的主会话
│   ├── discord:guild_1:chan_2:thread_100  # 线程 100
│   └── discord:guild_1:chan_2:thread_200  # 线程 200
│       （线程内的对话上下文独立于主频道）
│
└── feishu:ou_xxx            # 飞书用户的会话
```

> 💡 **面试要点**：session_key 的设计体现了"多租户隔离"的思想。每个 session_key 对应独立的会话状态，就像 SaaS 系统中每个租户有独立的数据。线程级覆盖是进一步的细粒度隔离。

---

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

### 练习 1：接入一个 Private Channel

推荐 Telegram 或 Feishu：

1. Enable Channel Plugin
2. 配置 Credential / Login
3. `nanobot channels status`
4. `nanobot gateway --verbose`
5. 发 Private DM
6. 测试 Pairing

### 练习 2：两个 Channel 的 Session 隔离

分别在两个平台对话，观察：

```
<config-dir>/sessions/<workspace-id>/
```

验证不同 session key 的 History/Metadata 不互相污染。

### 练习 3：Delivery Failure

故意停止某个 Channel transport，观察：

- ChannelManager retry
- Outbound delivery failure
- Core Turn 是否已经完成

理解“模型成功回答”和“平台成功送达”是两个不同阶段。

## 9.9 面试高频题

### 题目 1：如何设计多平台 Agent？

> 使用 Channel Adapter 将平台事件统一转换为 InboundMessage/OutboundMessage，Core 只依赖 MessageBus；ChannelManager 管发现、生命周期、Retry 和 Wire Projection。

### 题目 2：为什么 MessageBus 而不是 Channel 直接调用 Agent？

> 解耦 transport 与 Core，允许 CLI/WebUI/Telegram/Feishu 共享同一 Session/Runtime，同时让 local typed event 与网络发送分离。

### 题目 3：Feishu current-source 还需要 ngrok 吗？

> 默认 Long Connection 不需要公网 IP。只有具体平台采用 Webhook/OAuth Callback 时才需要 public HTTPS。

### 题目 4：如何避免公开 Channel 让陌生人获得 Shell/File Tool？

> Pairing / strict allowFrom + Workspace Guard + Exec Sandbox + 最小 Tool Set，多层 Defense in Depth。

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