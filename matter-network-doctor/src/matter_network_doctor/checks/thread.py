from __future__ import annotations

import json
import os
from typing import Any

from matter_network_doctor.models import CheckResult, Status


SERVICE_TYPE = "_meshcop._udp.local."
THREAD_DATASETS_COMMAND = "thread/list_datasets"
HA_WEBSOCKET_URL = "ws://supervisor/core/websocket"


def _api_unavailable_suggestion(error: str | None) -> str:
    if error == "No add-on token is available.":
        return "Rebuild/reinstall the add-on after enabling homeassistant_api so Home Assistant injects an add-on token."
    if error and ("Unauthorized" in error or "not authorized" in error or "admin" in error.lower()):
        return "Home Assistant rejected the Thread dataset command; this may require an admin-level token that add-ons cannot always use."
    if error and ("not found" in error.lower() or "unknown command" in error.lower()):
        return "Make sure the Home Assistant Thread integration is loaded and your Home Assistant version supports thread/list_datasets."
    return "Check the Thread integration and Home Assistant Core API access if you expect a preferred network."


def _thread_dataset_result(timeout: float = 4.0) -> tuple[list[dict[str, Any]] | None, str | None]:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        return None, "No add-on token is available."

    try:
        from websocket import WebSocketException, create_connection

        ws = create_connection(HA_WEBSOCKET_URL, timeout=timeout)
        try:
            auth_required = json.loads(ws.recv())
            if auth_required.get("type") != "auth_required":
                return None, f"Unexpected WebSocket greeting: {auth_required.get('type', 'unknown')}"

            ws.send(json.dumps({"type": "auth", "access_token": token}))
            auth_response = json.loads(ws.recv())
            if auth_response.get("type") != "auth_ok":
                return None, f"Home Assistant WebSocket auth failed: {auth_response.get('message', auth_response.get('type', 'unknown'))}"

            ws.send(json.dumps({"id": 1, "type": THREAD_DATASETS_COMMAND}))
            response = json.loads(ws.recv())
        finally:
            ws.close()
    except ImportError as exc:
        return None, str(exc)
    except (OSError, WebSocketException, TimeoutError, json.JSONDecodeError) as exc:
        return None, str(exc)

    if not response.get("success"):
        error = response.get("error") or {}
        message = error.get("message") if isinstance(error, dict) else None
        return None, message or f"{THREAD_DATASETS_COMMAND} was not successful."

    result = response.get("result")
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)], None
    if isinstance(result, dict) and isinstance(result.get("datasets"), list):
        return [item for item in result["datasets"] if isinstance(item, dict)], None
    return None, f"Unexpected {THREAD_DATASETS_COMMAND} result shape."


def _dataset_name(dataset: dict[str, Any]) -> str:
    for key in ("network_name", "name", "networkName"):
        value = dataset.get(key)
        if isinstance(value, str) and value:
            return value
    return "Unnamed Thread network"


def _dataset_id(dataset: dict[str, Any]) -> str | None:
    for key in ("dataset_id", "id", "datasetId"):
        value = dataset.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _is_preferred_dataset(dataset: dict[str, Any]) -> bool:
    for key in ("preferred", "is_preferred", "preferred_network", "isPreferred"):
        if dataset.get(key) is True:
            return True
    return False


