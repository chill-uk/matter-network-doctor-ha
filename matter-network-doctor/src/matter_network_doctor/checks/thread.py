from __future__ import annotations

from matter_network_doctor.models import CheckResult, Status


SERVICE_TYPE = "_meshcop._udp.local."


def run(discovered: dict[str, list[dict]] | None = None) -> list[CheckResult]:
    services = (discovered or {}).get(SERVICE_TYPE, [])
    count = len(services)
    status = Status.PASS if count == 1 else Status.WARN if count > 1 else Status.WARN
    suggestions: list[str] = []
    if count == 0:
        suggestions.append("If you expect Thread support, check that an OpenThread Border Router is running and advertising _meshcop._udp.local.")
    if count > 1:
        suggestions.append("Multiple Thread Border Routers can be normal, but commissioning problems may indicate mismatched Thread datasets.")

    return [
        CheckResult(
            id="thread.border_router_discovery",
            title="Thread Border Router discovery",
            status=status,
            summary=(
                f"Found {count} Thread Border Router service{'s' if count != 1 else ''} via mDNS."
                if count
                else "No Thread Border Router services discovered via mDNS."
            ),
            details={"service_type": SERVICE_TYPE, "count": count, "services": services},
            suggestions=suggestions,
        )
    ]

