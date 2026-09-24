# Upstream Snapshot — 2026-09-24

本仓库按 **2026-09-24 的 `HKUDS/nanobot` `main`** 组织。


## Stable vs main

截至本快照日期，GitHub Releases 的最新稳定版本是 `v0.3.5`（2026-09-15）。本仓库用于源码学习时以 `main` 为准，因此 UI/命令/源码细节可能领先于稳定 wheel。开始实验前同时记录：

```text
nanobot --version
git rev-parse HEAD   # 如果你使用 editable source checkout
```

不要把 stable package 行为和 current-source 文档混在同一个实验里。

## 已核对的 current-source 事实

### Runtime

核心流：

```text
Channel
→ MessageBus / InboundMessage
→ AgentLoop
→ AgentRunner
↔ Provider
↔ Tools
→ AgentLoop
→ MessageBus / OutboundMessage
→ Channel
```

主要源码：

```text
nanobot/bus/events.py
nanobot/bus/queue.py
nanobot/agent/loop.py
nanobot/agent/runner.py
nanobot/agent/context.py
nanobot/session/manager.py
nanobot/agent/memory.py
nanobot/agent/tools/registry.py
nanobot/agent/tools/mcp.py
nanobot/agent/subagent.py
```

### Config / Workspace / Session

```text
~/.nanobot/config.json
~/.nanobot/workspace/
~/.nanobot/sessions/<workspace-id>/*.jsonl
```

如果 WebUI 选择独立 project workspace：

- agent identity / durable memory 仍属于 configured agent workspace；
- project `AGENTS.md`、相对路径、shell working dir 属于 effective project workspace。

### Memory

```text
Session JSONL                    近期结构化对话
AutoCompact                      空闲后压缩模型上下文，不删完整结构化历史
memory/history.jsonl             consolidation archive，不默认整份塞入 context
SOUL.md                          Dream 管理的 agent personality/style
USER.md                          Dream 管理的 user profile/preferences
memory/MEMORY.md                 Dream 管理的 durable facts
```

旧 `HISTORY.md` 属于 legacy migration 路径，不能再作为新架构主线。

### Skills / Plugins / MCP

- Skills：workspace / plugin / built-in；使用 progressive loading；可 `$skill-name` 显式调用。
- Agent Plugins v1：`<workspace>/plugins/<plugin>/plugin.json`，可包含 `mcp.json` 与 `skills/<name>/SKILL.md`。
- MCP：可直接通过 `tools.mcpServers` 配置，也可打包进 Agent Plugin。
- `MCPProvider` 生命周期由应用 composition root 管理，`AgentLoop` 不自己拥有连接生命周期。

### Concurrency

- 全局 inbound 并发：`NANOBOT_MAX_CONCURRENT_REQUESTS`；未设置/<=0 表示 unlimited。
- Subagent 并发：`agents.defaults.maxConcurrentSubagents`，当前默认 4；超出后等待 capacity。

不要背旧教程中的 `_concurrency_gate(3)`。

### Gateway / Automation

`nanobot gateway` 承载：

- enabled chat channels；
- WebSocket / WebUI；
- workspace-scoped cron；
- Dream system job；
- heartbeat system job；
- health endpoint。

Automation 三种重要形态：

```text
Scheduled automation → cron tool
Local trigger         → /trigger + nanobot trigger
Heartbeat             → HEARTBEAT.md + protected system schedule
```

### Current source installation

- Python >= 3.11
- editable source install 需要 Git + Bun

```powershell
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
nanobot webui
```

### Current user surfaces

```text
nanobot agent -m "Hello!"      # one-shot
nanobot agent                   # terminal session
nanobot webui                   # browser workbench
nanobot gateway                 # long-running runtime
nanobot serve                   # OpenAI-compatible API, after enabling api plugin
Python SDK                      # same agent runtime in-process
```

## Upstream URLs used by this snapshot

- https://github.com/HKUDS/nanobot/blob/main/docs/concepts.md
- https://github.com/HKUDS/nanobot/blob/main/docs/architecture.md
- https://github.com/HKUDS/nanobot/blob/main/docs/quick-start.md
- https://github.com/HKUDS/nanobot/blob/main/docs/configuration.md
- https://github.com/HKUDS/nanobot/blob/main/docs/automations.md
- https://github.com/HKUDS/nanobot/blob/main/docs/deployment.md
- https://github.com/HKUDS/nanobot/blob/main/docs/chat-apps.md
- https://github.com/HKUDS/nanobot/blob/main/docs/python-sdk.md
- https://github.com/HKUDS/nanobot/blob/main/docs/openai-api.md
- https://github.com/HKUDS/nanobot/blob/main/docs/guides/ai-agent-memory.md
- https://github.com/HKUDS/nanobot/blob/main/docs/guides/configure-mcp-tools.md
- https://github.com/HKUDS/nanobot/blob/main/docs/guides/secure-local-ai-agent.md
- https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/loop.py
- https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/runner.py
- https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/memory.py
- https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/tools/mcp.py
- https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/subagent.py

## 学习时发现不一致怎么办

1. 先 `git pull` 更新 upstream checkout；
2. 找官方 `docs/architecture.md` 和 `docs/configuration.md`；
3. 再查实际源码；
4. 最后更新本仓库对应章节；
5. 不要为了保住旧笔记而强行解释新实现。
