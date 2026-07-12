"""Output rendering: concise / full / JSON."""
import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from agentwin.core.storage import runs_dir

console = Console()


def new_run_dir(uuid: str, subcmd: str) -> Path:
    """Create a timestamped run file under ~/.config/agentwin/runs/<uuid>/."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    d = runs_dir() / uuid
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{ts}_{subcmd}.md"


def write_full_markdown(
    out_path: Path,
    subcmd: str,
    params: Dict[str, Any],
    result: Dict[str, Any],
) -> Path:
    """Write full result as markdown to out_path."""
    lines = [
        f"# agentwin {subcmd} - Full Report",
        "",
        f"- **Timestamp**: {datetime.now(timezone.utc).isoformat()}",
        f"- **Host**: {socket.gethostname()}",
        f"- **Run ID**: {out_path.stem}",
        "",
        "## Parameters",
        "",
        "```json",
        json.dumps(params, indent=2, ensure_ascii=False, default=str),
        "```",
        "",
        "## Result",
        "",
        "```json",
        json.dumps(result, indent=2, ensure_ascii=False, default=str),
        "```",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def render_concise(
    status: str,
    uuid: Optional[str],
    summary_lines: list,
    full_path: Path,
) -> None:
    """Render the default agent-friendly concise output."""
    icon = "✓" if status == "ok" else "✗"
    parts = [f"{icon}"]
    if uuid:
        parts.append(f"{uuid}")
    for line in summary_lines:
        parts.append(f"  {line}")
    parts.append(f"  Full: {full_path}")
    console.print("\n".join(parts))


def render_json(data: Any) -> None:
    console.print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def render_full(text: str) -> None:
    console.print(text)
