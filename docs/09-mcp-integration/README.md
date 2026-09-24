# 09 — 自己做一个 MCP：把 ResearchPilot 变成真实 Agent Capability

## 本章目标

不做“天气 MCP”。直接复用你已有的科研 RAG 能力。

最小 server 只暴露 2 个工具：

```text
search_papers(query, top_k)
answer_with_evidence(query)
```

第一版甚至不需要让 MCP 自己调用 LLM；`search_papers` 返回结构化 passages，让 Nanobot 主 Agent 做 generation。

## 推荐边界

```text
Nanobot Agent
    ↓ MCP
Research MCP Server
    ↓
PDF Corpus / index
    ↓
Document-aware retrieval
```

MCP Server 返回：

```json
{
  "results": [
    {
      "doc_id": "mycroft",
      "page": 12,
      "chunk_id": "mycroft-p12-c12",
      "score": 0.79,
      "text": "..."
    }
  ]
}
```

不要返回一坨自然语言，让 provenance 丢失。

## 为什么这比普通 Demo 值钱

这里同时展示：

- MCP protocol integration；
- domain tool design；
- RAG retrieval；
- structured evidence；
- tool schema design；
- timeout/error boundary；
- Agent 与 domain service 解耦。

## Security

- tool 默认只读；
- corpus root 不接受任意绝对路径；
- 限制 `top_k`；
- 返回文本长度有上限；
- 不把 API key 放 tool result；
- Nanobot 侧用 `enabledTools` 最小暴露。

## 本仓库样例

见：

```text
projects/03-research-plugin/
```

## 验收

让 Nanobot 在不知道具体论文文件名的情况下：

1. 调 `search_papers`；
2. 拿到多个 doc evidence；
3. 用 source metadata 回答；
4. 把一次 tool call trace 保存到项目 README。
