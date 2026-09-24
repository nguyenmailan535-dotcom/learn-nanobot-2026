# 11 - 安全与部署

> **阅读时间**：约 2 小时  
> **前置知识**：[10 - 子Agent与定时任务](../10-subagent-and-cron/README.md)  
> **学习目标**：掌握 Nanobot 的安全机制设计、Docker 部署方案、生产环境最佳实践，为面试中的"部署与安全"类问题做好准备

---

## 目录

- [11.1 为什么安全如此重要](#111-为什么安全如此重要)
- [11.2 Nanobot 安全机制详解](#112-nanobot-安全机制详解)
- [11.3 密钥与敏感信息管理](#113-密钥与敏感信息管理)
- [11.4 Docker 部署](#114-docker-部署)
- [11.5 生产环境配置](#115-生产环境配置)
- [11.6 多实例架构](#116-多实例架构)
- [11.7 日志与监控](#117-日志与监控)
- [11.8 备份策略](#118-备份策略)
- [11.9 配置安全清单](#119-配置安全清单)
- [11.10 面试高频题](#1110-面试高频题)
- [11.11 本章小结](#1111-本章小结)

---

## 11.1 为什么安全如此重要

### 11.1.1 AI Agent 的安全风险

AI Agent 比传统软件面临更多安全风险，因为它**具有自主执行能力**：

```
传统软件：
  用户操作 → 预设逻辑 → 确定性执行
  风险可预测，边界明确

AI Agent：
  用户指令 → LLM 推理 → 自主决策 → 工具执行
  输出不确定，行为边界模糊
```

### 11.1.2 典型攻击场景

| 攻击类型 | 场景 | 风险 |
|---------|------|------|
| **Prompt 注入** | 用户构造恶意指令让 Agent 执行危险操作 | 数据泄露、系统破坏 |
| **路径遍历** | Agent 被引导访问 workspace 外的文件 | 读取 /etc/passwd 等 |
| **命令注入** | 通过 exec 工具执行恶意 Shell 命令 | 系统被接管 |
| **SSRF** | Agent 被引导访问内网服务 | 内网探测、元数据泄露 |
| **密钥泄露** | API Key 被写入日志或记忆文件 | 账号被盗用 |
| **资源耗尽** | 无限循环的工具调用 | 系统崩溃、费用暴增 |

### 11.1.3 安全设计原则

```
最小权限原则 (Least Privilege)
├── Agent 只能访问必需的资源
├── 工具只暴露必需的功能
└── SubAgent 的权限比主Agent更少

纵深防御原则 (Defense in Depth)
├── 多层安全检查
├── 每层都假设其他层可能失败
└── 即使一层被绕过，其他层仍然保护系统

故障安全原则 (Fail-Safe)
├── 出错时拒绝操作（而非放行）
├── 未配置时默认安全
└── 异常情况记录但不暴露细节
```

---

## 11.2 Nanobot 安全机制详解

### 11.2.1 Workspace Access Boundary

current 配置：

```
tools.restrictToWorkspace
```

这是应用层 Workspace Guard。文件 Tool 与 Shell Working Directory 结合 Effective Project Workspace 做路径边界控制。

> 它不是 OS Sandbox，因此不要把“限制路径”与“进程级隔离”混为一谈。

### 11.2.2 Exec Sandbox

current 支持：

```
tools.exec.sandbox
```

- Linux：`bwrap`
- macOS：`seatbelt`
- Windows：继续保持 `restrictToWorkspace`，并谨慎评估 Shell 能力

生产环境可叠加：

```
Application Workspace Guard
+
OS Process Sandbox
```

### 11.2.3 SSRF

Web Fetch 与 HTTP/SSE MCP 走网络安全检查，阻止不安全 Private/Internal Target。

如确需访问可信私网，只使用窄范围：

```
tools.ssrfWhitelist
```

不要全量放开 Private CIDR。

### 11.2.4 Channel Access

current Chat App 还有：

- Pairing
- `channels.*.allowFrom`
- Group Policy
- WebSocket Token / Token Issue Secret

`allowFrom: ["*"]` 等价于明确允许所有可到达该 Channel 的用户，不应作为默认生产配置。

### 11.2.5 MCP / Plugin 最小权限

- MCP `enabledTools` 限制 Server 暴露给 Agent 的 Capability
- Agent Plugin 必须显式 Enable
- Plugin 做 Manifest/Containment/Fingerprint 验证
- stdio MCP command/args/env 属于本地进程执行边界

### 11.2.6 Session / Runtime Policy

Session 可以拥有 disabled tools；AgentLoop 在 restore 阶段构造 Restricted ToolRegistry。权限边界不应只依赖 Prompt。

## 11.3 密钥与敏感信息管理

### 11.3.1 基本原则

```
✅ 正确做法：
├── API Key 通过环境变量传入
├── 密钥文件加入 .gitignore
├── 使用专用的密钥管理服务
└── 定期轮换密钥

❌ 错误做法：
├── API Key 硬编码在 config.json 中并提交到 Git
├── 密钥写在 AGENTS.md 或 MEMORY.md 中
├── 在日志中打印完整密钥
└── 多个服务共用同一个密钥
```

### 11.3.2 环境变量管理

```bash
# 方式一：直接设置环境变量
export OPENAI_API_KEY="sk-xxxxxxxx"
export TELEGRAM_BOT_TOKEN="123456:ABC..."

# 方式二：使用 .env 文件
cat > .env << 'EOF'
OPENAI_API_KEY=sk-xxxxxxxx
TELEGRAM_BOT_TOKEN=123456:ABC...
BRAVE_API_KEY=BSAxxxxxxxx
EOF

# 将 .env 加入 .gitignore
echo ".env" >> .gitignore
```

### 11.3.3 config.json 中引用环境变量

```json
{
  "providers": {
    "openai": {
      "api_key": "${OPENAI_API_KEY}",
      "api_base": "https://api.openai.com/v1"
    }
  },
  "channels": {
    "telegram": {
      "bot_token": "${TELEGRAM_BOT_TOKEN}"
    }
  }
}
```

### 11.3.4 .gitignore 配置

```gitignore
# 密钥文件
.env
*.pem
*.key
credentials.json

# Nanobot 数据
config.json
memory/
sessions/

# 系统文件
__pycache__/
*.pyc
.DS_Store
```

---

## 11.4 Docker 部署

### 11.4.1 current 部署前提

官方 current deployment guide 建议先保证：

```bash
nanobot status
nanobot agent -m "Hello!"
```

本地正常后再部署 Gateway。

### 11.4.2 持久化目录

部署时需要持久化：

- active config directory（含 sessions）
- Agent Workspace（memory、cron、artifacts 等）
- WebUI/media/log runtime data（按当前 config path）

官方 Docker 示例采用挂载 `~/.nanobot` 到容器用户的 Nanobot 数据目录。

### 11.4.3 非 Root 与资源限制

原版“非 root + CPU/Memory 限制 + health check”的原则仍然有效。

### 11.4.4 Docker 中的 Sandbox

如果容器内显式启用 `tools.exec.sandbox: "bwrap"`，需要给 nested namespace/bwrap 相应能力；否则 bwrap 可能直接失败。不要把容器本身与 Nanobot exec sandbox 当成同一层。

---

## 11.5 生产环境配置

### 11.5.1 Gateway

长期运行：

```bash
nanobot gateway
```

Gateway current 会承载：

- enabled Chat Channels
- WebSocket/WebUI（如启用）
- Workspace Cron
- Dream / Heartbeat System Jobs
- Health Endpoint

### 11.5.2 WebUI 与 Health Endpoint

current default：

| Surface | Default |
|---|---|
| Health | `http://127.0.0.1:18790/health` |
| WebUI/WebSocket | `http://127.0.0.1:8765` |

WebUI 由 WebSocket Channel 提供，不是 Health Endpoint。

### 11.5.3 Reverse Proxy

是否需要 Nginx/Public HTTPS 取决于暴露 Surface：

- 只本地使用：不需要公网
- Feishu/WeCom Long Connection：不需要旧版 webhook/ngrok
- Microsoft Teams / Linear OAuth/Webhook 等：可能需要 Public HTTPS
- Remote WebUI/API：需要认证、TLS、最小暴露面

---

## 11.6 多实例架构

current-source 运行多个隔离 Bot 时，应使用不同：

```
--config
--workspace
gateway.port / channel ports
```

而不是仅复制几个 Webhook Path。

每个实例要分别考虑：

- Session Namespace
- Memory Workspace
- Cron Store
- Channel Credential
- Pairing State
- WebUI Port
- Provider Rate Limit

## 11.7 日志与监控

### 11.7.1 日志配置

```python
# Nanobot 日志级别
import logging

# 开发环境
logging.basicConfig(level=logging.DEBUG)

# 生产环境
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nanobot/agent.log'),
        logging.StreamHandler()
    ]
)
```

**日志级别建议**：

| 环境 | 级别 | 说明 |
|------|------|------|
| 开发 | DEBUG | 详细信息，包括工具调用细节 |
| 测试 | INFO | 关键操作和事件 |
| 生产 | WARNING | 警告和错误 |

### 11.7.2 关键监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| API 调用次数 | LLM API 调用频率 | 超出预算 |
| 响应延迟 | 用户消息到回复的时间 | > 30s |
| 错误率 | 工具调用失败比例 | > 5% |
| 内存使用 | 进程内存占用 | > 1.5GB |
| 会话活跃数 | 同时进行的会话数量 | > 100 |
| Token 消耗 | 每小时 token 使用量 | 超出预算 |
| 记忆压缩次数 | MemoryConsolidator 触发频率 | 异常频繁 |

### 11.7.3 日志安全

```python
# 重要：日志中不要记录敏感信息
def safe_log(message: str, data: dict) -> str:
    """安全的日志记录，脱敏敏感信息"""
    safe_data = {}
    for key, value in data.items():
        if key in ("api_key", "token", "secret", "password"):
            safe_data[key] = value[:8] + "***"  # 只显示前8位
        else:
            safe_data[key] = value
    
    return f"{message}: {safe_data}"

# 示例
logger.info(safe_log("Provider config", {
    "provider": "openai",
    "api_key": "sk-abcdefghijklmnop",  # 会被脱敏为 "sk-abcde***"
    "model": "gpt-4o"
}))
```

---

## 11.8 备份策略

### 11.8.1 current-source 需要备份什么

current 默认状态分散在 Config Data Directory 与 Agent Workspace，备份时不要再只打包旧版 `memory/HISTORY.md`。

~~~text
建议备份：
├── <config-dir>/config.json
├── <config-dir>/sessions/<workspace-id>/
├── <agent-workspace>/SOUL.md
├── <agent-workspace>/USER.md
├── <agent-workspace>/AGENTS.md
├── <agent-workspace>/memory/
│   ├── MEMORY.md
│   ├── history.jsonl
│   └── Dream/Git state
├── <agent-workspace>/skills/
├── <agent-workspace>/plugins/
└── <agent-workspace>/cron/
    ├── jobs.json
    └── runs/
~~~

WebUI/media/log 等运行数据是否需要备份，取决于你的恢复目标。

### 11.8.2 为什么 Session 与 Workspace 都要备份

只备份 Workspace：

- Long-term Memory 还在
- 但 Conversation Replay / Provider State / Session Metadata 可能丢失

只备份 Session：

- Conversation 还在
- 但 SOUL/USER/MEMORY/Skills/Plugins/Cron 可能丢失

所以恢复策略要围绕**整个实例状态**设计。

### 11.8.3 备份原则

1. **先确认 active paths**：用 `nanobot status`，不要假设固定路径。
2. **一致性**：运行中的 JSONL/Job Store 最好在受控时点快照。
3. **Secret**：Config Backup 本身包含敏感 Credential 时要加密和限制权限。
4. **恢复演练**：备份成功不等于可恢复，必须在独立目录做 Restore Test。
5. **Dream 可审计**：Durable Memory 的 Git-backed history 也属于有价值的恢复信息。

## 11.9 配置安全清单

### 生产部署前必检

```
[ ] Identity / Access
├── [ ] Channel Pairing / allowFrom 已收紧
├── [ ] Remote WebUI/API 有认证
└── [ ] 不使用不必要的 wildcard access

[ ] Tool Boundary
├── [ ] tools.restrictToWorkspace = true
├── [ ] Shell 不是必须就关闭或严格限制
├── [ ] Linux/macOS 评估 tools.exec.sandbox
├── [ ] MCP enabledTools 最小化
└── [ ] Session disabled tools 符合场景

[ ] Network
├── [ ] SSRF Guard 保持启用
├── [ ] ssrfWhitelist 仅可信窄范围
└── [ ] Remote MCP / Callback 使用 TLS 与认证

[ ] Secret
├── [ ] API Key / Bot Token 不入 Git
├── [ ] 不写 Prompt / Skill / command args
└── [ ] 日志内容策略经过检查

[ ] Runtime
├── [ ] maxToolIterations 合理
├── [ ] maxConcurrentSubagents 合理
├── [ ] NANOBOT_MAX_CONCURRENT_REQUESTS 按资源设置
├── [ ] Session/Memory/Config 持久化
└── [ ] Backup + Restore 做过演练
```

## 11.10 面试高频题

### 题目 1：Prompt Injection 怎么防？

> 不能只靠 System Prompt。要做 Defense in Depth：Workspace Guard、OS Sandbox、Tool Allowlist、MCP enabledTools、SSRF Guard、Channel Pairing、Session Policy 等硬边界。模型被诱导也不能越过宿主权限。

### 题目 2：restrictToWorkspace 是 Sandbox 吗？

> 它是应用层 Path/Workspace Boundary，不等同 OS Sandbox。current 可再用 bwrap/seatbelt 做进程级隔离。

### 题目 3：公开 Chat Bot 最大风险是什么？

> 未授权用户可能间接获得 File/Shell/Web/MCP Tool 能力。因此先做 Pairing/allowFrom，再做最小 Tool 权限和 Workspace/Sandbox 隔离。

### 题目 4：如何部署 current Nanobot？

> 先本地 smoke test，再用 Gateway 作为长期进程；持久化 config/session/workspace；按 Surface 配认证与 TLS；根据是否需要 webhook/long connection 决定是否需要公网入口。

### 题目 5：为什么 Observability 也是安全的一部分？

> 需要知道哪一个 Turn、哪个 Tool、哪个 Channel、哪个 Session 做了什么；current Turn stage timing、typed events、usage/log policy 让异常行为可追踪。

## 11.11 本章小结

### current Security / Deployment 心智模型

~~~text
Untrusted User / Document / MCP Result
        ↓
Channel Access
├── Pairing
└── allowFrom
        ↓
Agent Runtime
├── Session Policy
├── Tool Allowlist / MCP enabledTools
├── max iterations / concurrency / timeout
└── Recovery / Logging
        ↓
Host Boundary
├── tools.restrictToWorkspace
├── tools.exec.sandbox
└── SSRF Guard / ssrfWhitelist
        ↓
Deployment
├── non-root
├── Resource Limits
├── TLS / Auth
├── Persistent Config + Session + Workspace
└── Backup / Restore / Health / Observability
~~~

### 面试记忆清单

| 考点 | current-source 一句话回答 |
|---|---|
| 文件边界 | `tools.restrictToWorkspace` 是应用层 Workspace Guard |
| Shell 隔离 | Linux 可用 bwrap，macOS 可用 seatbelt；与 Workspace Guard 分层 |
| SSRF | Web/MCP HTTP 默认做网络安全检查，私网例外只加窄范围 whitelist |
| Channel 权限 | Pairing / strict allowFrom，避免陌生人间接获得 Tool 能力 |
| MCP 权限 | enabledTools 最小化 |
| Subagent | Iteration/Concurrency 可配置，不背固定“15 次” |
| 部署 | Gateway 是长期运行宿主；按 Surface 决定是否需要公网 HTTPS |
| 持久化 | 同时保护 Config Data、Sessions、Agent Workspace |
| 设计原则 | 最小权限 + 纵深防御 + 故障安全 + 可审计 |

---

> **下一章**：[12 - 定制实战项目](../12-nanobot-real-projects/README.md)
