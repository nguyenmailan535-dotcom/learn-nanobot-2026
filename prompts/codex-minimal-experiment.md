# Codex Prompt — Minimal Experiment

```text
我想验证：{HYPOTHESIS}

请在当前仓库新增一个独立最小实验，不改 Nanobot core。

约束：
- 一次只验证这个 hypothesis；
- 一个文件优先；
- 不提前做 class hierarchy / config framework；
- 打印关键中间状态；
- 给 PowerShell 运行命令；
- 说明预期输出；
- 实际运行；
- 结果出来后停止，不自动进入下一优化。

如果实验依赖 current-source 行为，先 grep/读取相关实现确认 API，不要按旧教程猜。
```
