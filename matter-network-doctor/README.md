# Matter Network Doctor Home Assistant Add-on Repository

This repository contains the Matter Network Doctor Home Assistant add-on.

To install it in Home Assistant:

1. Open **Settings**.
2. Open **Add-ons**.
3. Open the **Add-on Store**.
4. Open the three-dot menu and choose **Repositories**.
5. Add this repository URL:

```text
https://github.com/chill-uk/matter-network-doctor-ha
```

The add-on folder is [matter-network-doctor](matter-network-doctor/config.yaml).

## Matter Network Doctor

Matter Network Doctor is a local, read-only diagnostic tool for checking whether a Home Assistant environment appears ready for Matter and Thread discovery.

It is designed as a Home Assistant add-on first. The scanner runs from inside the smart-home network so it can inspect IPv6, multicast, mDNS, Matter service discovery, Thread Border Router discovery, and common Home Assistant add-on endpoints.

## What It Checks

- System context: hostname, interfaces, IP addresses, routes, and whether host networking appears available.
- IPv6: link-local addresses, non-link-local addresses, default route, neighbor table, forwarding, and ULA visibility.
- Multicast: IPv4 and IPv6 multicast memberships, including common mDNS groups.
- mDNS: `_matter._tcp.local.`, `_meshcop._udp.local.`, `_home-assistant._tcp.local.`, and `_http._tcp.local.`.
- Matter discovery: local Matter services advertised through mDNS.
- Thread discovery: Thread Border Routers advertised through `_meshcop._udp.local.`.
- Home Assistant reachability: `homeassistant.local`, port `8123`, and Supervisor API presence when exposed.
- Matter Server reachability: best-effort probes for common port `5580` targets.
- OpenThread Border Router reachability: best-effort probes for common port `8081` targets.

## What It Cannot Prove

This tool does not certify Matter compatibility. It cannot prove that every router, VLAN, firewall rule, Thread dataset, controller, or device is configured correctly.

Instead, it reports what the add-on can observe from its own runtime environment. A result such as "no Matter services discovered" may be normal if no commissioned Matter devices are currently advertising, or it may point to a multicast/mDNS problem.

## Why It Runs Locally

Browser-only tools cannot reliably inspect local IPv6 routing, multicast memberships, mDNS service discovery, Thread Border Router advertisements, or Home Assistant add-on reachability. Running locally inside Home Assistant gives the scanner visibility from the same environment many users rely on for Matter and Thread.

## Why Host Networking Helps

Matter and Thread diagnostics depend heavily on local multicast and mDNS. Home Assistant add-ons running with `host_network: true` are much more likely to see the same local network advertisements as Home Assistant itself.

The add-on uses host networking by default. It is still read-only and does not modify network settings.

## Privacy

Matter Network Doctor is local-only by default:

- No cloud uploads
- No telemetry
- No external API calls
- No automatic sharing
- No credentials required for the MVP
- No commissioning or device control
- No Thread dataset changes
- No Home Assistant configuration changes

## Running The Scanner Locally

The Python package lives inside the add-on folder. To run it outside Home Assistant for development:

```bash
cd matter-network-doctor
python -m pip install -e .
```

Run a readable scan:

```bash
matter-network-doctor scan
```

Run a JSON scan:

```bash
matter-network-doctor scan --json
```

Run focused checks:

```bash
matter-network-doctor ipv6
matter-network-doctor mdns
matter-network-doctor ha
```

## Home Assistant Add-on

The add-on lives in `matter-network-doctor/`. That folder is self-contained so it can be copied into a local Home Assistant add-ons directory for testing.

For local Docker testing of the add-on image:

```bash
docker build matter-network-doctor
```

The default add-on command runs:

```bash
matter-network-doctor scan
```

The first version outputs the report to Home Assistant add-on logs.
