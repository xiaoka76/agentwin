"""Auth flow + UUID generation."""
import hashlib
from dataclasses import dataclass, asdict
from typing import Literal, Optional

AuthMethod = Literal["winrm-password", "ssh-key", "ssh-password"]


@dataclass
class HostCredential:
    uuid: str
    host: str
    port: int
    user: str
    auth_method: AuthMethod
    # 加密后的密码或 base64 编码的私钥路径
    secret_enc: str
    # 可选别名
    name: Optional[str] = None


def make_uuid(host: str, port: int, user: str, auth_method: AuthMethod) -> str:
    """Stable 12-char UUID from connection params."""
    raw = f"{host}:{port}:{user}:{auth_method}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def to_dict(cred: HostCredential) -> dict:
    return asdict(cred)


def from_dict(d: dict) -> HostCredential:
    """Deserialize from dict with validation."""
    required = {"uuid", "host", "port", "user", "auth_method", "secret_enc"}
    missing = required - d.keys()
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    return HostCredential(**{k: v for k, v in d.items() if k in HostCredential.__dataclass_fields__})
