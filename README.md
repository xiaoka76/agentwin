# agentwin

[![PyPI](https://img.shields.io/pypi/v/agentwin.svg)](https://pypi.org/project/agentwin/)
[![Python](https://img.shields.io/pypi/pyversions/agentwin.svg)](https://pypi.org/project/agentwin/)
[![License](https://img.shields.io/pypi/l/agentwin.svg)](https://github.com/xiaoka76/agentwin/blob/main/LICENSE)
[![CI](https://github.com/xiaoka76/agentwin/actions/workflows/ci.yml/badge.svg)](https://github.com/xiaoka76/agentwin/actions)

**Agent-friendly Windows remote management CLI** — a `uv tool` for AI agents to remotely manage Windows machines via WinRM or SSH.

---

## English

### What is agentwin?

`agentwin` is a command-line tool designed for AI agents (and humans) to interact with remote Windows devices. It supports both WinRM (NTLM) and SSH protocols, with automatic protocol detection, encrypted credential storage, and agent-friendly output formatting.

### Installation

#### 🚀 For AI agents: one-liner install

If you are an AI agent setting up `agentwin` for your user, run this **single command** (it auto-installs `uv` if missing, then installs `agentwin`):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && uv tool install agentwin && agentwin --version
```

That's it — no interactive prompts, no dependencies to figure out. The tool is now available as the `agentwin` command.

#### Recommended: `uv tool install`

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install agentwin
uv tool install agentwin

# Verify
agentwin --version
```

#### npx-style: `uvx` (run without installing)

`uvx` is the Python equivalent of `npx` — it downloads, runs, and discards. Perfect for one-off commands or trying it out:

```bash
# Run any subcommand without globally installing
uvx agentwin health 10.0.0.20
uvx agentwin sysinfo --host <uuid>
uvx agentwin --help

# Always use the latest version
uvx --from agentwin agentwin --version
```

#### Alternative: `pipx`

```bash
pipx install agentwin
```

#### From source (for contributors)

```bash
git clone https://github.com/xiaoka76/agentwin.git
cd agentwin
uv tool install -e .
```

### Quick Start

```bash
# 1. Health check — scan ports and detect available protocols
agentwin health 10.0.0.20

# 2. Authenticate — save encrypted credentials
agentwin auth 10.0.0.20 --user Administrator --password "your_password"

#    Or specify auth method explicitly (default: port 5985→WinRM, port 22→SSH)
agentwin auth 10.0.0.20 --user Administrator --password "your_password" --method winrm-password
agentwin auth 10.0.0.20 --user Administrator --password "your_password" --port 2222 --method ssh-password
agentwin auth 10.0.0.20 --user Administrator --key ~/.ssh/id_rsa

# 3. List saved hosts
agentwin list

# 4. Execute a command (default: PowerShell)
agentwin execute --host a1b2c3d4 "Get-ChildItem C:\Users"
#    Use --cmd to run via cmd.exe instead
agentwin execute --host a1b2c3d4 --cmd "ipconfig /all"

# 5. Collect system information
agentwin sysinfo --host a1b2c3d4
```

### Subcommands

| Command     | Description                                      |
|-------------|--------------------------------------------------|
| `health`    | Scan target host for open ports and protocols    |
| `auth`      | Authenticate and save encrypted credentials      |
| `execute`   | Run a single command (default: PowerShell, `--cmd` for cmd.exe) |
| `script`    | Run a PowerShell script (default) or CMD (`--cmd`) via file or `--inline` |
| `sysinfo`   | Collect comprehensive system information         |
| `list`      | List all saved hosts                             |
| `remove`    | Remove a saved host by UUID                      |
| `cp`        | Copy files to/from remote host                   |
| `pull`      | Alias for `cp --direction pull`                  |

### Output Format

By default, `agentwin` prints a **concise summary** to stdout and saves the **full result** as a markdown file:

```
$ agentwin sysinfo --host a1b2c3d4
✓ WIN-NAS  a1b2c3d4
  OS    Windows Server 2025 Datacenter (26100)
  CPU   x64
  Disk  C: 120G(89G free) | D: 64G(62G free) | 1 unmounted
  Net   10.0.0.20/23

Full: /home/user/.config/agentwin/runs/a1b2c3d4/2026-07-12T22-30-15Z_sysinfo.md
```

**Always read the full file** at the path shown in stdout for complete results.

#### Output Flags

| Flag            | Behavior                              |
|-----------------|---------------------------------------|
| *(none)*        | Concise stdout + full file saved      |
| `--full`        | Print full output to stdout           |
| `--quiet` / `-q`| Status code + UUID only               |
| `--json`        | Force JSON output to stdout           |
| `--output <path>`| Custom save path                     |
| `--no-save`     | Skip file save                        |
| `--no-color`    | Disable ANSI colors                   |

### Credential Security

- Credentials are encrypted with **Fernet** (AES-128-CBC + HMAC)
- The encryption key is derived from `machine_id + username + app_salt`
- Stored in `~/.config/agentwin/hosts.json` (cross-platform via `platformdirs`)
- **No master password, no keyring** — zero manual intervention
- **Changing machine = re-authentication required** (security by design)

### Protocol Support

| Protocol | Auth Methods              | Ports          |
|----------|---------------------------|----------------|
| WinRM    | NTLM (password)           | 5985 (HTTP), 5986 (HTTPS) |
| SSH      | Key (ed25519) / Password  | 22             |

- **Auto-detection**: `health` subcommand reports which protocols are available
- **Fallback chain**: WinRM → SSH key → SSH password

### File Transfer Strategy

| Protocol | File Size | Method |
|----------|-----------|--------|
| SSH | Any | SFTP direct transfer (no size limit, speed = network bandwidth) |
| WinRM | ≤ 1MB | Base64 chunked upload (limited by `powershell -encodedcommand` 8191-char limit) |
| WinRM | > 1MB | Error: prompts user to use SSH or SMB |

> WinRM is not suitable for large files due to SOAP/XML protocol overhead.
> Enable OpenSSH on Windows and use `agentwin auth <host> --port 22` for large file transfers.

---

## 中文

### 项目简介

`agentwin` 是一个命令行工具，专为 AI agent（以及人类）设计，用于通过 WinRM 或 SSH 协议远程管理 Windows 设备。

### 安装

#### 🚀 给 AI agent 的一键安装

如果你是 AI agent，要为你的用户装 `agentwin`，**一行命令搞定**（缺 `uv` 就自动装，完了装 `agentwin`）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && uv tool install agentwin && agentwin --version
```

完事——没有交互提示，没有依赖要操心。装完 `agentwin` 命令就能用了。

#### 推荐：`uv tool install`

```bash
# 装 uv（如果还没装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 装 agentwin
uv tool install agentwin

# 验证
agentwin --version
```

#### npx 风格：`uvx`（免安装直接跑）

`uvx` 是 Python 的 `npx`——下载、运行、丢弃。适合临时跑命令或先体验一下：

```bash
# 不用全局装，直接跑任何子命令
uvx agentwin health 10.0.0.20
uvx agentwin sysinfo --host <uuid>
uvx agentwin --help

# 始终用最新版本
uvx --from agentwin agentwin --version
```

#### 备选：`pipx`

```bash
pipx install agentwin
```

#### 从源码装（贡献者用）

```bash
git clone https://github.com/xiaoka76/agentwin.git
cd agentwin
uv tool install -e .
```

### 快速开始

```bash
# 1. 健康检查 — 扫描端口并检测可用协议
agentwin health 10.0.0.20

# 2. 认证 — 保存加密凭据
agentwin auth 10.0.0.20 --user Administrator --password "你的密码"

#    也可用 --method 显式指定认证方式（默认端口 5985→WinRM，22→SSH）
agentwin auth 10.0.0.20 --user Administrator --password "你的密码" --method winrm-password
agentwin auth 10.0.0.20 --user Administrator --password "你的密码" --port 2222 --method ssh-password
agentwin auth 10.0.0.20 --user Administrator --key ~/.ssh/id_rsa

# 3. 列出已保存的主机
agentwin list

# 4. 执行命令（默认 PowerShell）
agentwin execute --host a1b2c3d4 "Get-ChildItem C:\Users"
#    加 --cmd 改用 cmd.exe
agentwin execute --host a1b2c3d4 --cmd "ipconfig /all"

# 5. 采集系统信息
agentwin sysinfo --host a1b2c3d4
```

### 子命令清单

| 命令       | 说明                           |
|-----------|--------------------------------|
| `health`  | 扫描目标主机的开放端口和协议       |
| `auth`    | 认证并保存加密凭据               |
| `execute` | 执行单条命令（默认 PowerShell，`--cmd` 走 cmd.exe） |
| `script`  | 运行 PowerShell（默认）或 CMD（`--cmd`）脚本（文件或 `--inline`） |
| `sysinfo` | 采集全面的系统信息               |
| `list`    | 列出所有已保存的主机             |
| `remove`  | 按 UUID 删除已保存的主机         |
| `cp`      | 向/从远程主机复制文件            |
| `pull`    | `cp --direction pull` 的别名    |

### 输出格式说明

默认情况下，`agentwin` 在 stdout 打印**简洁摘要**，并将**完整结果**保存为 markdown 文件：

```
$ agentwin sysinfo --host a1b2c3d4
✓ WIN-NAS  a1b2c3d4
  OS    Windows Server 2025 Datacenter (26100)
  CPU   x64
  Disk  C: 120G(89G free) | D: 64G(62G free) | 1 unmounted
  Net   10.0.0.20/23

Full: /home/user/.config/agentwin/runs/a1b2c3d4/2026-07-12T22-30-15Z_sysinfo.md
```

**务必读取** stdout 末尾路径指向的完整文件以获取全部信息。

### 凭据存储

- 凭据使用 **Fernet**（AES-128-CBC + HMAC）加密
- 加密密钥由 `machine_id + username + app_salt` 派生
- 存储在 `~/.config/agentwin/hosts.json`（通过 `platformdirs` 跨平台）
- **无需主密码，无需 keyring** — 零人工干预
- **换机器 = 重新认证**（安全设计）

### 协议支持

| 协议    | 认证方式              | 端口            |
|--------|----------------------|----------------|
| WinRM  | NTLM（密码）          | 5985 (HTTP), 5986 (HTTPS) |
| SSH    | 密钥 (ed25519) / 密码 | 22             |

- **自动探测**：`health` 子命令报告哪些协议可用
- **降级链**：WinRM → SSH 密钥 → SSH 密码

### 文件传输策略

| 连接类型 | 文件大小 | 传输方式 |
|---------|---------|---------|
| SSH | 任意 | SFTP 直传（无大小限制，速度取决于网络带宽） |
| WinRM | ≤ 1MB | Base64 分块上传（受 `powershell -encodedcommand` 命令行 8191 字符限制） |
| WinRM | > 1MB | 报错提示用户使用 SSH 或 SMB |

> WinRM 因 SOAP/XML 协议开销不适合传输大文件。建议在 Windows 上启用 OpenSSH 服务，然后用 `agentwin auth <host> --port 22` 注册 SSH 连接以支持大文件传输。
