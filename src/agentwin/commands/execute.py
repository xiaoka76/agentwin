"""execute subcommand - run a single command on remote host."""
import json
from pathlib import Path
from typing import Optional

import typer

from agentwin.core.client import RemoteClient
from agentwin.core.storage import resolve_host
from agentwin.utils.clixml import clean
from agentwin.utils.output import (
    new_run_dir,
    render_concise,
    render_full,
    render_json,
    write_full_markdown,
)


def execute_cmd(
    command: str = typer.Argument(..., help="Command to execute"),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Host UUID"),
    cmd: bool = typer.Option(False, "--cmd", help="Run via cmd.exe instead of PowerShell"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Run a single command on the remote host (default: PowerShell)."""
    try:
        target, cred = resolve_host(host)
    except ValueError as e:
        raise typer.BadParameter(str(e))
    client = RemoteClient(cred)
    try:
        if cmd:
            exit_code, stdout, stderr = client.run_cmd(command)
        else:
            exit_code, stdout, stderr = client.run_ps(command)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    finally:
        client.close()

    stdout_clean = clean(stdout)
    stderr_clean = clean(stderr)

    result = {
        "host_uuid": target,
        "host": cred.host,
        "command": command,
        "exit_code": exit_code,
        "stdout": stdout_clean,
        "stderr": stderr_clean,
    }

    out_path = new_run_dir(target, "execute")
    if not no_save:
        if output:
            out_path = output
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(out_path, "execute", {"host": target, "command": command}, result)

    if json_output:
        render_json(result)
    elif quiet:
        return
    elif full:
        render_full(f"Exit code: {exit_code}\n\nSTDOUT:\n{stdout_clean}\n\nSTDERR:\n{stderr_clean}")
    else:
        stdout_lines = stdout_clean.strip().split("\n") if stdout_clean.strip() else []
        tail = stdout_lines[-5:] if len(stdout_lines) > 5 else stdout_lines
        lines = [
            f"Exit: {exit_code}",
            f"Host: {cred.host} ({target})",
        ]
        if tail:
            lines.append(f"Last {len(tail)} line(s):")
            for l in tail:
                lines.append(f"  {l}")
        if stderr_clean:
            lines.append(f"Stderr: {stderr_clean[:200]}")
        render_concise("ok" if exit_code == 0 else "error", target, lines, out_path)
