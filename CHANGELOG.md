# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-07-13

### Fixed
- Removed unsupported `timeout` keyword argument from `pywinrm.Session.run_ps()` call, which caused `TypeError` when executing PowerShell commands via WinRM. PowerShell commands now run correctly over WinRM.

## [0.1.0] - 2026-07-13

### Added
- Initial public release of `agentwin`.
- Agent-friendly CLI for managing Windows hosts over WinRM (NTLM) and SSH (key/password).
- Nine subcommands: `health`, `auth`, `list`, `remove`, `execute`, `script`, `sysinfo`, `cp`, `pull`.
- Fernet-encrypted credential storage with a machine-derived key (no master password, zero manual setup).
- Default output is concise stdout + full run log written to `~/.local/state/agentwin/runs/<ISO-ts>/<subcmd>.md` for agent consumption.
- Flags: `--full`, `--quiet`/`-q`, `--json`, `--output`, `--no-save`, `--no-color`.
- Cross-platform paths via `platformdirs` (Linux/macOS/Windows).
- QwenPaw skill `agentwin` shipped under `skills/agentwin/`.

### Notes
- This is the first published version; the package name `agentwin` and the GitHub repo `xiaoka76/agentwin` are now linked.
- Credential files are not portable across machines by design (machine-derived key).
