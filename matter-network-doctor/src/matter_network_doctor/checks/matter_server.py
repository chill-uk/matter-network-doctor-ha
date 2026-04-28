from __future__ import annotations

from matter_network_doctor.checks.common import resolve_host, tcp_probe
from matter_network_doctor.models import CheckResult, Status


TARGETS = [
    ("homeassistant.local", 5580),
    ("matter-server", 5580),
    ("core-matter-server", 5580),
    ("localhost", 5580),
]


def run() -> list[CheckResult]:
    probes = []
    reachable = []
    for host, port in TARGETS:
        addresses = resolve_host(host)
        ok, detail = tcp_probe(host, port)
        item = {"host": host, "port": port, "addresses": addresses, "reachable": ok, "detail": detail}
        probes.append(item)
        if ok:
            reachable.append(item)

    return [
        CheckResult(
            id="matter_server.reachability",
            title="Matter Server reachability",
            status=Status.PASS if reachable else Status.INFO,
            summary=(
                f"Matter Server appears reachable on {len(reachable)} common target{'s' if len(reachable) != 1 else ''}."
                if reachable
                else "Matter Server was not detected on common targets."
            ),
            details={"targets": probes},
            suggestions=[] if reachable else [
                "This does not necessarily mean Matter Server is not installed.",
                "The add-on may not be able to see the Matter Server service name from this network namespace.",
            ],
        )
    ]

