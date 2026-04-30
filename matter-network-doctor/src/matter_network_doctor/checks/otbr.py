from __future__ import annotations

from typing import Any

import httpx

from matter_network_doctor.checks.common import resolve_host, tcp_probe
from matter_network_doctor.models import CheckResult, Status


TARGETS = [
    ("homeassistant.local", 8081),
    ("core-openthread-border-router", 8081),
    ("otbr", 8081),
    ("localhost", 8081),
]

STATE_NAMES = {
    0: "disabled",
    1: "detached",
    2: "child",
    3: "router",
    4: "leader",
}


def _base_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def _get_json(client: httpx.Client, base_url: str, path: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = client.get(f"{base_url}{path}")
        if response.status_code == 204:
            return {}, None
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return None, str(exc)
    if isinstance(data, dict):
        return data, None
    return None, f"Unexpected response shape from {path}."


def _get_text(client: httpx.Client, base_url: str, path: str) -> tuple[str | None, str | None]:
    try:
        response = client.get(f"{base_url}{path}")
        if response.status_code == 204:
            return "", None
        response.raise_for_status()
        return response.text.strip(), None
    except httpx.HTTPError as exc:
        return None, str(exc)


def _field(data: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in data:
            return data[name]
    return None


def _state_label(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return STATE_NAMES.get(value, str(value))
    return None


def _summarize_node(data: dict[str, Any]) -> dict[str, Any]:
    leader_data = _field(data, "LeaderData", "leader_data", "leaderData")
    if not isinstance(leader_data, dict):
        leader_data = None

    return {
        "network_name": _field(data, "NetworkName", "network_name", "networkName"),
        "extended_pan_id": _field(data, "ExtPanId", "extended_pan_id", "extPanId"),
        "state": _state_label(_field(data, "State", "state")),
        "rloc16": _field(data, "Rloc16", "rloc16"),
        "rloc_address": _field(data, "RlocAddress", "rloc_address", "rlocAddress"),
        "router_count": _field(data, "NumOfRouter", "num_of_router", "numOfRouter"),
        "leader_data": leader_data,
    }


def _probe_rest_api(reachable_targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    api_results = []
    with httpx.Client(timeout=2.0, follow_redirects=False) as client:
        for target in reachable_targets:
            base_url = _base_url(str(target["host"]), int(target["port"]))
            node, node_error = _get_json(client, base_url, "/node")
            dataset_tlv, dataset_error = _get_text(client, base_url, "/node/active-dataset-tlvs")

            item: dict[str, Any] = {
                "base_url": base_url,
                "node_available": node is not None,
                "node_error": node_error,
                "active_dataset_tlv_available": dataset_tlv is not None and bool(dataset_tlv),
                "active_dataset_tlv_length": len(dataset_tlv) if dataset_tlv else 0,
                "active_dataset_tlv_error": dataset_error,
            }
            if node:
                item["node"] = _summarize_node(node)
            api_results.append(item)
    return api_results


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

    api_results = _probe_rest_api(reachable)
    node_results = [result for result in api_results if result["node_available"]]
    dataset_results = [result for result in api_results if result["active_dataset_tlv_available"]]
    first_node = node_results[0].get("node") if node_results else {}
    network_name = first_node.get("network_name") if isinstance(first_node, dict) else None
    state = first_node.get("state") if isinstance(first_node, dict) else None

    meshcop = (discovered or {}).get("_meshcop._udp.local.", [])
    results = [
        CheckResult(
            id="otbr.reachability",
            title="OpenThread Border Router reachability",
            status=Status.PASS if reachable else Status.INFO,
            summary=(
                f"OTBR endpoint appears reachable on {len(reachable)} common target name{'s' if len(reachable) != 1 else ''}."
                if reachable
                else "OTBR web/API endpoint was not detected on common targets."
            ),
            details={"targets": probes},
            suggestions=[] if reachable else ["Rely on _meshcop._udp.local discovery if the OTBR endpoint is not exposed."],
        ),
        CheckResult(
            id="otbr.rest_api",
            title="OTBR REST API",
            status=Status.PASS if node_results else Status.INFO,
            summary=(
                f"OTBR REST API returned node details from {len(node_results)} target name{'s' if len(node_results) != 1 else ''}."
                if node_results
                else "OTBR REST API node details were not available from common targets."
            ),
            details={"targets": api_results},
            suggestions=[] if node_results else ["The OTBR endpoint may be reachable but not expose the standard /node REST endpoint from this add-on."],
        ),
        CheckResult(
            id="otbr.node_status",
            title="OTBR Thread status",
            status=Status.PASS if network_name or state else Status.INFO,
            summary=(
                f"OTBR reports Thread network {network_name or 'unknown'}"
                + (f" with state {state}." if state else ".")
                if network_name or state
                else "OTBR Thread status was not available through the REST API."
            ),
            details={"node": first_node},
        ),
        CheckResult(
            id="otbr.mdns",
            title="OTBR mDNS discovery",
            status=Status.PASS if meshcop else Status.INFO,
            summary="Thread Border Router service discovered through mDNS." if meshcop else "No Thread Border Router service discovered through mDNS.",
            details={"services": meshcop},
        ),
    ]
    if dataset_results:
        results.insert(
            -1,
            CheckResult(
                id="otbr.active_dataset",
                title="OTBR active dataset",
                status=Status.PASS,
                summary="OTBR active dataset TLV is readable. The TLV value is intentionally not printed because it can contain Thread credentials.",
                details={
                    "available_from": [
                        {
                            "base_url": result["base_url"],
                            "active_dataset_tlv_length": result["active_dataset_tlv_length"],
                        }
                        for result in dataset_results
                    ],
                    "redacted": True,
                },
            ),
        )
    return results
