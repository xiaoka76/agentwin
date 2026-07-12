"""script subcommand - run a PowerShell or CMD script from file or inline content."""
import json
from pathlib import Path
from typing import Optional

import typer

from agentwin.core.storage import resolve_host
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
    script_file: Optional[Path] = typer.Argument(None, help="Path to script file", exists=True, readable=True),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Host UUID"),
    cmd: bool = typer.Option(False, "--cmd", help="Run as CMD script"),
    inline: Optional[str] = typer.Option(None, "--inline", "-i", help="Inline script content (instead of file)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Run a PowerShell or CMD script on the remote host.

    Pass a script file path as argument, or use --inline to pass script content directly.

    Examples:
      agentwin script ./myscript.ps1 --host abc
      agentwin script --inline "Get-Service | Where-Object Status -eq Running" --host abc
    """
    if script_file and inline:
        raise typer.BadParameter("Cannot specify both script file and --inline. Choose one.")
    if not script_file and not inline:
        raise typer.BadParameter("Must specify a script file or use --inline to provide script content.")

    try:
        target, cred = resolve_host(host)
    except ValueError as e:
        raise typer.BadParameter(str(e))

    if script_file:
        script_content = script_file.read_text(encoding="utf-8")
        script_source = str(script_file)
        script_name = script_file.name
    else:
        script_content = inline
        script_source = "<inline>"
        script_name = "inline"

    client = RemoteClient(cred)
    try:
        if cmd:
            exit_code, stdout, stderr = client.run_cmd(script_content)
        else:
            exit_code, stdout, stderr = client.run_ps(script_content)
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
        "script_source": script_source,
        "exit_code": exit_code,
        "stdout": stdout_clean,
        "stderr": stderr_clean,
    }

    out_path = new_run_dir(target, "script")
    if not no_save:
        if output:
            out_path = output
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(out_path, "script", {"host": target, "script_source": script_source}, result)

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
            f"Script: {script_name}",
        ]
        if tail:
            lines.append(f"Last {len(tail)} line(s):")
            for l in tail:
                lines.append(f"  {l}")
        if stderr_clean:
            lines.append(f"Stderr: {stderr_clean[:200]}")
        render_concise("ok" if exit_code == 0 else "error", target, lines, out_path)
