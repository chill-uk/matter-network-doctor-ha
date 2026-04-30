from __future__ import annotations

from datetime import datetime, timezone

from matter_network_doctor import __version__
from matter_network_doctor.checks import (
    homeassistant,
    ipv6,
    matter,
    matter_server,
    mdns,
    multicast,
    otbr,
    system,
    thread,
)
from matter_network_doctor.models import CheckResult, DiagnosticReport, Status


def _discover_mdns(mdns_timeout: float) -> tuple[dict[str, list[dict]], str | None]:
    try:
        return mdns.discover_services(timeout=mdns_timeout), None
    except Exception as exc:
        return {service_type: [] for service_type in mdns.DEFAULT_SERVICE_TYPES}, str(exc)


def _summary(sections: dict[str, list[CheckResult]]) -> list[CheckResult]:
    flat = [result for name, results in sections.items() if name not in {"Summary", "Suggestions"} for result in results]
    counts = {status.value: sum(1 for result in flat if result.status == status) for status in Status}
    if counts["fail"]:
        status = Status.FAIL
        text = "Your Home Assistant environment has issues that may affect Matter or Thread discovery."
    elif counts["warn"]:
        status = Status.WARN
        text = "Your Home Assistant environment shows partial Matter/Thread readiness."
    else:
        status = Status.PASS
        text = "Your Home Assistant environment appears ready for Matter discovery."

    return [
        CheckResult(
            id="summary.overall",
            title="Overall result",
            status=status,
            summary=text,
            details={"counts": counts},
            suggestions=["Review warnings before troubleshooting device commissioning."] if counts["warn"] or counts["fail"] else [],
        )
    ]


def _suggestions(sections: dict[str, list[CheckResult]]) -> list[CheckResult]:
    suggestions: list[str] = []
    for name, results in sections.items():
        if name in {"Summary", "Suggestions"}:
            continue
        for result in results:
            suggestions.extend(result.suggestions)

    deduped = list(dict.fromkeys(suggestions))
    has_thread_network = any(
        result.id.startswith("thread.mdns_network.") or result.id == "otbr.node_status" and result.status == Status.PASS
        for result in sections.get("Thread Discovery", []) + sections.get("OpenThread Border Router", [])
    )
    if has_thread_network:
        deduped = [
            suggestion
            for suggestion in deduped
            if "add-on token" not in suggestion and "Home Assistant API access" not in suggestion and "homeassistant_api" not in suggestion
        ]
    if not deduped:
        deduped = ["No specific suggestions generated."]

    return [
        CheckResult(
            id="suggestions.generated",
            title="Suggestions",
            status=Status.INFO,
            summary=f"Generated {len(deduped)} suggestion{'s' if len(deduped) != 1 else ''}.",
            details={"suggestions": deduped},
        )
    ]


def scan(verbose: bool = False, mdns_timeout: float = 4.0) -> DiagnosticReport:
    discovered, mdns_error = _discover_mdns(mdns_timeout)
    sections: dict[str, list[CheckResult]] = {
        "System": system.run(verbose=verbose),
        "IPv6": ipv6.run(verbose=verbose),
        "Multicast": multicast.run(verbose=verbose),
        "mDNS": mdns.run(discovered=discovered, error=mdns_error),
        "Matter Discovery": matter.run(discovered=discovered),
        "Thread Discovery": thread.run(discovered=discovered),
        "Home Assistant": homeassistant.run(discovered=discovered),
        "Matter Server": matter_server.run(),
        "OpenThread Border Router": otbr.run(discovered=discovered),
    }
    sections["Summary"] = _summary(sections)
    sections["Suggestions"] = _suggestions(sections)
    return DiagnosticReport(
        version=__version__,
        generated_at=datetime.now(timezone.utc).isoformat(),
        sections=sections,
    )


def scan_ipv6(verbose: bool = False) -> DiagnosticReport:
    sections = {"IPv6": ipv6.run(verbose=verbose)}
    sections["Summary"] = _summary(sections)
    sections["Suggestions"] = _suggestions(sections)
    return DiagnosticReport(version=__version__, generated_at=datetime.now(timezone.utc).isoformat(), sections=sections)


def scan_mdns(mdns_timeout: float = 4.0) -> DiagnosticReport:
    discovered, mdns_error = _discover_mdns(mdns_timeout)
    sections = {
        "mDNS": mdns.run(discovered=discovered, error=mdns_error),
        "Matter Discovery": matter.run(discovered=discovered),
        "Thread Discovery": thread.run(discovered=discovered),
    }
    sections["Summary"] = _summary(sections)
    sections["Suggestions"] = _suggestions(sections)
    return DiagnosticReport(version=__version__, generated_at=datetime.now(timezone.utc).isoformat(), sections=sections)


def scan_ha(mdns_timeout: float = 4.0) -> DiagnosticReport:
    discovered, _mdns_error = _discover_mdns(mdns_timeout)
    sections = {
        "Home Assistant": homeassistant.run(discovered=discovered),
        "Matter Server": matter_server.run(),
        "OpenThread Border Router": otbr.run(discovered=discovered),
    }
    sections["Summary"] = _summary(sections)
    sections["Suggestions"] = _suggestions(sections)
    return DiagnosticReport(version=__version__, generated_at=datetime.now(timezone.utc).isoformat(), sections=sections)
