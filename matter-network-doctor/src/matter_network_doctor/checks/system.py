from __future__ import annotations

import os
import socket

import psutil

from matter_network_doctor.checks.common import compact_output, run_command
from matter_network_doctor.models import CheckResult, Status


def run(verbose: bool = False) -> list[CheckResult]:
    results: list[CheckResult] = []
    hostname = socket.gethostname()
    interfaces = {
        name: [addr.address for addr in addrs]
        for name, addrs in psutil.net_if_addrs().items()
    }

    results.append(
        CheckResult(
            id="system.context",
            title="Runtime context collected",
            status=Status.INFO,
            summary=f"Running on hostname {hostname} with {len(interfaces)} detected interfaces.",
            details={
                "hostname": hostname,
                "interfaces": interfaces,
                "container": {
                    "supervisor_token_present": bool(os.environ.get("SUPERVISOR_TOKEN")),
                    "homeassistant_token_present": bool(os.environ.get("HASSIO_TOKEN")),
                },
            },
        )
    )

    ip_addr = run_command(["ip", "addr"])
    ip_route = run_command(["ip", "route"])
    ip6_route = run_command(["ip", "-6", "route"])

    command_details = {
        "ip_addr": compact_output(ip_addr.stdout.splitlines()) if ip_addr.stdout else [],
        "ip_route": compact_output(ip_route.stdout.splitlines()) if ip_route.stdout else [],
        "ip6_route": compact_output(ip6_route.stdout.splitlines()) if ip6_route.stdout else [],
    }

    if all(result.ok for result in (ip_addr, ip_route, ip6_route)):
        status = Status.PASS
        summary = "Network interface and route commands are readable."
    else:
        status = Status.WARN
        summary = "Some network interface or route commands were not readable."

    results.append(
        CheckResult(
            id="system.network_commands",
            title="Network command access",
            status=status,
            summary=summary,
            details=command_details if verbose else {"commands_checked": ["ip addr", "ip route", "ip -6 route"]},
            suggestions=[] if status == Status.PASS else ["Install iproute2 in the container or check add-on permissions."],
        )
    )

    route_text = ip_route.stdout + "\n" + ip6_route.stdout
    host_like = "docker0" in route_text or "hassio" in route_text or "br-" in route_text
    results.append(
        CheckResult(
            id="system.host_network",
            title="Host networking visibility",
            status=Status.INFO,
            summary=(
                "Host networking appears plausible from available routes."
                if host_like
                else "Host networking could not be confirmed from route output."
            ),
            details={"heuristic_matched": host_like},
            suggestions=[] if host_like else ["For better mDNS and multicast diagnostics, run the add-on with host_network enabled."],
        )
    )

    return results

