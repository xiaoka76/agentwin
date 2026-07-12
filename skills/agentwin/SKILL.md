---
name: agentwin
version: 0.1.0
author: xiaoka
description: Remotely manage Windows machines (NAS, server, workstation) from Linux/macOS/Windows via WinRM or SSH — execute commands, collect system info, transfer files. Use when the user asks to connect to / run commands on / get info from a Windows host, manage a Windows server or NAS, run PowerShell remotely, or transfer files to/from Windows.
homepage: https://github.com/xiaoka76/agentwin
---

# agentwin skill

Use this skill when you need to remotely manage a Windows machine (NAS, server, workstation) from a Linux/macOS/Windows environment via WinRM or SSH.

## Trigger phrases

- "Connect to a Windows machine and run a command"
- "Run PowerShell on remote Windows"
- "Check Windows server status"
- "Get Windows system info"
- "List processes/services on Windows"
- "Upload/download files to/from Windows"
- "Manage my Windows server / NAS"

## Prerequisites

```bash
# Install (one-time, from PyPI)
uv tool install agentwin

# Or use the npx-style runner — no global install needed
uvx agentwin --help
```

If `uv` is not installed yet, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Workflow

### 1. Health check — scan target host

```bash
agentwin health <host>
# e.g. agentwin health 10.0.0.20
# Reports open ports and available protocols (WinRM, SSH)
```

### 2. Authenticate — save encrypted credentials

```bash
agentwin auth <host> --user <username> --password "<password>"
# e.g. agentwin auth 10.0.0.20 --user Administrator --password "mypassword"
# Returns a 12-char hex UUID (e.g. e2404c202530)

# Specify auth method explicitly (default: port 5985→WinRM, port 22→SSH)
agentwin auth <host> --user Administrator --password "mypassword" --method winrm-password
agentwin auth <host> --user Administrator --password "mypassword" --port 2222 --method ssh-password
agentwin auth <host> --user Administrator --key ~/.ssh/id_rsa
```

### 3. Execute commands

```bash
# PowerShell (default) — supports Get-ChildItem, Get-Process, etc.
agentwin execute --host <uuid> "Get-ChildItem C:\Users"

# cmd.exe — use --cmd flag for traditional commands
agentwin execute --host <uuid> --cmd "ipconfig /all"
```

### 4. Collect system information

```bash
agentwin sysinfo --host <uuid>
# Shows OS version, CPU, disk volumes, network interfaces
```

### 5. Run script files or inline content

```bash
# PowerShell script file (default)
agentwin script --host <uuid> ./myscript.ps1

# CMD script file
agentwin script --host <uuid> --cmd ./myscript.bat

# Inline script content — no file needed, pass script directly
agentwin script --host <uuid> --inline "Get-Service | Where-Object Status -eq Running"
agentwin script --host <uuid> --cmd --inline "ipconfig /all"
```

### 6. File transfer

```bash
# Upload a file to remote host
agentwin cp --host <uuid> ./local-file.txt "C:\Users\Administrator\Desktop\"

# Download a file from remote host
agentwin cp --host <uuid> --direction pull "C:\Users\Administrator\Desktop\remote.txt" ./

# Alias for pull
agentwin pull --host <uuid> "C:\Users\Administrator\Desktop\remote.txt" ./
```

**File transfer strategy:**

| Connection | File Size | Method |
|-----------|-----------|--------|
| SSH | Any | SFTP direct transfer (no size limit) |
| WinRM | ≤ 1MB | Base64 chunked upload |
| WinRM | > 1MB | **Error** — prompts user to use SSH or SMB |

> WinRM file transfer is limited by `powershell -encodedcommand` (8191-char CLI limit).
> For large files, enable OpenSSH on the Windows machine and register an SSH connection with `agentwin auth <host> --port 22`.

### 7. Manage saved hosts

```bash
# List all saved hosts
agentwin list

# Remove a saved host
agentwin remove <uuid>
```

## Important notes

### Output format

- Default output is **concise** (key facts + path to full markdown file)
- Full results saved to `~/.config/agentwin/runs/<uuid>/<timestamp>_<subcmd>.md` (`health` uses host IP)
- **Always read the full file** at the path shown in stdout (`Full: <path>`)
- PowerShell output is cleaned: CLIXML noise, progress records, and **pure empty lines** are stripped
- All subcommands support these output flags:

| Flag            | Behavior                              |
|-----------------|---------------------------------------|
| `--full`        | Print full output to stdout           |
| `--quiet` / `-q`| Status code + UUID only               |
| `--json`        | Force JSON output to stdout           |
| `--output <path>`| Custom save path                     |
| `--no-save`     | Skip file save                        |

### Execution environment

| Subcommand  | Default shell | Flag for alternative       |
|-------------|---------------|----------------------------|
| `execute`   | PowerShell    | `--cmd` → cmd.exe          |
| `script`    | PowerShell    | `--cmd` → cmd.exe; `--inline` for inline content |

### Credential security

- Encrypted with Fernet (AES-128-CBC + HMAC), key derived from `machine_id + username + salt`
- Stored in `~/.config/agentwin/hosts.json` (Linux/macOS) or `%APPDATA%\agentwin\` (Windows)
- No master password, no keyring — zero manual intervention
- Changing machine = re-authentication required

### Protocol support

| Protocol | Auth Methods              | Ports          |
|----------|---------------------------|----------------|
| WinRM    | NTLM (password)           | 5985 (HTTP), 5986 (HTTPS) |
| SSH      | Key (ed25519) / Password  | 22             |

- Auto-detected by `health` subcommand
- Fallback chain: WinRM → SSH key → SSH password

## Enabling OpenSSH Server on Windows

Once SSH is enabled on Windows, you can transfer large files via SFTP (bypassing WinRM's size limitation):

```powershell
# Check OpenSSH installation status
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'

# Install OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Start sshd service
Start-Service sshd

# Enable automatic startup
Set-Service -Name sshd -StartupType 'Automatic'

# Ensure TCP port 22 is allowed through firewall
Get-NetFirewallRule -Name *OpenSSH-Server* | Select Name, Enabled

# If not enabled, add the rule manually
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' `
  -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22

# Note: by default, SSH accepts username/password login
```

After setup, register the SSH connection in agentwin:

```bash
agentwin auth <host> --user Administrator --password "your_password" --port 22
```
