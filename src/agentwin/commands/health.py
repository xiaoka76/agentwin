"""health subcommand - port scanning and protocol detection."""
from pathlib import Path
from typing import Optional

import typer

from agentwin.core.health import DEFAULT_PORTS, available_protocols, scan
from agentwin.utils.output import (
    new_run_dir,
    render_concise,
    render_full,
    render_json,
    write_full_markdown,
)


def health_cmd(
    host: str = typer.Argument(..., help="Target host IP or hostname"),
    ports: str = typer.Option("", "--ports", "-p", help="Comma-separated custom ports"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    full: bool = typer.Option(False, "--full", help="Print full output to stdout"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    no_save: bool = typer.Option(False, "--no-save"),
):
    """Scan target host for open ports and detect available protocols."""
    custom_ports = [int(p) for p in ports.split(",") if p.strip()] if ports else DEFAULT_PORTS
    results = scan(host, custom_ports)
    protos = available_protocols(results)
    open_ports = [r for r in results if r["open"]]

    result = {
        "host": host,
        "scan_results": results,
        "available_protocols": protos,
        "open_port_count": len(open_ports),
    }

    run_dir = new_run_dir("health")
    if not no_save:
        out_path = output or (run_dir / "health.md")
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
        write_full_markdown(run_dir, "health", {"host": host, "ports": custom_ports}, result)

    if json_output:
        render_json(result)
    elif quiet:
        return
    elif full:
        render_full(__import__("json").dumps(result, indent=2))
    else:
        lines = [
            f"Host: {host}",
            f"Open: {', '.join(str(r['port']) for r in open_ports) or '(none)'}",
            f"Protocols: {', '.join(protos) or '(none)'}",
        ]
        render_concise("ok", None, lines, output or run_dir / "health.md")
