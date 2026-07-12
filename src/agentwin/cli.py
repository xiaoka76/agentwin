"""agentwin CLI entry point."""
import typer
from rich.console import Console

from agentwin.commands.auth import auth_cmd
from agentwin.commands.cp import cp_cmd
from agentwin.commands.execute import execute_cmd
from agentwin.commands.health import health_cmd
from agentwin.commands.list_cmd import list_cmd
from agentwin.commands.pull import pull_cmd
from agentwin.commands.remove import remove_cmd
from agentwin.commands.script import script_cmd
from agentwin.commands.sysinfo import sysinfo_cmd

app = typer.Typer(
    name="agentwin",
    help="Agent-friendly Windows remote management CLI",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.callback()
def main(
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable ANSI colors in output"
    ),
):
    """agentwin - Agent-friendly Windows remote management CLI."""
    if no_color:
        from agentwin.utils.output import console as c

        c.no_color = True


app.command(name="health")(health_cmd)
app.command(name="auth")(auth_cmd)
app.command(name="execute")(execute_cmd)
app.command(name="script")(script_cmd)
app.command(name="sysinfo")(sysinfo_cmd)
app.command(name="list")(list_cmd)
app.command(name="remove")(remove_cmd)
app.command(name="cp")(cp_cmd)
app.command(name="pull")(pull_cmd)

if __name__ == "__main__":
    app()
