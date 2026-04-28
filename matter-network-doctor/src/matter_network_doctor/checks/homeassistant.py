from __future__ import annotations

import os

import httpx

from matter_network_doctor.checks.common import resolve_host
from matter_network_doctor.models import CheckResult, Status


def _http_probe(url: str, headers: dict[str, str] | None = None) -> tuple[bool, str | int]:
    try:
        with httpx.Client(timeout=2.0, follow_redirects=False) as client:
            response = client.get(url, headers=headers)
            return response.status_code < 500, response.status_code
    except httpx.HTTPError as exc:
        return False, str(exc)


def run(discovered: dict[str, list[dict]] | None = None) -> list[CheckResult]:
    addresses = resolve_host("homeassistant.local")
    ha_reachable, ha_detail = _http_probe("http://homeassistant.local:8123")

    supervisor_token = os.environ.get("SUPERVISOR_TOKEN") or os.environ.get("HASSIO_TOKEN")
    supervisor_status: Status = Status.SKIP
    supervisor_summary = "Supervisor API probe skipped because no add-on token is available."
    supervisor_details: dict[str, str | int | bool] = {"token_available": False}
    if supervisor_token:
        ok, detail = _http_probe(
            "http://supervisor/core/info",
            headers={"Authorization": f"Bearer {supervisor_token}"},
        )
        supervisor_status = Status.PASS if ok else Status.WARN
        supervisor_summary = "Supervisor API is reachable." if ok else "Supervisor API was not reachable."
        supervisor_details = {"token_available": True, "result": detail}

    ha_mdns = (discovered or {}).get("_home-assistant._tcp.local.", [])

    return [
        CheckResult(
            id="ha.resolve",
            title="Resolve homeassistant.local",
            status=Status.PASS if addresses else Status.WARN,
            summary="homeassistant.local resolved." if addresses else "homeassistant.local did not resolve.",
            details={"addresses": addresses},
            suggestions=[] if addresses else ["Check local DNS/mDNS resolution from the add-on environment."],
        ),
        CheckResult(
            id="ha.http",
            title="Home Assistant HTTP reachability",
            status=Status.PASS if ha_reachable else Status.WARN,
            summary="Home Assistant HTTP endpoint is reachable." if ha_reachable else "Home Assistant HTTP endpoint was not reachable.",
            details={"url": "http://homeassistant.local:8123", "result": ha_detail},
            suggestions=[] if ha_reachable else ["This may be normal if Home Assistant uses a different hostname or network namespace."],
        ),
        CheckResult(
            id="ha.supervisor",
            title="Supervisor API reachability",
            status=supervisor_status,
            summary=supervisor_summary,
            details=supervisor_details,
        ),
        CheckResult(
            id="ha.mdns",
            title="Home Assistant mDNS discovery",
            status=Status.PASS if ha_mdns else Status.INFO,
            summary="Home Assistant was discovered via mDNS." if ha_mdns else "Home Assistant was not discovered via mDNS.",
            details={"services": ha_mdns},
        ),
    ]

