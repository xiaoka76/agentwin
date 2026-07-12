"""Fernet-based credential encryption with machine-derived key."""
import getpass
import hashlib
import platform
import subprocess
from base64 import urlsafe_b64encode
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from platformdirs import user_config_dir

APP_NAME = "agentwin"
SALT_FILE = "salt.key"


def _get_machine_id() -> str:
    """Get a stable machine ID across Linux/macOS/Windows."""
    system = platform.system()
    try:
        if system == "Linux":
            return Path("/etc/machine-id").read_text().strip()
        elif system == "Darwin":
            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatform", "IODeviceTree"],
                stderr=subprocess.DEVNULL,
            ).decode()
            for line in out.split("\n"):
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]
            return platform.node()
        elif system == "Windows":
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
            )
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(value)
        else:
            return platform.node()
    except Exception:
        return platform.node()


def _get_salt() -> bytes:
    """Get or create the per-user salt."""
    config_dir = Path(user_config_dir(APP_NAME))
    config_dir.mkdir(parents=True, exist_ok=True)
    salt_path = config_dir / SALT_FILE
    if not salt_path.exists():
        salt_path.write_bytes(hashlib.sha256(platform.node().encode()).digest())
    return salt_path.read_bytes()


def get_fernet() -> Fernet:
    """Build a Fernet instance with machine-derived key."""
    machine_id = _get_machine_id()
    username = _get_username()
    salt = _get_salt()
    key_material = f"{machine_id}:{username}:agentwin-v1".encode()
    h = hashlib.sha256()
    h.update(salt)
    h.update(key_material)
    fernet_key = urlsafe_b64encode(h.digest())
    return Fernet(fernet_key)


def _get_username() -> str:
    return getpass.getuser()


def encrypt(plaintext: str) -> str:
    """Encrypt a string, return base64 string."""
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a base64 string, return plaintext."""
    return get_fernet().decrypt(token.encode()).decode()
