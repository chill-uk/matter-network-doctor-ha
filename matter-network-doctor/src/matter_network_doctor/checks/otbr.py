from __future__ import annotations

from matter_network_doctor.checks.common import resolve_host, tcp_probe
from matter_network_doctor.models import CheckResult, Status


TARGETS = [
    ("homeassistant.local", 8081),
    ("core-openthread-border-router", 8081),
    ("otbr", 8081),
    ("localhost", 8081),
]


def run(discovered: dict[str, list[dict]] | None = None) -> list[CheckResult]:
    probes = []
    reachable = []
    for host, port in TARGETS:
        addresses = resolve_host(host)
        ok, detail = tcp_probe(host, port)
        item = {"host": host, "port": port, "addresses": addresses, "reachable": ok, "detail": detail}
        probes.append(item)
        if ok:
            reachable.append(item)

    meshcop = (discovered or {}).get("_meshcop._udp.local.", [])
    return [
        CheckResult(
            id="otbr.reachability",
            title="OpenThread Border Router reachability",
            status=Status.PASS if reachable else Status.INFO,
            summary=(
                f"OTBR endpoint appears reachable on {len(reachable)} common target{'s' if len(reachable) != 1 else ''}."
                if reachable
                else "OTBR web/API endpoint was not detected on common targets."
            ),
            details={"targets": probes},
            suggestions=[] if reachable else ["Rely on _meshcop._udp.local discovery if the OTBR endpoint is not exposed."],
        ),
        CheckResult(
            id="otbr.mdns",
            title="OTBR mDNS discovery",
            status=Status.PASS if meshcop else Status.INFO,
            summary="Thread Border Router service discovered through mDNS." if meshcop else "No Thread Border Router service discovered through mDNS.",
            details={"services": meshcop},
        ),
    ]

