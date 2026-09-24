# 11 - 安全与部署

> **阅读时间**：约 2 小时  
> **2026 current-source 说明**：本章直接沿用原版 learn-nanobot 的章节结构与主体内容；凡涉及 Nanobot 具体源码、配置、路径、记忆、并发、MCP 生命周期等实现细节，均按 HKUDS/nanobot main @ 2026-09-24 (source trace snapshot around 62aa6ba6a33790a656b952ef150517bd70d6eb30) 修订。

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

### 11.2.1 restrictToWorkspace：应用层 Workspace Guard

current 配置字段：

~~~text
tools.restrictToWorkspace
~~~

它限制 filesystem/search/shell 等能力的普通作用范围。注意：

> 它是应用层 guard，不等于 OS sandbox。

current 还区分 Agent Workspace 与 effective Project Workspace，并对 built-in/agent skills、exact history path 提供 capability-specific read access，而不是简单把整个 Agent Workspace 放开。

### 11.2.2 Exec Sandbox

current 生产建议同时启用：
- `tools.restrictToWorkspace: true`；
- `tools.exec.sandbox`。

Linux 可使用 bubblewrap（bwrap），macOS 可使用 seatbelt。Sandbox 提供进程级隔离，比只做命令字符串黑名单更可靠。

如果业务不需要 Shell：

~~~text
tools.exec.enable = false
~~~

是最强的最小权限策略。

### 11.2.3 SSRF 防护

current HTTP web fetch 与 HTTP/SSE MCP 都经过 network/SSRF protection：
- 阻止 localhost/private/link-local/internal targets；
- DNS resolution/pinning 防止重绑定；
- redirect 也要重新检查；
- private target 必须通过窄范围 `tools.ssrfWhitelist` 显式授权。

### 11.2.4 Channel Access：allowFrom / Pairing

对 DM-capable Channel，优先使用 pairing 或严格 allowFrom。不要在公网暴露：

~~~text
allowFrom: ["*"]
~~~

同时又给 Agent Shell/Web/File 写权限。

### 11.2.5 最小权限原则

current 可以分成：

~~~text
Channel identity boundary
→ Session policy
→ Tool discovery/scope
→ enabledTools(MCP)
→ Workspace access
→ Exec sandbox
→ Network SSRF guard
→ OS/container user
~~~

安全不是单个“沙箱开关”，而是多层边界。

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

### 11.4.1 为什么用 Docker

原版理由仍成立：
- 依赖隔离；
- 可复现；
- 非 root 用户；
- volume persistence；
- restart policy。

但 current Nanobot 有官方 deployment 文档，应优先基于仓库当前 Dockerfile/compose，而不是复制一份过时的自制镜像。

### 11.4.2 推荐部署思路

~~~text
Host
├── config dir volume
│   ├── config.json
│   ├── sessions/
│   ├── logs/
│   └── runtime data
└── agent workspace volume
    ├── SOUL.md
    ├── USER.md
    ├── memory/
    ├── skills/
    ├── plugins/
    └── cron/
~~~

Project Workspace 如果需要额外挂载，单独设置清楚 read/write 权限。

### 11.4.3 Docker Compose

至少关注：
- 非 root user；
- 只暴露真正需要的端口；
- config/workspace volumes；
- restart policy；
- secrets/env；
- health endpoint；
- Sandbox 所需 Linux capability（如果启用 bwrap，需要按 current docs 配置）。

### 11.4.4 构建与运行

current 长期运行 Surface：

~~~text
nanobot gateway
~~~

Gateway 负责 enabled chat channels、WebUI/WebSocket（按配置）、Cron-backed system jobs、Dream、Heartbeat 和 Health endpoint。

### 11.4.5 环境变量传递

优先：
- secret manager / container secret；
- environment；
- protected config store。

不要把 Provider/API credential bake 到 image layer。

### 11.4.6 数据卷挂载策略

要分清：
- Config/runtime data；
- Agent Workspace；
- Project Workspace；
- 外部 MCP Server data。

这几类数据生命周期不同，不建议全部粗暴挂到一个 `/workspace`。


## 11.5 生产环境配置

### 11.5.1 生产环境 config.json

