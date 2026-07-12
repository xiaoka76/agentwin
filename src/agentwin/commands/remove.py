"""remove subcommand - remove a saved host by UUID."""
from pathlib import Path
from typing import Optional

import typer

from agentwin.core.storage import remove_host
from agentwin.utils.output import (
    new_run_dir,
    render_concise,
    render_full,
    render_json,
    write_full_markdown,
)


def remove_cmd(
    uuid: str = typer.Argument(..., help="Host UUID to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Remove a saved host by UUID."""
    if not force:
        typer.confirm(f"Remove host {uuid}?", abort=True)

    removed = remove_host(uuid)

    result = {"uuid": uuid, "removed": removed}

    run_dir = new_run_dir("remove")
    if not no_save:
        out_path = output or (run_dir / "remove.md")
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(run_dir, "remove", {"uuid": uuid}, result)

    if json_output:
        render_json(result)
    elif quiet:
        return
    elif full:
        render_full(__import__("json").dumps(result, indent=2))
    else:
        if removed:
            lines = [f"Removed {uuid}"]
            render_concise("ok", None, lines, output or run_dir / "remove.md")
        else:
            lines = [f"Host {uuid} not found"]
            render_concise("error", None, lines, output or run_dir / "remove.md")
