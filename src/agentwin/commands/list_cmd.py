"""list subcommand - list all saved hosts."""
from pathlib import Path
from typing import Optional

import typer

from agentwin.core.storage import load_hosts
from agentwin.utils.output import (
    new_run_dir,
    render_concise,
    render_full,
    render_json,
    write_full_markdown,
)


def list_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """List all saved hosts."""
    hosts = load_hosts()

    host_list = []
    for h in hosts:
        host_list.append({
            "uuid": h.uuid,
            "name": h.name or "",
            "host": h.host,
            "port": h.port,
            "user": h.user,
            "auth_method": h.auth_method,
        })

    result = {"hosts": host_list, "count": len(host_list)}

    run_dir = new_run_dir("list")
    if not no_save:
        out_path = output or (run_dir / "list.md")
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(run_dir, "list", {}, result)

    if json_output:
        render_json(result)
    elif quiet:
        return
    elif full:
        render_full(__import__("json").dumps(result, indent=2))
    else:
        if not hosts:
            lines = ["(no hosts saved)"]
            render_concise("ok", None, lines, output or run_dir / "list.md")
        else:
            for h in hosts:
                name_part = f" ({h.name})" if h.name else ""
                lines = [
                    f"{h.uuid}{name_part}",
                    f"  {h.user}@{h.host}:{h.port} [{h.auth_method}]",
                ]
                render_concise("ok", None, lines, output or run_dir / "list.md")
