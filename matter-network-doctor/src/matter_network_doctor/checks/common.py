from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass
from typing import Iterable


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_command(command: list[str], timeout: float = 3.0) -> CommandResult:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout.strip(),
            stderr=completed.stderr.strip(),
        )
    except FileNotFoundError as exc:
        return CommandResult(command=command, returncode=127, stdout="", stderr=str(exc))
    except subprocess.TimeoutExpired:
        return CommandResult(command=command, returncode=124, stdout="", stderr="Command timed out")


def resolve_host(host: str) -> list[str]:
    addresses: set[str] = set()
    try:
        for family, _, _, _, sockaddr in socket.getaddrinfo(host, None):
            if family in (socket.AF_INET, socket.AF_INET6):
                addresses.add(str(sockaddr[0]))
    except socket.gaierror:
        return []
    return sorted(addresses)


def tcp_probe(host: str, port: int, timeout: float = 1.5) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "reachable"
    except OSError as exc:
        return False, str(exc)


def compact_output(lines: Iterable[str], limit: int = 40) -> list[str]:
    output = list(lines)
    if len(output) <= limit:
        return output
    return output[:limit] + [f"... truncated {len(output) - limit} lines ..."]