重点不是复制一个大而全示例，而是采用最小权限：
- 只启用需要的 Provider/Channel/Tool；
- `restrictToWorkspace=true`；
- 需要 Shell 时启用 sandbox；
- MCP 使用 `enabledTools` allowlist；
- `ssrfWhitelist` 只允许窄 CIDR；
- Channel 使用 pairing/allowFrom；
- 设置合理的 request/subagent concurrency；
- Provider timeout/retry 按业务配置。

### 11.5.2 网络暴露

官方 current architecture 区分：
- Health endpoint；
- WebUI/WebSocket；
- API Surface。

默认尽量 bind localhost。若必须通过 Nginx/Caddy 暴露：
- HTTPS；
- auth；
- reverse proxy timeout；
- WebSocket Upgrade；
- rate limiting；
- 只暴露所需 path/port。

### 11.5.3 HTTPS

使用组织现有 TLS termination / reverse proxy 即可。不要因为旧版某些 Channel 需要 平台事件入口 就默认整个 Gateway 必须公网开放。


## 11.6 多实例架构

### 11.6.1 为什么需要多实例

适合：
- 不同部门/租户；
- 不同安全边界；
- 不同 Provider credential；
- 不同 Agent Workspace；
- 不同 Channel account。

### 11.6.2 多实例部署方案

current 官方思路：每个实例使用独立：
- `--config`；
- `--workspace`；
- runtime data dir；
- gateway/channel port（如同机运行）。

不要多个进程共享同一个 Session/Cron/Memory Store，除非源码明确支持并发 ownership。

### 11.6.3 路由

外部 reverse proxy 可以按 hostname/path 路由不同 WebUI/API 实例；Chat Channel 通常由各自 credential/account 自然分流，而不是强行把所有平台 平台事件入口 都路由到一个自定义 endpoint。


## 11.7 日志与监控

### 11.7.1 日志

current `AgentLoop._run_turn_stage()` 会记录 stage/outcome/duration；Turn completion 还可带 provider/model/channel/latency 等字段。

建议生产监控：
- Turn latency；
- Provider error/retry；
- Tool error/timeout；
- Channel send failure；
- MCP connection/reconnect；
- Cron run status；
- Dream/Compaction failure；
- Subagent running/waiting count；
- Session recovery/cancellation。

### 11.7.2 关键指标

Backend + Agent 两层一起看：

~~~text
HTTP/WebSocket/Channel delivery
Session queue depth
Active turns
LLM latency / tokens / cost
Tool latency/error rate
MCP health
Automation lag
Subagent concurrency
Memory/Dream failures
~~~

### 11.7.3 日志安全

current RequestContext/Session Policy 支持 log_content 语义。生产中仍应：
- 不打印 API key/token；
- 不无条件记录完整用户内容；
- Tool result 可能含 secret/PII；
- MCP/HTTP header 要脱敏；
- reasoning/private trace 不应作为普通日志输出。


## 11.8 备份策略

### 11.8.1 需要备份的数据

至少分三类：

**Config/runtime data**
~~~text
config.json
sessions/
automation run records
必要的 OAuth/MCP runtime credential store（按官方路径）
~~~

**Agent Workspace**
~~~text
SOUL.md
USER.md
memory/MEMORY.md
memory/history.jsonl
skills/
plugins/
cron/jobs.json
HEARTBEAT.md
~~~

**Project Workspace**
- 取决于业务；通常应该由项目自身 Git/对象存储策略负责。

### 11.8.2 备份原则

1. Consistent snapshot：避免一边写 Session/Cron 一边直接打 tar；
2. Encryption at rest；
3. Offsite backup；
4. Restore drill；
5. Secret 与普通文档分开；
6. Retention policy；
7. Dream GitStore 只能帮助审计 durable memory，**不等于完整系统备份**。


## 11.9 配置安全清单

### Channel
- [ ] pairing / allowFrom 已收窄
- [ ] 未把公网聊天入口与高权限 Shell 组合暴露
- [ ] Channel credential 不在 Git

### Tool / Files
- [ ] tools.restrictToWorkspace 已启用
- [ ] Shell 非必要则关闭
- [ ] Linux/macOS Shell 使用 current sandbox
- [ ] Project Workspace 权限最小化

### MCP / Network
- [ ] enabledTools 使用 allowlist
- [ ] stdio command/args 已审查
- [ ] HTTP MCP / Web fetch 经过 SSRF guard
- [ ] ssrfWhitelist 只包含必要窄 CIDR
- [ ] OAuth/API credential 不在 command args

