# agentwin skill

Use this skill when you need to remotely manage a Windows machine (NAS, server, workstation) from a Linux/macOS environment via WinRM or SSH.

## Trigger

- "Connect to a Windows machine and run a command"
- "Run PowerShell on remote Windows"
- "Check Windows server status"
- "Get Windows system info"
- "List processes/services on Windows"
- "Upload/download files to/from Windows"
- "Manage my Windows server / NAS"

## Quick start

```bash
# 1. Health check
agentwin health 10.0.0.20

# 2. Authenticate
agentwin auth 10.0.0.20 --user Administrator --password "xxx"

# 3. Run commands / collect info
agentwin execute --host <uuid> "ipconfig /all"
agentwin sysinfo --host <uuid>
```

## Important

- The default output is **concise** (key facts + a path to the full markdown). **Read the full file** at the path shown in stdout to get complete results.
- Credentials are encrypted with Fernet + machine-derived key, stored in `~/.config/agentwin/hosts.json`.
- All subcommands support `--json` / `--full` / `--quiet` / `--output` / `--no-save` flags.
