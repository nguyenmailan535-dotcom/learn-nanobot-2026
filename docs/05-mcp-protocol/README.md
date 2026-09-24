# 05 - MCP 协议与 Nanobot 集成：从 M×N 问题到 MCPProvider 生命周期

> 🎯 **本章目标**：真正理解 MCP 解决什么问题、Host/Client/Server 如何协作、Transport 与 Tool Schema 的关系，并能从 current-source 解释 Nanobot 为什么把 MCPProvider 放在应用组合层而不是 AgentLoop 内部。

---

## 目录

- [5.1 为什么需要 MCP](#51-为什么需要-mcp)
- [5.2 MCP 要解决的 M×N 问题](#52-mcp-要解决的-mn-问题)
- [5.3 Host、Client、Server 三个角色](#53-hostclientserver-三个角色)
- [5.4 MCP 的核心能力](#54-mcp-的核心能力)
- [5.5 Tool Calling、MCP、Skill、Plugin 的区别](#55-tool-callingmcpskillplugin-的区别)
- [5.6 Transport：stdio、HTTP、SSE](#56-transportstdiohttpsse)
- [5.7 Nanobot current-source 的 MCP 架构](#57-nanobot-current-source-的-mcp-架构)
- [5.8 MCPProvider 源码解读](#58-mcpprovider-源码解读)
- [5.9 enabledTools：不是 UI 开关，而是权限边界](#59-enabledtools不是-ui-开关而是权限边界)
- [5.10 Agent Plugin 与 MCP](#510-agent-plugin-与-mcp)
- [5.11 MCP 的安全风险](#511-mcp-的安全风险)
- [5.12 最小实验](#512-最小实验)
- [5.13 面试高频题](#513-面试高频题)
- [5.14 本章总结](#514-本章总结)

---

## 5.1 为什么需要 MCP

假设你有三个 Agent Host：

~~~text
ChatGPT-like Agent
IDE Agent
Research Agent
~~~

又有四个外部系统：

~~~text
GitHub
Filesystem
PostgreSQL
Browser
~~~

没有统一协议时，开发者很容易写成：

~~~text
Host A ↔ GitHub Adapter
Host A ↔ Filesystem Adapter
Host A ↔ PostgreSQL Adapter
...

Host B ↔ GitHub Adapter
Host B ↔ Filesystem Adapter
...
~~~

每一个 Host 都要理解每一个外部系统的：

- 连接方式；
- Tool Schema；
- 鉴权；
- 生命周期；
- 错误格式。

这就是典型的 M×N 集成问题。

MCP 的目标之一，是把它变成：

~~~text
Agent Host
   ↓
MCP Client
   ↓
统一协议
   ↓
MCP Server
   ↓
外部能力
~~~

不是让所有系统“一夜之间自动兼容”，而是定义一个双方都能遵守的协议边界。

---

## 5.2 MCP 要解决的 M×N 问题

### 没有 MCP

假设：

~~~text
M 个 Agent Host
N 个 Tool Provider
~~~

理论上可能出现接近：

~~~text
M × N
~~~

套定制集成。

### 有 MCP

每个 Host 只需要实现 MCP Client 一侧，每个 Tool Provider 实现 MCP Server 一侧。

概念上变成：

~~~text
M + N
~~~

真实世界还有鉴权、扩展和版本兼容，但接口层的组合爆炸显著降低。

### 对你的 ResearchPilot 有什么意义

如果多论文检索直接写死在 Nanobot AgentLoop：

~~~text
Nanobot Core
    ↓
ResearchPilot Python Function
~~~

以后换 Host 很麻烦。

如果封装成 MCP：

~~~text
Nanobot ─┐
IDE Agent├→ Research MCP Server → Paper Corpus
其他 Host┘
~~~

检索能力就从“某个项目内部函数”变成可复用 capability service。

---

## 5.3 Host、Client、Server 三个角色

### Host

用户真正运行的 Agent 应用。

对本课程来说，Nanobot 就是 Host。

### Client

Host 内负责 MCP protocol/session 的一侧，负责：

- 连接 Server；
- capability discovery；
- tool invocation；
- resource/prompt access；
- transport/lifecycle。

Nanobot current-source 已经封装这部分，不要求你自己手撸底层 JSON-RPC。

### Server

暴露能力的一侧。

例如 Research MCP：

~~~text
search_papers
list_documents
get_passage
~~~

真正的 PDF parsing、embedding、retrieval 都是 Server 背后的 domain logic。

---

## 5.4 MCP 的核心能力

MCP 不只有 Tool。

常见 primitives 包括：

~~~text
Tools
Resources
Prompts
~~~

### Tools

模型可以请求执行的动作，例如：

~~~text
search_papers(query, top_k)
~~~

### Resources

Server 暴露的可读取资源，例如文档、数据库 schema、文件内容。

### Prompts

Server 暴露的可复用 prompt template/capability。

### 为什么本项目优先 Tool

ResearchPilot 最核心的 contract 是：

~~~text
query
→ retrieve passages
→ structured evidence
~~~

天然适合 Tool。

第一版不要为了“把 MCP 功能都用一遍”同时塞 Tools/Resources/Prompts。

---

## 5.5 Tool Calling、MCP、Skill、Plugin 的区别

| 概念 | 解决的问题 |
|---|---|
| Tool Calling | 模型如何结构化表达“我要调用工具” |
| Tool | Host 内一个可执行能力 |
| MCP | Host 与外部 capability server 如何标准化通信 |
| Skill | 给 Agent 的领域/工作方法说明 |
| Agent Plugin | 把 Skill、MCP 等打包成可安装/启用单元 |

一个完整例子：

~~~text
literature-analysis Skill
   ↓
告诉 Agent：先检索，再基于 evidence 回答

search_papers Tool
   ↓
模型决定调用

MCP
   ↓
把调用传给 Research MCP Server

Agent Plugin
   ↓
把 Skill + MCP Server 配置打包
~~~

所以 Skill 不是 Tool，MCP 也不是 Tool Calling 的替代品。

---

## 5.6 Transport：stdio、HTTP、SSE

### stdio

Host 启动本地子进程，通过 stdin/stdout 通信。

优点：

- 本地开发简单；
- 不需要额外端口；
- Server 生命周期容易绑定 Host。

风险：

- Host 实际启动本地进程；
- command/args 本身就是执行边界；
- 不应把 secret 写进命令参数。

### HTTP / SSE

Server 可远程独立部署。

优点：

- 多 Client 共享；
- 语言/进程边界清楚；
- 更适合独立服务。

风险：

- 鉴权；
- 网络超时；
- SSRF；
- OAuth；
- redirect / DNS 安全。

### 第一版 Research MCP 建议

先用 stdio，原因不是它更高级，而是变量更少。

---

## 5.7 Nanobot current-source 的 MCP 架构

关键源码：

~~~text
nanobot/agent/tools/mcp.py
nanobot/agent/tools/registry.py
nanobot/config/schema.py
nanobot/agent/plugins.py
nanobot/cli/agent.py
nanobot/cli/gateway_runtime.py
~~~

current mental model：

~~~text
Config / Agent Plugin
        ↓
MCP Server Config
        ↓
Application Composition Root
        ↓
shared ToolRegistry
        ↓
MCPProvider
        ↓
connect
        ↓
discover MCP capabilities
        ↓
register wrapped tools
        ↓
AgentLoop / AgentRunner
~~~

最关键的一点：

> **MCPProvider 的连接生命周期属于应用启动/关闭层，而不是 AgentLoop。**

官方 architecture 文档对此有明确说明。

---

## 5.8 MCPProvider 源码解读

current class 注释：

~~~python
class MCPProvider:
    """Own configured MCP connections and their dynamic tool registrations."""
~~~

责任可以拆成：

~~~text
configured MCP connections
+
dynamic Tool registrations
~~~

### 5.8.1 CLI 中如何组装

current CLI 可以看到类似：

~~~text
tools = ToolRegistry()
mcp_provider = MCPProvider.from_config(runtime_config, tools)
...
await mcp_provider.connect()
...
AgentLoop.from_config(..., tool_registry=tools)
~~~

所以：

~~~text
同一个 ToolRegistry
     ↑          ↑
MCPProvider   AgentLoop
~~~

### 5.8.2 为什么不是 AgentLoop 自己 new MCPProvider

否则：

- CLI 要复制生命周期；
- Gateway 要复制生命周期；
- SDK 又复制；
- shutdown 更难统一；
- 测试更难替换。

Composition Root 管理后：

~~~text
startup
→ connect infrastructure
→ run Agent
→ shutdown
→ close infrastructure
~~~

ownership 更清楚。

### 5.8.3 为什么 MCP Tool 最终仍进 ToolRegistry

AgentRunner 不应该关心：

~~~text
native Python Tool?
MCP Tool?
plugin Tool?
~~~

它只需要统一的：

~~~text
name
schema
execute
result
~~~

这就是 Adapter 的价值。

---

## 5.9 enabledTools：不是 UI 开关，而是权限边界

current MCPServerConfig 有 enabled_tools。

默认可用：

~~~text
["*"]
~~~

表示允许全部 capabilities。

当配置 allowlist 后，只注册允许的 Tool；current source 对 resources/prompts 也有相应限制语义。

### 为什么重要

假设 Server 暴露：

~~~text
read_file
write_file
delete_file
execute_shell
~~~

Research Agent 实际只需要：

~~~text
read_file
~~~

那么应该：

~~~text
Server Capabilities
      ↓
enabledTools
      ↓
Agent Visible Capabilities
~~~

而不是把“Server 支持什么”误当成“Agent 就该有什么权限”。

---

## 5.10 Agent Plugin 与 MCP

current：

~~~text
nanobot/agent/plugins.py
~~~

支持 Agent Plugins v1。

典型目录：

~~~text
workspace/plugins/research-agent/
├── plugin.json
├── mcp.json
└── skills/
    └── literature-analysis/
        └── SKILL.md
~~~

current source 会：

1. 验证 plugin manifest；
2. 识别 enabled plugin；
3. 读取 plugin skills；
4. 合并 plugin MCP server；
5. 对 package 做 fingerprint / activation 检查。

### Fingerprint 为什么值得学

用户启用了某个经过检查的 package。

如果之后 package 内容被替换，不应该静默继承相同信任。

所以 capability package 本身也是安全边界。

---

## 5.11 MCP 的安全风险

### 1. Local Process Risk

stdio Server 本质是本地进程。

需要审查：

- command；
- args；
- cwd；
- env。

### 2. SSRF

HTTP/SSE MCP 会访问网络。

current Nanobot 对 remote MCP 使用网络安全 guard。

私有目标若必须允许，应只加入窄范围：

~~~text
tools.ssrfWhitelist
~~~

不要为了调通直接放开整个私网段。

### 3. OAuth / Credential

不要把 token 写在：

~~~text
command args
workspace markdown
Git repo
~~~

### 4. Tool Poisoning

不可信 Server 不只可能返回恶意数据，也可能通过：

- Tool Name；
- Description；
- Result Content；

影响模型决策。

---

## 5.12 最小实验

### Experiment 05A：只读 Filesystem MCP

目标：

~~~text
Nanobot
→ local stdio MCP
→ 只允许 read capability
→ 读取测试目录文件
~~~

要求：

1. Server 只访问测试目录；
2. enabledTools 只保留 read；
3. 打开 verbose log；
4. 记录 ToolRegistry 新增了哪些名字。

### Experiment 05B：禁用一个 MCP Tool

同一个 Server 只允许：

~~~text
enabledTools = ["read_file"]
~~~

然后要求 Agent 做 write。

观察：

~~~text
模型看不到 write tool
~~~

而不是等到执行时才拒绝。

---

## 5.13 面试高频题

### Q1：MCP 和 Function Calling 有什么区别？

> Function Calling 是模型与 Host 之间的结构化 Tool 请求机制；MCP 是 Host 与外部 capability server 之间的标准协议。MCP Tool 最终仍可以通过 Function Calling 形式暴露给模型。

### Q2：为什么 Nanobot MCPProvider 不放 AgentLoop？

> MCP connection 是 application-owned infrastructure。CLI、Gateway、SDK 都可能复用 Agent Core，但连接启动、重连和关闭属于 Composition Root；shared ToolRegistry 是两者交点。

### Q3：为什么 enabledTools 很重要？

> 它把 Server 的全部能力裁剪成 Agent 的被授权能力，属于最小权限边界，也减少模型 Tool 选择空间。

### Q4：为什么 ResearchPilot 适合封装 MCP？

> 它已有稳定 domain contract：query → passages + provenance。封装后 Agent orchestration 与 retrieval service 解耦，其他 Host 也能复用。

---

## 5.14 本章总结

记住：

~~~text
Model
  ↓ Tool Call
AgentRunner
  ↓
ToolRegistry
  ↓
MCP Tool Adapter
  ↓
MCPProvider / Connection
  ↓
MCP Server
  ↓
Domain Capability
~~~

下一阶段开始真正动手：先把 current-source 安装、Config、Workspace、Session 跑通，再进入 Memory、Skill 和 MCP 实战。
