# 05 — MCP：协议、框架集成与安全边界

## 先区分 Function Calling 与 MCP

Function Calling 解决：

> 模型如何用结构化参数请求宿主执行一个工具？

MCP 解决：

> Agent host 如何用统一协议发现并调用外部 capability server？

两者可以同时存在：MCP tool 最终仍会以模型可理解的工具 schema 出现在 provider/tool loop 里。

## Nanobot 的 current-source MCP 心智模型

```text
Apps / config
→ MCP server config
→ application composition root
→ MCPProvider.connect()
→ tools wrapped/registered into shared ToolRegistry
→ AgentRunner calls tool
→ shutdown → MCPProvider.aclose()
```

关键点：**connection lifecycle application-owned**。

## 支持的使用形态

- local stdio；
- remote HTTP；
- remote SSE；
- OAuth（通过当前 Apps/WebUI 流程）；
- `enabledTools` 做最小权限暴露。

## 当前配置思路

```json
{
  "tools": {
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/safe/path"],
        "enabledTools": ["read_file"]
      }
    }
  }
}
```

注意这只是 partial config snippet。

## 你真正要会的面试点

- MCP server 与本地 Python tool 的 trade-off；
- stdio vs remote transport；
- server discovery 与 tool exposure；
- 为什么 `enabledTools` 是安全能力；
- why lifecycle belongs to composition root；
- tool schema 变化如何影响 model behavior；
- timeout / OAuth / untrusted server 风险。

## 实验

本章不自己实现 server。先接一个只读 filesystem MCP，限制到一个测试目录，并只暴露 read tool。

验收：能指出“MCP connected”之后 tool 是在哪里进入 Nanobot ToolRegistry 的。
