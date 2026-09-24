# 11 — Security / Deployment / Observability

## Security 不是部署后的补丁

Agent 能执行 shell、读文件、访问网络、调用 MCP，因此权限本身就是功能设计的一部分。

## Workspace restriction

```json
{
  "tools": {
    "restrictToWorkspace": true,
    "exec": {
      "enable": true,
      "sandbox": "bwrap"
    }
  }
}
```

注意：`restrictToWorkspace` 是 application-level guard，不等价于 OS sandbox。

- Linux：可用 `bwrap`；
- macOS：current 配置支持 `seatbelt`；
- Windows：没有等价的官方同级 shell sandbox 时，要更谨慎地开放 exec。

## Network / SSRF

Web fetch 和 remote HTTP MCP 会遇到 SSRF 风险。不要为了调通内网地址就把 whitelist 放到整个私网段。

## Secrets

API keys / bot tokens / mailbox passwords：

- 优先环境变量；
- 不 commit `config.json` 中的真实 secret；
- 不把 secret 放进 workspace，让 Agent 文件工具能读到。

## Channel safety

- pairing；
- narrow `allowFrom`；
- group 默认 mention-only；
- WebUI/WS/API 非必要不绑定 `0.0.0.0`；
- remote API 暴露时配置 auth。

## Deployment checklist

先保证：

```powershell
nanobot status
nanobot agent -m "Hello"
```

本地正常，再部署：

```text
Gateway
WebUI
Docker / systemd
OpenAI-compatible API
```

需要持久化：

```text
active config directory + sessions/
workspace + workspace-id + memory + cron
```

## Observability

至少记录：

```text
query/session id
selected model
latency
tool started / completed / error
tools used
usage
stop reason
retrieval evidence
final answer
```

current config 还支持 Langfuse 相关环境变量，可作为后续实验，而不是一开始就上复杂 tracing stack。

## Capstone 安全验收

- MCP 是只读还是可写？
- shell 是否必要？
- corpus 是否能越权读其他目录？
- tool timeout 是否明确？
- remote channel 是否有 access control？
- eval 日志是否泄露论文/用户敏感内容？
