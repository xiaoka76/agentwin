"""cp subcommand - copy files to/from remote host."""
from pathlib import Path
from typing import Optional

import typer

from agentwin.commands.execute import _resolve_host
from agentwin.core.client import RemoteClient
from agentwin.utils.output import (
    new_run_dir,
    render_concise,
    render_full,
    render_json,
    write_full_markdown,
)


def cp_cmd(
    src: str = typer.Argument(..., help="Source path"),
    dst: str = typer.Argument(..., help="Destination path"),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Host UUID"),
    direction: str = typer.Option("push", "--direction", "-d", help="push or pull"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Copy files to/from the remote host."""
    target, cred = _resolve_host(host)
    client = RemoteClient(cred)
    try:
        if direction == "push":
            bytes_transferred = client.upload(src, dst)
        else:
            bytes_transferred = client.download(src, dst)
    except Exception as e:
        raise typer.Exit(code=1) from e
    finally:
        client.close()

    result = {
        "host_uuid": target,
        "host": cred.host,
        "direction": direction,
        "src": src,
        "dst": dst,
        "bytes_transferred": bytes_transferred,
    }

    run_dir = new_run_dir("cp")
    if not no_save:
        out_path = output or (run_dir / "cp.md")
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(run_dir, "cp", {"host": target, "src": src, "dst": dst, "direction": direction}, result)

    if json_output:
        render_json(result)
    elif quiet:
        return
    elif full:
        render_full(__import__("json").dumps(result, indent=2))
    else:
        lines = [
            f"Direction: {direction}",
            f"  {src} -> {dst}",
            f"  {bytes_transferred} bytes transferred",
        ]
        render_concise("ok", target, lines, output or run_dir / "cp.md")
