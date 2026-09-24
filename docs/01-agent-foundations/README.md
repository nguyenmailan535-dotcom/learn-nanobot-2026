# 01 — Agent 基础：只学后面源码和面试会真正用到的部分

## 本章目标

不是重新学一遍“什么是大模型”，而是建立后面读 Nanobot 的最小 vocabulary。

你完成本章后必须能解释：

```text
LLM call
≠
Agent turn
```

普通 LLM 调用通常是：

```text
messages → provider → response
```

Agent turn 至少多了：

```text
state/context
+ tools
+ execution loop
+ environment effects
+ stop condition
```

## 最小 Agent Loop

```python
messages = [user_message]

while True:
    response = llm(messages, tools=tool_schemas)

    if response.tool_calls:
        tool_results = execute(response.tool_calls)
        messages += [response, *tool_results]
        continue

    return response.text
```

真正框架复杂的地方不是这个 `while`，而是：

- 上下文从哪里来；
- session 如何隔离；
- tool schema 如何发现；
- tool error 如何处理；
- streaming 如何恢复；
- concurrent tools / concurrent sessions 怎么管；
- workspace 权限边界在哪里；
- 超长 context 怎么 compact；
- long-term memory 如何更新；
- background automation 如何重新进入 agent turn。

## ReAct 不要死背 Thought 文本

面试时更准确的说法：ReAct 的核心是 **模型推理和环境行动交替**。现代 API 可能不暴露完整 reasoning 文本，但 `model → tool call → observation → model` 的闭环仍然存在。

## Agent / Workflow

- Workflow：控制流主要由开发者显式定义；
- Agent：模型对下一步工具/行动有更大决策权；
- 实际系统通常混合：外层是 deterministic workflow，局部是 agentic loop。

## 为什么本仓库会一直强调 Eval

Agent 的输出不是普通函数的完全确定结果。一个“跑通”的 Demo 不代表系统可靠。

以后每个项目至少区分：

```text
retrieval failure
planning/tool-selection failure
tool execution failure
generation/grounding failure
citation failure
permission/sandbox failure
```

## 面试自测

1. Function Calling 和 Agent 的关系是什么？
2. 为什么 Tool Calling 本身不等于 Agent？
3. Agent 的状态至少有哪些层次？
4. 为什么一个 Agent 项目必须做 trace / bad case，而不能只展示成功截图？
5. Java 后端里的“请求级状态”和 Agent session 有什么相同/不同？

## 完成标准

用你自己的话画一张：

```text
User → Agent → Model → Tool → Observation → Agent → User
```

并在图上标出 state、session、context、side effect。