def _mdns_thread_networks(services: list[dict]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for service in services:
        txt = service.get("txt") if isinstance(service.get("txt"), dict) else {}
        network_name = txt.get("nn") or "Unknown Thread network"
        extended_pan_id = txt.get("xp")
        key = extended_pan_id or network_name
        entry = grouped.setdefault(
            key,
            {
                "network_name": network_name,
                "extended_pan_id": extended_pan_id,
                "border_routers": [],
            },
        )
        entry["border_routers"].append(
            {
                "service_name": service.get("name"),
                "hostname": service.get("hostname"),
                "port": service.get("port"),
                "addresses": service.get("addresses", []),
                "vendor": txt.get("vn"),
                "model": txt.get("mn"),
            }
        )
    return sorted(grouped.values(), key=lambda item: item["network_name"])


def _dataset_network_rows(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for dataset in datasets:
        rows.append(
            {
                "dataset_id": _dataset_id(dataset),
                "network_name": _dataset_name(dataset),
                "preferred": _is_preferred_dataset(dataset),
                "source": dataset.get("source"),
            }
        )
    return rows


def run(discovered: dict[str, list[dict]] | None = None) -> list[CheckResult]:
    services = (discovered or {}).get(SERVICE_TYPE, [])
    count = len(services)
    status = Status.PASS if count == 1 else Status.WARN if count > 1 else Status.WARN
    suggestions: list[str] = []
    if count == 0:
        suggestions.append("If you expect Thread support, check that an OpenThread Border Router is running and advertising _meshcop._udp.local.")
    if count > 1:
        suggestions.append("Multiple Thread Border Routers can be normal, but commissioning problems may indicate mismatched Thread datasets.")

    results = [
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

    mdns_networks = _mdns_thread_networks(services)
    results.append(
        CheckResult(
            id="thread.mdns_networks",
            title="Advertised Thread networks",
            status=Status.PASS if mdns_networks else Status.INFO,
            summary=(
                f"Found {len(mdns_networks)} advertised Thread network{'s' if len(mdns_networks) != 1 else ''} via mDNS."
                if mdns_networks
                else "No advertised Thread networks found via mDNS."
            ),
            details={"networks": mdns_networks},
            suggestions=[] if mdns_networks else ["Thread networks are usually visible through _meshcop._udp.local when border routers are advertising."],
        )
    )
    for index, network in enumerate(mdns_networks, start=1):
        routers = network["border_routers"]
        results.append(
            CheckResult(
                id=f"thread.mdns_network.{index}",
                title=f"Advertised network: {network['network_name']}",
                status=Status.INFO,
                summary=f"{len(routers)} border router{'s' if len(routers) != 1 else ''} advertising this Thread network.",
                details=network,
            )
        )

    datasets, dataset_error = _thread_dataset_result()
    if datasets is None:
        results.append(
            CheckResult(
                id="thread.ha_datasets",
                title="Home Assistant Thread networks",
                status=Status.SKIP,
                summary=f"Home Assistant Thread dataset list was not available. {dataset_error}",
                details={"command": THREAD_DATASETS_COMMAND, "error": dataset_error},
                suggestions=[_api_unavailable_suggestion(dataset_error)],
            )
        )
        return results

    dataset_rows = _dataset_network_rows(datasets)
    preferred = [row for row in dataset_rows if row["preferred"]]
    if preferred:
        preferred_summary = f"Preferred Thread network: {preferred[0]['network_name']}."
        preferred_status = Status.PASS
        preferred_suggestions: list[str] = []
    else:
        preferred_summary = "No preferred Thread network reported by Home Assistant."
        preferred_status = Status.WARN if dataset_rows else Status.INFO
        preferred_suggestions = ["Set a preferred Thread network in Home Assistant if Matter-over-Thread commissioning should use Home Assistant credentials."]

    results.append(
        CheckResult(
            id="thread.ha_preferred_network",
            title="Preferred Thread network",
            status=preferred_status,
            summary=preferred_summary,
            details={"preferred": preferred, "datasets": dataset_rows},
            suggestions=preferred_suggestions,
        )
    )
    results.append(
        CheckResult(
            id="thread.ha_datasets",
            title="Home Assistant Thread networks",
            status=Status.PASS if dataset_rows else Status.INFO,
            summary=(
                f"Home Assistant reports {len(dataset_rows)} Thread network{'s' if len(dataset_rows) != 1 else ''}."
                if dataset_rows
                else "Home Assistant reports no stored Thread networks."
            ),
            details={"datasets": dataset_rows},
        )
    )
    for index, dataset in enumerate(dataset_rows, start=1):
        marker = "preferred" if dataset["preferred"] else "stored"
        results.append(
            CheckResult(
                id=f"thread.ha_dataset.{index}",
                title=f"HA network: {dataset['network_name']}",
                status=Status.PASS if dataset["preferred"] else Status.INFO,
                summary=f"Home Assistant reports this as a {marker} Thread network.",
                details=dataset,
            )
        )

    return results
