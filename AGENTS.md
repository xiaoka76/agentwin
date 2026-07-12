# AGENTS.md — agentwin

> 给 agent 看的项目级"宪法"。人类朋友随手翻翻也行，但**重点是后续接手的 agent**。

## 这是什么

**`agentwin`** 是一个 uv tool 命令行工具，**让 AI agent 方便地通过它来操作远程的支持 WinRM/SSH 的 Windows 设备**。

- **包名 / CLI 命令 / import 名 / QwenPaw skill 名**全部统一为 `agentwin`
- **位置**：`/app/working/workspaces/silver-wolf/coding_projects/agentwin/`
- **技术栈**：Python ≥ 3.10 + `uv` + `typer` + `rich` + `pywinrm`（WinRM）+ `paramiko`（SSH fallback）+ `cryptography`（Fernet）+ `platformdirs`（跨平台路径）

## 给 agent 的快速上手

### 1. 安装工具

```bash
cd /app/working/workspaces/silver-wolf/coding_projects/agentwin
uv tool install -e .
# 现在 agentwin 命令在 PATH 里了
```

### 2. 健康检查

```bash
agentwin health 10.0.0.20
```

### 3. 认证一台 Windows 主机

```bash
agentwin auth 10.0.0.20 --user Administrator --password "Liyuang1998"
# 打印 UUID（12 位 hex），凭据已加密保存
```

### 4. 执行命令 / 采集系统信息

```bash
agentwin execute --host a1b2c3d4 "ipconfig /all"
agentwin sysinfo --host a1b2c3d4
agentwin list
```

## ⚠️ 输出格式约定（极其重要）

> **agent 看到的 stdout ≠ 全部信息**。**绝不要**假设 stdout 里有所有内容。

### 默认行为（无 flag）

```bash
$ agentwin sysinfo
✓ WIN-NAS  a1b2c3d4
  OS    Windows Server 2025 Datacenter (26100)
  CPU   x64
  Disk  C: 120G(89G free) | D: 64G(62G free) | 1 unmounted
  Net   10.0.0.20/23

Full: /home/xiaoka/.config/agentwin/runs/2026-07-12T22-30-15Z/sysinfo.md
```

- **stdout**：状态 + 一句话总结 + **完整路径**（关键！agent 通过路径按需读取）
- **完整内容**：自动落盘到 `~/.config/agentwin/runs/<ISO时间戳>/<subcmd>.md`

### flag 速查

| flag              | 行为                                | 何时用                           |
| ----------------- | --------------------------------- | ----------------------------- |
| *(无)*             | 简洁 stdout + 完整落盘                 | **默认**，agent 主用                |
| `--full`          | 完整内容也打到 stdout                   | 调试 / 一次性看完整结果                 |
| `--quiet` / `-q`  | 只输出状态码 + UUID                    | 脚本管道                          |
| `--json`          | stdout 强制 JSON                   | 需要字段直读时                       |
| `--output <path>` | 自定义落盘路径                          | agent 想控制落盘位置                  |
| `--no-save`       | 落盘也跳过                            | 临时跑 / 隐私场景                    |
| `--no-color`      | 显式关闭 ANSI 颜色（typer 默认自动检测 TTY） | CI / 容器 / 不想看到控制字符             |

> 💡 agent **必须**用 `Read` 工具读 stdout 末尾打印的 `Full: <path>` 路径，才能拿到完整信息。
> 不要只解析 stdout 几行就交差。

## 🗂️ 凭据存储

