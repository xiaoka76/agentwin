"""execute subcommand - run a single command on remote host."""
from pathlib import Path
from typing import Optional

import typer

from agentwin.core.client import RemoteClient
from agentwin.core.storage import get_current, get_host
from agentwin.utils.clixml import clean
from agentwin.utils.output import (
    new_run_dir,
    render_concise,
    render_full,
    render_json,
    write_full_markdown,
)


def _resolve_host(uuid: Optional[str]):
    """Resolve UUID from arg or current file."""
    target = uuid or get_current()
    if not target:
        raise typer.BadParameter("No host specified. Run `agentwin auth` first or pass --host.")
    cred = get_host(target)
    if not cred:
        raise typer.BadParameter(f"Host UUID {target} not found in store.")
    return target, cred


def execute_cmd(
    command: str = typer.Argument(..., help="Command to execute"),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Host UUID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Run a single command on the remote host."""
    target, cred = _resolve_host(host)
    client = RemoteClient(cred)
    try:
        exit_code, stdout, stderr = client.run_cmd(command)
    except Exception as e:
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

    run_dir = new_run_dir("execute")
    if not no_save:
        out_path = output or (run_dir / "execute.md")
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(run_dir, "execute", {"host": target, "command": command}, result)

    if json_output:
        render_json(result)
    elif quiet:
        return
    elif full:
        render_full(f"Exit code: {exit_code}\n\nSTDOUT:\n{stdout_clean}\n\nSTDERR:\n{stderr_clean}")
    else:
        stdout_lines = stdout_clean.strip().split("\n")
        tail = stdout_lines[-5:] if len(stdout_lines) > 5 else stdout_lines
        lines = [
            f"Exit: {exit_code}",
            f"Host: {cred.host} ({target})",
            f"Last {len(tail)} line(s):",
        ]
        for l in tail:
            lines.append(f"  {l}")
        if stderr_clean:
            lines.append(f"Stderr: {stderr_clean[:200]}")
        render_concise("ok" if exit_code == 0 else "error", target, lines, output or run_dir / "execute.md")
