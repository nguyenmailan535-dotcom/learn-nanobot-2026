# Codex Prompt — Source Trace

把 `{QUESTION}`、`{FILES_OR_SCOPE}` 替换掉后直接使用。

```text
我正在学习 2026-09-24 的 HKUDS/nanobot current-source。

这轮只回答一个问题：
{QUESTION}

范围：
{FILES_OR_SCOPE}

要求：
1. 先用搜索定位真实调用点，不要只根据类名猜；
2. 给出从入口到出口的最短调用链；
3. 对每一跳说明输入/输出数据结构；
4. 区分“源码事实”和“你的解释”；
5. 如果 current source 与旧教程不同，指出差异；
6. 不扩散到我没有问的 Memory/MCP/Deploy 等模块；
7. 最后给我 3 个可以自己验证的断点/日志点；
8. 不改代码，先停下来等我确认理解。
```