- **位置**：`~/.config/agentwin/hosts.json`（跨平台由 `platformdirs` 处理）
  - Linux/macOS: `~/.config/agentwin/`
  - Windows: `%APPDATA%\agentwin\`
- **加密**：Fernet（AES-128-CBC + HMAC），密钥 = `hash(machine_id + username + app_salt)`
- **零人工干预**：不需要主密码，不需要 keyring，**换机器 = 重新 auth**（明说这是安全特性）
- **`machine_id` 来源**：
  - Linux: `/etc/machine-id`
  - macOS: `IOPlatformUUID`
  - Windows: `HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid`

**绝对不要**在 stdout 打印明文密码。**绝对不要**写日志到 `hosts.json` 之外。

## 🔌 协议支持

- **首选**：WinRM + NTLM（密码）—— `pywinrm`
- **fallback 链**：SSH + 密钥（推荐 ed25519）> SSH + 密码 —— `paramiko`
- **自动探测**：`health` 子命令报告哪种协议可用

> WinRM 协议本身**不支持 SSH 密钥认证**。但 Windows 自带的 OpenSSH 服务支持密钥，所以两条链路并存。

## 🆔 UUID 策略

```python
uuid = sha256(f"{host}:{port}:{user}:{auth_method}").hexdigest()[:12]
```

- 相同登录信息 → 同一 UUID
- 密码/密钥/端口变化 → UUID 变（合理）
- 用户可加 `--name "nas"` 起人类可读别名

## 📁 项目结构

```
agentwin/
├── pyproject.toml
├── README.md
├── LICENSE                     # MIT
├── AGENTS.md                   # ← 你正在看的这个
├── .gitignore
├── src/agentwin/
│   ├── __init__.py
│   ├── __main__.py             # python -m agentwin
│   ├── cli.py                  # typer app 入口
│   ├── core/
│   │   ├── client.py           # WinRM + SSH 双协议客户端
│   │   ├── auth.py             # 认证 + UUID 生成
│   │   ├── crypto.py           # 凭据加密/解密
│   │   ├── storage.py          # ~/.config/agentwin/ 读写
│   │   └── health.py           # 端口扫描
│   ├── commands/
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── execute.py
│   │   ├── script.py
│   │   ├── sysinfo.py
│   │   ├── list_cmd.py
│   │   ├── remove.py
│   │   ├── cp.py
│   │   └── pull.py
│   └── utils/
│       ├── output.py           # 简洁 / 完整 / JSON 渲染
│       └── clixml.py           # PowerShell CLIXML 噪音过滤
├── skills/agentwin/
│   ├── SKILL.md                # QwenPaw skill 描述
│   └── scripts/                # 包装脚本（可选）
└── tests/
    ├── test_smoke.py
    └── test_uuid.py
```

## 🤖 给 agent 的"调用守则"

1. **必须**按 `agentwin <subcmd>` 形式调用，不要走 `python -m agentwin`（除非调试）
2. **不要**循环检查退出码——typer 退出码 `0` = 成功，`1` = 业务错误，`2` = 参数错误
3. **看到 `Full: <path>` 就去读**——别只盯着 stdout 那几行
4. **跨平台路径**：用 `platformdirs` 拿，不要硬编码 `~/.config/`
5. **长时间任务**（`script` / `cp`）用 `--output <path>` 落盘，方便 agent 后续读取
6. **错误处理**：失败时落盘文件包含 `STDERR` 段，agent 应优先看错误流

## 🛠️ 开发流程

```bash
# 安装（开发模式）
uv tool install -e .

# 跑测试
uv run pytest tests/

# 跑某个子命令
agentwin health 127.0.0.1
```

## 📝 命名 & 命名空间

- **包名**：`agentwin`（PyPI、import、`[project.scripts]` entry point）
- **CLI 主命令**：`agentwin`
- **QwenPaw skill 名**：`agentwin`（**与 CLI 同名**，搜索一次找全）
- **`aw` 别名**：**暂不发布**到 `[project.scripts]`，避免与 PyPI 上 `aw`（"AI Agentic Workflows"）撞名
- 任何时候**不要**改包名为 `agent-win` / `agent_win` / `aw`——会破坏 import 一致性

## ❌ 禁止事项

- ❌ **不要**在 stdout 打印明文密码
- ❌ **不要**硬编码 `~/.config/agentwin/`——用 `platformdirs`
- ❌ **不要**默认 JSON 灌爆 stdout
- ❌ **不要**把 `aw` 加到 `[project.scripts]`
- ❌ **不要**用 `keyring`（容器/无 GUI 环境会卡，违反零干预硬约束）
- ❌ **不要**改包名（破坏 PyPI / 文档 / skill 的一致性）

## 📚 相关记忆

- 银狼工作区：`/app/working/workspaces/silver-wolf/`
- 详细设计背景：`/app/working/workspaces/silver-wolf/memory/2026-07-12/nas-winrm-skill-plan.md`
- 命名调研记录：见 `nas-winrm-skill-plan.md` §7.1
