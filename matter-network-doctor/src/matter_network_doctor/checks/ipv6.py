from __future__ import annotations

import re

from matter_network_doctor.checks.common import compact_output, run_command
from matter_network_doctor.models import CheckResult, Status


IPV6_RE = re.compile(r"inet6\s+([0-9a-fA-F:]+)")


def _ipv6_addresses(output: str) -> list[str]:
    return IPV6_RE.findall(output)


def run(verbose: bool = False) -> list[CheckResult]:
    results: list[CheckResult] = []
    addr = run_command(["ip", "-6", "addr"])
    route = run_command(["ip", "-6", "route"])
    neigh = run_command(["ip", "-6", "neigh"])
    disabled = run_command(["sysctl", "-n", "net.ipv6.conf.all.disable_ipv6"])
    forwarding = run_command(["sysctl", "-n", "net.ipv6.conf.all.forwarding"])

    addresses = _ipv6_addresses(addr.stdout)
    link_local = [ip for ip in addresses if ip.lower().startswith("fe80")]
    non_link_local = [ip for ip in addresses if not ip.lower().startswith(("fe80", "::1"))]
    ula = [ip for ip in addresses if ip.lower().startswith(("fc", "fd"))]
    default_route = any(line.startswith("default") for line in route.stdout.splitlines())

    if disabled.ok:
        enabled_status = Status.PASS if disabled.stdout.strip() == "0" else Status.WARN
        enabled_summary = "IPv6 appears enabled." if disabled.stdout.strip() == "0" else "IPv6 may be disabled."
        enabled_suggestions = [] if disabled.stdout.strip() == "0" else ["Matter uses IPv6 locally; check host IPv6 settings."]
    else:
        enabled_status = Status.SKIP
        enabled_summary = "IPv6 enabled sysctl could not be read in this environment."
        enabled_suggestions = []

    results.append(
        CheckResult(
            id="ipv6.enabled",
            title="IPv6 enabled",
            status=enabled_status,
            summary=enabled_summary,
            details={"sysctl": disabled.stdout.strip(), "error": disabled.stderr},
            suggestions=enabled_suggestions,
        )
    )
    results.append(
        CheckResult(
            id="ipv6.link_local",
            title="Link-local IPv6 address",
            status=Status.PASS if link_local else Status.WARN if addr.ok else Status.SKIP,
            summary=(
                "Link-local IPv6 address detected."
                if link_local
                else "No link-local IPv6 address detected."
                if addr.ok
                else "IPv6 address command could not be read in this environment."
            ),
            details={"addresses": link_local},
            suggestions=[] if link_local or not addr.ok else ["Check whether IPv6 is enabled on the Home Assistant network interface."],
        )
    )
    results.append(
        CheckResult(
            id="ipv6.non_link_local",
            title="Non-link-local IPv6 address",
            status=Status.PASS if non_link_local else Status.WARN,
            summary=(
                "Non-link-local IPv6 address detected."
                if non_link_local
                else "No non-link-local IPv6 address detected."
            ),
            details={"addresses": non_link_local},
            suggestions=[] if non_link_local else ["This can be normal, but ULA or global IPv6 can help some Matter environments."],
        )
    )
    results.append(
        CheckResult(
            id="ipv6.default_route",
            title="IPv6 default route",
            status=Status.INFO if not default_route else Status.PASS,
            summary="IPv6 default route found." if default_route else "No IPv6 default route found.",
            details={"routes": compact_output(route.stdout.splitlines()) if verbose else {"present": default_route}},
            suggestions=[],
        )
    )
    results.append(
        CheckResult(
            id="ipv6.neighbors",
            title="IPv6 neighbor table",
            status=Status.PASS if neigh.ok else Status.WARN,
            summary="IPv6 neighbor table is readable." if neigh.ok else "IPv6 neighbor table is not readable.",
            details={"neighbors": compact_output(neigh.stdout.splitlines()) if verbose else {"readable": neigh.ok}},
            suggestions=[] if neigh.ok else ["Check container permissions or iproute2 availability."],
        )
    )
    results.append(
        CheckResult(
            id="ipv6.ula",
            title="ULA prefix visibility",
            status=Status.INFO if not ula else Status.PASS,
            summary="ULA address detected." if ula else "No ULA address detected.",
            details={"addresses": ula},
            suggestions=[],
        )
    )
    results.append(
        CheckResult(
            id="ipv6.forwarding",
            title="IPv6 forwarding",
            status=Status.INFO,
            summary=f"IPv6 forwarding sysctl is {forwarding.stdout.strip() or 'unknown'}.",
            details={"sysctl": forwarding.stdout.strip(), "error": forwarding.stderr},
        )
    )

    return results
