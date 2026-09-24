# 06 — Current Source Setup / Config / Workspace / Session

## 环境

current source：

- Python 3.11+
- Git
- Bun（editable source checkout 的 matching TUI 需要）

Windows PowerShell：

```powershell
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
nanobot --version
nanobot webui
```

如果只用稳定包，不应假设 `main` 文档与安装版本完全同步。

## 第一次只验证 4 件事

```powershell
nanobot status
nanobot agent -m "Reply only: setup-ok"
nanobot webui
nanobot gateway status
```

先别接 Feishu/MCP。

## Config vs Workspace

默认：

```text
~/.nanobot/config.json         providers/channels/tools/runtime settings
~/.nanobot/workspace/          memory/skills/cron/artifacts
~/.nanobot/sessions/<id>/      session JSONL，放在 agent workspace 外
```

配置一般优先 WebUI；需要 advanced config-as-code 时再直接改 JSON。

## Project workspace

WebUI 可以给某个 chat 选择另一个 project workspace。

你要做一个验证：

1. agent workspace 写 `USER.md`；
2. project A 写 `AGENTS.md`；
3. project B 写不同 `AGENTS.md`；
4. 在 WebUI 切换 project；
5. 观察 project instructions 跟着 project 变，而 agent identity/memory 不变。

## Provider / model

不要把 credential、apiBase、model ID 混用。用：

```powershell
nanobot onboard --wizard
```

或 WebUI Settings → Models。

## 本章验收

你能解释：

- 为什么 session 放在 config-dir 而不是普通 workspace 文件里；
- workspace-id 的意义；
- `nanobot webui` 和 `nanobot gateway` 的进程关系；
- one-shot agent 和 long-running gateway 是否复用 runtime。