### Runtime
- [ ] NANOBOT_MAX_CONCURRENT_REQUESTS 根据资源设定
- [ ] maxConcurrentSubagents 合理
- [ ] Tool/Provider timeout 与 retry 有上限
- [ ] Gateway graceful shutdown 已验证

### Data
- [ ] Session / Memory / Logs 的敏感数据策略明确
- [ ] Backup 加密
- [ ] 已做 Restore drill
- [ ] Dream durable memory 可以 audit/restore


## 11.10 面试高频题

### Q1：你如何设计 Agent 的安全边界？

> “我会分 Channel 身份、Session policy、Tool scope、Workspace、OS sandbox、Network、Credential 七层。Nanobot current-source 中对应 allowFrom/pairing、disabled tools、ToolLoader scope、restrictToWorkspace、exec sandbox、SSRF guard 和 MCP enabledTools。任何一层都不能单独当成完整安全方案。”

### Q2：restrictToWorkspace 与 sandbox 有什么区别？

> “restrictToWorkspace 是应用层路径 guard；sandbox 是进程级 OS 隔离。生产建议两者同时启用。只做路径检查无法阻止 Shell 进程通过别的系统接口逃逸。”

### Q3：HTTP MCP 为什么有 SSRF 风险？

Agent 可以被诱导访问 private/internal URL。需要 DNS/redirect 校验和 allowlist，不能只检查字符串是否以 127.0.0.1 开头。

### Q4：多实例怎么隔离？

每个实例独立 Config、Agent Workspace、Session/runtime data、Port/Channel credential。不要把不同信任域共享到同一 writable workspace。

### Q5：如何做 Agent 可观测性？

至少覆盖：
- Turn stage latency；
- LLM usage/latency；
- Tool trace；
- MCP health；
- Session queue；
- Channel delivery；
- Automation/Subagent；
- Memory/Dream；
并确保日志内容经过隐私/secret policy。

## 11.11 本章小结

### 安全机制总图

```
┌──────────────────────────────────────────────────────┐
│                Nanobot 安全防御体系                    │
│                                                      │
│  ┌─ 代码级硬限制 ──────────────────────────────────┐ │
│  │                                                 │ │
│  │  restrict_to_workspace                          │ │
│  │  ├── 文件操作路径验证（防路径遍历）              │ │
│  │  └── exec 的 cwd 强制设为 workspace             │ │
│  │                                                 │ │
│  │  exec 危险命令检测                               │ │
│  │  ├── 正则匹配危险模式                            │ │
│  │  └── 超时控制                                   │ │
│  │                                                 │ │
│  │  SSRF 防护                                      │ │
│  │  ├── 私有 IP 地址阻止                           │ │
│  │  ├── 云元数据地址阻止                            │ │
│  │  └── 域名白名单（可选）                          │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ 权限控制 ──────────────────────────────────────┐ │
│  │  主Agent: 完整工具集 + 40次迭代                  │ │
│  │  SubAgent: 受限工具集 + current runtime/config limit迭代                 │ │
│  │  Cron上下文: 禁止创建新Cron                      │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ 密钥管理 ──────────────────────────────────────┐ │
│  │  环境变量传入 + .gitignore + 日志脱敏            │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ 运维安全 ──────────────────────────────────────┐ │
│  │  HTTPS + 非root运行 + 资源限制 + 监控告警       │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 面试记忆清单

| 考点 | 一句话回答 |
|------|-----------|
| 核心安全机制 | restrict_to_workspace 限制文件和Shell操作范围 |
| 危险命令 | exec 工具正则检测 rm -rf /、mkfs 等危险模式 |
| SSRF 防护 | web_fetch 阻止私有IP、云元数据地址 |
| 密钥管理 | 环境变量传入，不硬编码，不入库 |
| Docker 部署 | 非root用户 + 资源限制 + 只读挂载配置 |
| 数据持久化 | Docker Volume 挂载 memory/ 和 sessions/ |
| 多实例 | 独立 config/workspace/端口，互不影响 |
| 备份策略 | 定期备份 memory + sessions + config |
| 成本控制 | context_window_tokens + max_tokens + 渐进披露 |
| 设计原则 | 最小权限 + 纵深防御 + 故障安全 |

---

> **下一章**：[12 - Nanobot 实战项目](../12-nanobot-real-projects/README.md) —— 通过实战项目深入掌握 Nanobot 的高级用法