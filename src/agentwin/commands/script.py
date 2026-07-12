"""script subcommand - run a PowerShell or CMD script file."""
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


def script_cmd(
    script_file: Path = typer.Argument(..., help="Path to script file", exists=True, readable=True),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Host UUID"),
    ps: bool = typer.Option(False, "--ps", help="Run as PowerShell script"),
    cmd: bool = typer.Option(False, "--cmd", help="Run as CMD script"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Run a PowerShell or CMD script file on the remote host."""
    target, cred = _resolve_host(host)
    script_content = script_file.read_text(encoding="utf-8")

    client = RemoteClient(cred)
    try:
        if ps or cred.auth_method == "winrm-password":
            exit_code, stdout, stderr = client.run_ps(script_content)
        else:
            exit_code, stdout, stderr = client.run_cmd(script_content)
    except Exception as e:
        raise typer.Exit(code=1) from e
    finally:
        client.close()

    stdout_clean = clean(stdout)
    stderr_clean = clean(stderr)

    result = {
        "host_uuid": target,
        "host": cred.host,
        "script_file": str(script_file),
        "exit_code": exit_code,
        "stdout": stdout_clean,
        "stderr": stderr_clean,
    }

    run_dir = new_run_dir("script")
    if not no_save:
        out_path = output or (run_dir / "script.md")
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(run_dir, "script", {"host": target, "script_file": str(script_file)}, result)

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
            f"Script: {script_file.name}",
            f"Last {len(tail)} line(s):",
        ]
        for l in tail:
            lines.append(f"  {l}")
        if stderr_clean:
            lines.append(f"Stderr: {stderr_clean[:200]}")
        render_concise("ok" if exit_code == 0 else "error", target, lines, output or run_dir / "script.md")
