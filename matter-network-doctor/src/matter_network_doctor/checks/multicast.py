from __future__ import annotations

from matter_network_doctor.checks.common import compact_output, run_command
from matter_network_doctor.models import CheckResult, Status


def run(verbose: bool = False) -> list[CheckResult]:
    ipv4 = run_command(["ip", "maddr"])
    ipv6 = run_command(["ip", "-6", "maddr"])
    combined = f"{ipv4.stdout}\n{ipv6.stdout}".lower()

    results = [
        CheckResult(
            id="multicast.ipv4_memberships",
            title="IPv4 multicast memberships",
            status=Status.PASS if ipv4.ok else Status.WARN,
            summary="IPv4 multicast memberships are readable." if ipv4.ok else "IPv4 multicast memberships are not readable.",
            details={"memberships": compact_output(ipv4.stdout.splitlines()) if verbose else {"readable": ipv4.ok}},
            suggestions=[] if ipv4.ok else ["Install iproute2 in the container or check add-on permissions."],
        ),
        CheckResult(
            id="multicast.ipv6_memberships",
            title="IPv6 multicast memberships",
            status=Status.PASS if ipv6.ok else Status.WARN,
            summary="IPv6 multicast memberships are readable." if ipv6.ok else "IPv6 multicast memberships are not readable.",
            details={"memberships": compact_output(ipv6.stdout.splitlines()) if verbose else {"readable": ipv6.ok}},
            suggestions=[] if ipv6.ok else ["Install iproute2 in the container or check add-on permissions."],
        ),
        CheckResult(
            id="multicast.mdns_ipv4",
            title="mDNS IPv4 multicast group",
            status=Status.INFO if "224.0.0.251" in combined else Status.WARN,
            summary=(
                "mDNS IPv4 multicast group 224.0.0.251 is visible."
                if "224.0.0.251" in combined
                else "mDNS IPv4 multicast group 224.0.0.251 was not visible."
            ),
            details={"group": "224.0.0.251", "visible": "224.0.0.251" in combined},
        ),
        CheckResult(
            id="multicast.mdns_ipv6",
            title="mDNS IPv6 multicast group",
            status=Status.INFO if "ff02::fb" in combined else Status.WARN,
            summary=(
                "mDNS IPv6 multicast group ff02::fb is visible."
                if "ff02::fb" in combined
                else "mDNS IPv6 multicast group ff02::fb was not visible."
            ),
            details={"group": "ff02::fb", "visible": "ff02::fb" in combined},
        ),
    ]
    return results

