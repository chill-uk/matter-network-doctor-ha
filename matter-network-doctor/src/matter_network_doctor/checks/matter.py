from __future__ import annotations

from matter_network_doctor.models import CheckResult, Status


SERVICE_TYPE = "_matter._tcp.local."


def run(discovered: dict[str, list[dict]] | None = None) -> list[CheckResult]:
    services = (discovered or {}).get(SERVICE_TYPE, [])
    count = len(services)
    return [
        CheckResult(
            id="matter.discovery",
            title="Matter service discovery",
            status=Status.PASS if count else Status.WARN,
            summary=(
                f"Found {count} Matter service{'s' if count != 1 else ''} via mDNS."
                if count
                else "No Matter services discovered via mDNS."
            ),
            details={"service_type": SERVICE_TYPE, "count": count, "services": services},
            suggestions=[] if count else [
                "This can be normal if no commissioned Matter devices are advertising.",
                "If commissioning is unreliable, check mDNS and multicast across VLANs and Wi-Fi/Ethernet boundaries.",
            ],
        )
    ]

