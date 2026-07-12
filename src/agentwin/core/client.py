"""WinRM + SSH dual-protocol client."""
from pathlib import Path
from typing import Tuple

import paramiko
import winrm

from agentwin.core.auth import HostCredential
from agentwin.core.crypto import decrypt


class RemoteClient:
    """Unified remote execution client."""

    def __init__(self, cred: HostCredential):
        self.cred = cred
        self._winrm = None
        self._ssh = None

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
        if self.cred.auth_method == "winrm-password":
            session = self._winrm_session()
            r = session.run_cmd(command)
            return (
                r.status_code,
                r.std_out.decode("utf-8", errors="ignore"),
                r.std_err.decode("utf-8", errors="ignore"),
            )
        else:
            ssh = self._ssh_client()
            stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            return (
                exit_code,
                stdout.read().decode("utf-8", errors="ignore"),
                stderr.read().decode("utf-8", errors="ignore"),
            )

    def run_ps(self, script: str, timeout: int = 60) -> Tuple[int, str, str]:
        """Execute PowerShell script via WinRM."""
        if self.cred.auth_method == "winrm-password":
            session = self._winrm_session()
            r = session.run_ps(script)
            return (
                r.status_code,
                r.std_out.decode("utf-8", errors="ignore"),
                r.std_err.decode("utf-8", errors="ignore"),
            )
        # SSH 上跑 powershell.exe
        return self.run_cmd(f'powershell -NoProfile -Command "{script}"', timeout)

    def upload(self, local_path: str, remote_path: str) -> int:
        """Upload a file. Return bytes transferred."""
        if self.cred.auth_method == "winrm-password":
            session = self._winrm_session()
            with open(local_path, "rb") as f:
                data = f.read()
            # 用 base64 编码后通过 PS 写文件
            import base64

            b64 = base64.b64encode(data).decode()
            ps = (
                f"$b64 = '{b64}'; "
                f"$bytes = [Convert]::FromBase64String($b64); "
                f"[IO.File]::WriteAllBytes('{remote_path}', $bytes)"
            )
            r = session.run_ps(ps)
            if r.status_code != 0:
                raise RuntimeError(f"Upload failed: {r.std_err.decode()}")
            return len(data)
        else:
            sftp = self._ssh_client().open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            return Path(local_path).stat().st_size

    def download(self, remote_path: str, local_path: str) -> int:
        """Download a file. Return bytes transferred."""
        if self.cred.auth_method == "winrm-password":
            session = self._winrm_session()
            ps = f"[Convert]::ToBase64String([IO.File]::ReadAllBytes('{remote_path}'))"
            r = session.run_ps(ps)
            if r.status_code != 0:
                raise RuntimeError(f"Download failed: {r.std_err.decode()}")
            import base64

            data = base64.b64decode(r.std_out.decode().strip())
            Path(local_path).write_bytes(data)
            return len(data)
        else:
            sftp = self._ssh_client().open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            return Path(local_path).stat().st_size

    def close(self):
        """Close any open connections."""
        if self._ssh:
            self._ssh.close()
