"""Port scanning + protocol detection."""
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

# 协议特征端口
PROTOCOL_PORTS = {
    22: "SSH",
    135: "RPC",
    139: "NetBIOS",
    445: "SMB",
    3389: "RDP",
    5985: "WinRM-HTTP",
    5986: "WinRM-HTTPS",
}

DEFAULT_PORTS = sorted(PROTOCOL_PORTS.keys())


def scan_port(host: str, port: int, timeout: float = 1.0) -> Tuple[int, bool, float]:
    """Return (port, is_open, response_time)."""
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return (port, True, time.time() - start)
    except (socket.timeout, OSError):
        return (port, False, time.time() - start)


def scan(host: str, ports: List[int] = None, timeout: float = 1.0) -> List[Dict]:
    """Scan multiple ports in parallel."""
    if ports is None:
        ports = DEFAULT_PORTS
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(scan_port, host, p, timeout): p for p in ports}
        for fut in as_completed(futures):
            port, is_open, rt = fut.result()
            results.append({
                "port": port,
                "protocol": PROTOCOL_PORTS.get(port, "unknown"),
                "open": is_open,
                "response_time_ms": round(rt * 1000, 1),
            })
    results.sort(key=lambda r: r["port"])
    return results


def available_protocols(scan_results: List[Dict]) -> List[str]:
    """Return names of remote-management protocols available."""
    open_ports = {r["port"] for r in scan_results if r["open"]}
    protos = []
    if 5985 in open_ports or 5986 in open_ports:
        protos.append("WinRM")
    if 22 in open_ports:
        protos.append("SSH")
    return protos
