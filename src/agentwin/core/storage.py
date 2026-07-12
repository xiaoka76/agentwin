"""~/.config/agentwin/ storage layer."""
import json
from pathlib import Path
from typing import List, Optional

from platformdirs import user_config_dir

from agentwin.core.auth import HostCredential, from_dict
from agentwin.core.crypto import decrypt, encrypt

APP_NAME = "agentwin"
HOSTS_FILE = "hosts.json"
CURRENT_FILE = "current"


def config_dir() -> Path:
    p = Path(user_config_dir(APP_NAME))
    p.mkdir(parents=True, exist_ok=True)
    return p


def runs_dir() -> Path:
    """运行日志/落盘目录。与 config 合并（项目决策：单一目录备份更省事）。"""
    p = config_dir() / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def hosts_path() -> Path:
    return config_dir() / HOSTS_FILE


def current_path() -> Path:
    return config_dir() / CURRENT_FILE


def load_hosts() -> List[HostCredential]:
    p = hosts_path()
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return [from_dict(d) for d in data.get("hosts", [])]


def save_hosts(hosts: List[HostCredential]) -> None:
    payload = {"hosts": [h.__dict__ for h in hosts]}
    hosts_path().write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_host(uuid: str) -> Optional[HostCredential]:
    for h in load_hosts():
        if h.uuid == uuid:
            return h
    return None


def upsert_host(cred: HostCredential) -> None:
    hosts = load_hosts()
    for i, h in enumerate(hosts):
        if h.uuid == cred.uuid:
            hosts[i] = cred
            save_hosts(hosts)
            return
    hosts.append(cred)
    save_hosts(hosts)


def remove_host(uuid: str) -> bool:
    hosts = load_hosts()
    new_hosts = [h for h in hosts if h.uuid != uuid]
    if len(new_hosts) == len(hosts):
        return False
    save_hosts(new_hosts)
    return True


def set_current(uuid: str) -> None:
    current_path().write_text(uuid, encoding="utf-8")


def get_current() -> Optional[str]:
    p = current_path()
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8").strip() or None
