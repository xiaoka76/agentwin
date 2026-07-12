"""auth subcommand - authenticate and save encrypted credentials."""
import json
from pathlib import Path
from typing import Optional

import typer

from agentwin.core.auth import AuthMethod, HostCredential, make_uuid
from agentwin.core.crypto import encrypt
from agentwin.core.storage import set_current, upsert_host
from agentwin.utils.output import (
    new_run_dir,
    render_concise,
    render_full,
    render_json,
    write_full_markdown,
)


def auth_cmd(
    host: str = typer.Argument(..., help="Target host IP or hostname"),
    port: int = typer.Option(5985, "--port", "-p", help="Port number"),
    user: str = typer.Option("Administrator", "--user", "-u", help="Username"),
    password: Optional[str] = typer.Option(None, "--password", "-P", help="Password"),
    key: Optional[Path] = typer.Option(None, "--key", "-k", help="SSH private key path"),
    method: Optional[str] = typer.Option(
        None, "--method", "-m",
        help="Auth method: winrm-password, ssh-password, ssh-key. Auto-detected if not set."
    ),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Human-readable alias"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Authenticate and save encrypted credentials for a remote host."""
    if not password and not key:
        raise typer.BadParameter("Either --password or --key must be provided.")

    if method:
        valid_methods = ("winrm-password", "ssh-password", "ssh-key")
        if method not in valid_methods:
            raise typer.BadParameter(
                f"Invalid method '{method}'. Must be one of: {', '.join(valid_methods)}"
            )
        auth_method: AuthMethod = method  # type: ignore[assignment]
    elif key:
        auth_method = "ssh-key"
    elif port == 22:
        auth_method = "ssh-password"
    else:
        auth_method = "winrm-password"

    secret = encrypt(str(key.resolve()) if key else (password or ""))

    uuid = make_uuid(host, port, user, auth_method)

    cred = HostCredential(
        uuid=uuid,
        host=host,
        port=port,
        user=user,
        auth_method=auth_method,
        secret_enc=secret,
        name=name,
    )

    upsert_host(cred)
    set_current(uuid)

    result = {
        "uuid": uuid,
        "host": host,
        "port": port,
        "user": user,
        "auth_method": auth_method,
        "name": name,
    }

    out_file = new_run_dir("auth", "auth")
    if not no_save:
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(output or out_file, "auth", {"host": host, "port": port, "user": user}, result)

    if json_output:
        render_json(result)
    elif quiet:
        return
    elif full:
        render_full(json.dumps(result, indent=2))
    else:
        name_part = f" (name: {name})" if name else ""
        lines = [f"saved{name_part}", f"  Host: {host}:{port}", f"  User: {user}", f"  Auth: {auth_method}"]
        render_concise("ok", uuid, lines, output or out_file)
