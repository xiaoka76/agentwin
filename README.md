# agentwin

**Agent-friendly Windows remote management CLI** — a `uv tool` for AI agents to remotely manage Windows machines via WinRM or SSH.

---

## English

### What is agentwin?

`agentwin` is a command-line tool designed for AI agents (and humans) to interact with remote Windows devices. It supports both WinRM (NTLM) and SSH protocols, with automatic protocol detection, encrypted credential storage, and agent-friendly output formatting.

### Installation

```bash
# Install from source (development)
cd agentwin
uv tool install -e .

# Or from PyPI (once published)
uv tool install agentwin
```

### Quick Start

```bash
# 1. Health check — scan ports and detect available protocols
agentwin health 10.0.0.20

# 2. Authenticate — save encrypted credentials
agentwin auth 10.0.0.20 --user Administrator --password "your_password"

# 3. List saved hosts
agentwin list

# 4. Execute a command
agentwin execute --host a1b2c3d4 "ipconfig /all"

# 5. Collect system information
agentwin sysinfo --host a1b2c3d4
```

### Subcommands

| Command     | Description                                      |
|-------------|--------------------------------------------------|
| `health`    | Scan target host for open ports and protocols    |
| `auth`      | Authenticate and save encrypted credentials      |
| `execute`   | Run a single command on remote host              |
| `script`    | Run a PowerShell or CMD script file              |
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

Full: /home/user/.config/agentwin/runs/2026-07-12T22-30-15Z/sysinfo.md
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

---

## 中文

### 项目简介

`agentwin` 是一个命令行工具，专为 AI agent（以及人类）设计，用于通过 WinRM 或 SSH 协议远程管理 Windows 设备。

### 安装

```bash
# 从源码安装（开发模式）
cd agentwin
uv tool install -e .

# 或从 PyPI 安装（发布后）
uv tool install agentwin
```

### 快速开始

```bash
# 1. 健康检查 — 扫描端口并检测可用协议
agentwin health 10.0.0.20

# 2. 认证 — 保存加密凭据
agentwin auth 10.0.0.20 --user Administrator --password "你的密码"

# 3. 列出已保存的主机
agentwin list

# 4. 执行命令
agentwin execute --host a1b2c3d4 "ipconfig /all"

# 5. 采集系统信息
agentwin sysinfo --host a1b2c3d4
```

### 子命令清单

| 命令       | 说明                           |
|-----------|--------------------------------|
| `health`  | 扫描目标主机的开放端口和协议       |
| `auth`    | 认证并保存加密凭据               |
| `execute` | 在远程主机上执行单条命令          |
| `script`  | 运行 PowerShell 或 CMD 脚本文件  |
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

Full: /home/user/.config/agentwin/runs/2026-07-12T22-30-15Z/sysinfo.md
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
