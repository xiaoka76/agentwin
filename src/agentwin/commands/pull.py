"""pull subcommand - alias for cp --direction pull."""
from pathlib import Path
from typing import Optional

import typer

from agentwin.commands.cp import cp_cmd


def pull_cmd(
    remote: str = typer.Argument(..., help="Remote source path"),
    local: str = typer.Argument(..., help="Local destination path"),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Host UUID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Download a file from remote host (alias for cp --direction pull)."""
    # Delegate to cp_cmd with direction=pull
    cp_cmd(
        src=remote,
        dst=local,
        host=host,
        direction="pull",
        json_output=json_output,
        full=full,
        quiet=quiet,
        output=output,
        no_save=no_save,
    )
