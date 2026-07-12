"""WinRM + SSH dual-protocol client."""
import base64
from pathlib import Path
from typing import Tuple

import paramiko
import winrm

from agentwin.core.auth import HostCredential
from agentwin.core.crypto import decrypt

# WinRM 分块上传最大文件大小（超过此值提示用户使用 SSH/SMB）
WINRM_MAX_FILE_SIZE = 1024 * 1024  # 1MB


def _encode_ps_command(script: str) -> str:
    """Encode a PowerShell script as base64 for -EncodedCommand (UTF-16LE)."""
    return base64.b64encode(script.encode("utf-16-le")).decode()


class RemoteClient:
    """Unified remote execution client."""

    def __init__(self, cred: HostCredential):
        self.cred = cred
        self._winrm = None
        self._ssh = None

    @property
    def _is_ssh(self) -> bool:
        return self.cred.auth_method in ("ssh-password", "ssh-key")

    def _winrm_session(self):
        if self._winrm is None:
            secret = decrypt(self.cred.secret_enc)
            self._winrm = winrm.Session(
                self.cred.host,
                auth=(self.cred.user, secret),
                transport="ntlm",
                server_cert_validation="ignore",
            )
        return self._winrm

    def _ssh_client(self):
        if self._ssh is None:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.cred.auth_method == "ssh-key":
                secret = decrypt(self.cred.secret_enc)  # 私钥文件路径
                pkey = paramiko.RSAKey.from_private_key_file(secret)
                c.connect(
                    self.cred.host,
                    port=self.cred.port,
                    username=self.cred.user,
                    pkey=pkey,
                )
            else:  # ssh-password
                secret = decrypt(self.cred.secret_enc)
                c.connect(
                    self.cred.host,
                    port=self.cred.port,
                    username=self.cred.user,
                    password=secret,
                )
            self._ssh = c
        return self._ssh

    def run_cmd(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Execute a single command. Return (exit_code, stdout, stderr)."""
        if self._is_ssh:
            ssh = self._ssh_client()
            stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            return (
                exit_code,
                stdout.read().decode("utf-8", errors="ignore"),
                stderr.read().decode("utf-8", errors="ignore"),
            )
        session = self._winrm_session()
        r = session.run_cmd(command, timeout=timeout)
        return (
            r.status_code,
            r.std_out.decode("utf-8", errors="ignore"),
            r.std_err.decode("utf-8", errors="ignore"),
        )

    def run_ps(self, script: str, timeout: int = 60) -> Tuple[int, str, str]:
        """Execute PowerShell script."""
        if self._is_ssh:
            encoded = _encode_ps_command(script)
            return self.run_cmd(f"powershell -NoProfile -EncodedCommand {encoded}", timeout)
        session = self._winrm_session()
        r = session.run_ps(script)
        return (
            r.status_code,
            r.std_out.decode("utf-8", errors="ignore"),
            r.std_err.decode("utf-8", errors="ignore"),
        )

    def upload(self, local_path: str, remote_path: str) -> int:
        """Upload a file. Return bytes transferred."""
        if self._is_ssh:
            sftp = self._ssh_client().open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            return Path(local_path).stat().st_size

        # WinRM 路径
        file_size = Path(local_path).stat().st_size
        if file_size > WINRM_MAX_FILE_SIZE:
            raise RuntimeError(
                f"File too large for WinRM transfer ({file_size} bytes > 1MB). "
                "Use SSH (agentwin auth --port 22) or SMB for large files."
            )

        session = self._winrm_session()
        with open(local_path, "rb") as f:
            data = f.read()

        b64 = base64.b64encode(data).decode()
        # pywinrm 的 run_ps() 内部用 powershell -encodedcommand，
        # 受 Windows 命令行 8191 字符限制。
        # 脚本经 UTF-16LE 编码后 base64（约 2x 膨胀），
        # 每块 2500 base64 字符（约 1875 字节原始数据）安全。
        chunk_size = 2500
        temp_b64 = f"{remote_path}.b64"
        total_chunks = (len(b64) + chunk_size - 1) // chunk_size

        for i in range(0, len(b64), chunk_size):
            chunk = b64[i : i + chunk_size]
            chunk_num = i // chunk_size
            if chunk_num == 0:
                ps = f"[IO.File]::WriteAllText('{temp_b64}', '{chunk}')"
            else:
                ps = f"[IO.File]::AppendAllText('{temp_b64}', '{chunk}')"
            r = session.run_ps(ps)
            if r.status_code != 0:
                err = r.std_err.decode("utf-8", errors="ignore").strip()
                raise RuntimeError(
                    f"Upload failed at chunk {chunk_num}/{total_chunks}: {err or 'unknown error'}"
                )

        # 所有块上传完成后，将 base64 文件解码为目标文件
        ps = (
            f"$b64 = [IO.File]::ReadAllText('{temp_b64}'); "
            f"$bytes = [Convert]::FromBase64String($b64); "
            f"[IO.File]::WriteAllBytes('{remote_path}', $bytes); "
            f"Remove-Item '{temp_b64}'"
        )
        r = session.run_ps(ps)
        if r.status_code != 0:
            err = r.std_err.decode("utf-8", errors="ignore").strip()
            raise RuntimeError(f"Upload finalize failed: {err or 'unknown error'}")
        return len(data)

    def download(self, remote_path: str, local_path: str) -> int:
        """Download a file. Return bytes transferred."""
        if self._is_ssh:
            sftp = self._ssh_client().open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            return Path(local_path).stat().st_size

        # WinRM 路径：先检查远程文件大小
        session = self._winrm_session()
        r = session.run_ps(f"(Get-Item '{remote_path}').Length")
        if r.status_code != 0:
            raise RuntimeError(f"Failed to check remote file: {r.std_err.decode()}")
        try:
            file_size = int(r.std_out.decode().strip())
        except ValueError:
            raise RuntimeError(f"Failed to parse remote file size from: {r.std_out.decode()[:200]}")

        if file_size > WINRM_MAX_FILE_SIZE:
            raise RuntimeError(
                f"File too large for WinRM transfer ({file_size} bytes > 1MB). "
                "Use SSH (agentwin auth --port 22) or SMB for large files."
            )

        ps = f"[Convert]::ToBase64String([IO.File]::ReadAllBytes('{remote_path}'))"
        r = session.run_ps(ps)
        if r.status_code != 0:
            raise RuntimeError(f"Download failed: {r.std_err.decode()}")

        data = base64.b64decode(r.std_out.decode().strip())
        Path(local_path).write_bytes(data)
        return len(data)

    def close(self):
        """Close any open connections."""
        if self._ssh:
            self._ssh.close()
