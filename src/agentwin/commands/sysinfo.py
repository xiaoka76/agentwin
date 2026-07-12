"""sysinfo subcommand - collect comprehensive system information."""
from pathlib import Path
from typing import Optional

import typer

from agentwin.commands.execute import _resolve_host
from agentwin.core.client import RemoteClient
from agentwin.utils.clixml import clean
from agentwin.utils.output import (
    new_run_dir,
    render_concise,
    render_full,
    render_json,
    write_full_markdown,
)

SYSINFO_SCRIPT = """
Write-Host "=== COMPUTER INFO ==="
$ci = Get-ComputerInfo
Write-Host "OsName: $($ci.WindowsProductName)"
Write-Host "OsVersion: $($ci.WindowsVersion)"
Write-Host "OsBuild: $($ci.OsBuildNumber)"
Write-Host "OsArch: $($ci.OsArchitecture)"
Write-Host "Manufacturer: $($ci.PCsystemType)"
Write-Host "TotalPhysicalMemory: $($ci.TotalPhysicalMemory)"

Write-Host "=== CPU ==="
Get-CimInstance Win32_Processor | ForEach-Object {
    Write-Host "Name: $($_.Name)"
    Write-Host "Cores: $($_.NumberOfCores)"
    Write-Host "LogicalProcessors: $($_.NumberOfLogicalProcessors)"
    Write-Host "MaxClockSpeed: $($_.MaxClockSpeed)"
}

Write-Host "=== DISK ==="
Get-PhysicalDisk | ForEach-Object {
    Write-Host "FriendlyName: $($_.FriendlyName)"
    Write-Host "MediaType: $($_.MediaType)"
    Write-Host "Size: $($_.Size)"
    Write-Host "HealthStatus: $($_.HealthStatus)"
}

Write-Host "=== VOLUMES ==="
Get-Volume | ForEach-Object {
    Write-Host "DriveLetter: $($_.DriveLetter)"
    Write-Host "FileSystem: $($_.FileSystem)"
    Write-Host "SizeRemaining: $($_.SizeRemaining)"
    Write-Host "Size: $($_.Size)"
}

Write-Host "=== NETWORK ==="
Get-NetIPAddress -AddressFamily IPv4 | ForEach-Object {
    Write-Host "InterfaceAlias: $($_.InterfaceAlias)"
    Write-Host "IPAddress: $($_.IPAddress)"
    Write-Host "PrefixLength: $($_.PrefixLength)"
}
"""


def sysinfo_cmd(
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Host UUID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Collect comprehensive system information from the remote host."""
    target, cred = _resolve_host(host)
    client = RemoteClient(cred)
    try:
        exit_code, stdout, stderr = client.run_ps(SYSINFO_SCRIPT)
    except Exception as e:
        raise typer.Exit(code=1) from e
    finally:
        client.close()

    stdout_clean = clean(stdout)
    stderr_clean = clean(stderr)

    # Parse key fields for concise output
    os_name = _extract_field(stdout_clean, "OsName")
    os_build = _extract_field(stdout_clean, "OsBuild")
    cpu_name = _extract_field(stdout_clean, "Name")
    total_mem = _extract_field(stdout_clean, "TotalPhysicalMemory")

    result = {
        "host_uuid": target,
        "host": cred.host,
        "exit_code": exit_code,
        "raw_output": stdout_clean,
        "stderr": stderr_clean,
    }

    run_dir = new_run_dir("sysinfo")
    if not no_save:
        out_path = output or (run_dir / "sysinfo.md")
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(run_dir, "sysinfo", {"host": target}, result)

    if json_output:
        render_json(result)
    elif quiet:
        return
    elif full:
        render_full(stdout_clean)
    else:
        name_part = f"  {cred.name or cred.host}" if cred.name else f"  {cred.host}"
        lines = [
            name_part,
            f"  OS    {os_name or '?'} ({os_build or '?'})",
            f"  CPU   {cpu_name or '?'}",
            f"  Mem   {_fmt_bytes(total_mem) if total_mem else '?'}",
        ]
        render_concise("ok", target, lines, output or run_dir / "sysinfo.md")


def _extract_field(text: str, field: str) -> Optional[str]:
    """Extract a field value from the PowerShell output."""
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return None


def _fmt_bytes(s: str) -> str:
    """Format byte count to human-readable."""
    try:
        b = int(s)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if b < 1024:
                return f"{b:.0f}{unit}"
            b /= 1024
        return f"{b:.1f}TB"
    except (ValueError, TypeError):
        return s or "?"
