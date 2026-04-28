from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

from matter_network_doctor.models import CheckResult, Status


DEFAULT_SERVICE_TYPES = [
    "_matter._tcp.local.",
    "_meshcop._udp.local.",
    "_home-assistant._tcp.local.",
    "_http._tcp.local.",
]


@dataclass
class DiscoveredService:
    service_type: str
    name: str
    hostname: str | None = None
    port: int | None = None
    addresses: list[str] = field(default_factory=list)
    txt: dict[str, str] = field(default_factory=dict)


class _Listener(ServiceListener):
    def __init__(self, zeroconf: Zeroconf) -> None:
        self.zeroconf = zeroconf
        self.services: dict[tuple[str, str], DiscoveredService] = {}

    def add_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        self._collect(service_type, name)

    def update_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        self._collect(service_type, name)

    def remove_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        return None

    def _collect(self, service_type: str, name: str) -> None:
        info = self.zeroconf.get_service_info(service_type, name, timeout=1500)
        self.services[(service_type, name)] = _service_from_info(service_type, name, info)


def _decode_txt(properties: dict[bytes, bytes | None]) -> dict[str, str]:
    decoded: dict[str, str] = {}
    for key, value in properties.items():
        text_key = key.decode("utf-8", errors="replace")
        if value is None:
            decoded[text_key] = ""
        else:
            decoded[text_key] = value.decode("utf-8", errors="replace")
    return decoded


def _service_from_info(service_type: str, name: str, info: ServiceInfo | None) -> DiscoveredService:
    if info is None:
        return DiscoveredService(service_type=service_type, name=name)
    return DiscoveredService(
        service_type=service_type,
        name=name,
        hostname=info.server,
        port=info.port,
        addresses=info.parsed_addresses(),
        txt=_decode_txt(info.properties),
    )


def discover_services(service_types: list[str] | None = None, timeout: float = 4.0) -> dict[str, list[dict[str, Any]]]:
    types = service_types or DEFAULT_SERVICE_TYPES
    zeroconf = Zeroconf()
    listener = _Listener(zeroconf)
    browsers: list[ServiceBrowser] = []
    try:
        for service_type in types:
            browsers.append(ServiceBrowser(zeroconf, service_type, listener))
        time.sleep(timeout)
        discovered: dict[str, list[dict[str, Any]]] = {service_type: [] for service_type in types}
        for service in listener.services.values():
            discovered.setdefault(service.service_type, []).append(
                {
                    "service_type": service.service_type,
                    "name": service.name,
                    "hostname": service.hostname,
                    "port": service.port,
                    "addresses": service.addresses,
                    "txt": service.txt,
                }
            )
        for services in discovered.values():
            services.sort(key=lambda item: item["name"])
        return discovered
    finally:
        for browser in browsers:
            browser.cancel()
        zeroconf.close()


def run(discovered: dict[str, list[dict[str, Any]]] | None = None, error: str | None = None) -> list[CheckResult]:
    if error:
        return [
            CheckResult(
                id="mdns.discovery",
                title="mDNS discovery",
                status=Status.FAIL,
                summary="mDNS discovery failed.",
                details={"error": error},
                suggestions=["Check whether multicast is available from the add-on network namespace."],
            )
        ]

    try:
        services = discovered if discovered is not None else discover_services()
        total = sum(len(items) for items in services.values())
        status = Status.PASS if total > 0 else Status.WARN
        summary = f"mDNS discovery completed and found {total} relevant services."
        if total == 0:
            summary = "mDNS discovery completed but found no relevant services."
        return [
            CheckResult(
                id="mdns.discovery",
                title="mDNS discovery",
                status=status,
                summary=summary,
                details={"services": services},
                suggestions=[] if total else ["Check host networking, multicast routing, VLAN boundaries, and mDNS reflector settings."],
            ),
            CheckResult(
                id="mdns.homeassistant",
                title="Home Assistant mDNS service",
                status=Status.PASS if services.get("_home-assistant._tcp.local.") else Status.INFO,
                summary=(
                    "Home Assistant service discovered via mDNS."
                    if services.get("_home-assistant._tcp.local.")
                    else "Home Assistant service was not discovered via mDNS."
                ),
                details={"services": services.get("_home-assistant._tcp.local.", [])},
            ),
        ]
    except Exception as exc:
        return [
            CheckResult(
                id="mdns.discovery",
                title="mDNS discovery",
                status=Status.FAIL,
                summary="mDNS discovery failed.",
                details={"error": str(exc)},
                suggestions=["Check whether multicast is available from the add-on network namespace."],
            )
        ]
