# Matter Network Doctor

Matter Network Doctor is a Home Assistant add-on for people whose Matter or Thread devices are not working and who do not know where to start.

It checks the local network from inside Home Assistant and gives a simple report in the add-on logs. It does not fix settings, change your network, pair devices, or upload anything. It only looks and reports what it can see.

## What This Add-on Does

Matter and Thread problems are often caused by network discovery issues. A device may be powered on and nearby, but Home Assistant still cannot find it because something in the local network is blocking or hiding IPv6, multicast, mDNS, Thread, or the Matter Server.

Matter Network Doctor runs a set of read-only checks from the same Home Assistant environment where many people run their Matter controller, Matter Server, and OpenThread Border Router.

In plain terms, it answers questions like:

- Can Home Assistant see the local Matter services on your network?
- Can Home Assistant see your Thread Border Router?
- Is IPv6 available locally?
- Are multicast and mDNS discovery visible?
- Is the Matter Server reachable?
- Is the OpenThread Border Router reachable?
- Which Thread network name is being advertised, if one is visible?

The goal is not to say "your network is perfect." The goal is to give you and anyone helping you a much better starting point.

## What You Need To Do

1. Install the add-on.
2. Start the add-on.
3. Open the add-on **Logs** tab.
4. Read the **Quick Result** section near the top.
5. If you need help, share the log output with the person helping you.

The report is written to the Home Assistant add-on logs. There is no separate dashboard yet.

## What The Result Means

The log starts with a short **Quick Result** section. This is the part most people should read first.

- **Checks passed** means the add-on saw something useful working.
- **Warnings** means something may need attention.
- **Problems** means something important was not working from the add-on's point of view.
- **Optional checks skipped** usually means an extra check was not available, not necessarily that your network is broken.
- **Detected Thread network** shows the Thread network name if the add-on can see one.
- **What to try next** lists the most useful follow-up steps.

Below the quick result, the add-on prints detailed tables. These are mainly for troubleshooting and support.

## Installation

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

## What It Checks

- System context: hostname, interfaces, IP addresses, routes, and whether host networking appears available.
- IPv6: link-local addresses, non-link-local addresses, default route, neighbor table, forwarding, and ULA visibility.
- Multicast: IPv4 and IPv6 multicast memberships, including common mDNS groups.
- mDNS: `_matter._tcp.local.`, `_meshcop._udp.local.`, `_home-assistant._tcp.local.`, and `_http._tcp.local.`.
- Matter discovery: local Matter services advertised through mDNS.
- Thread discovery: Thread Border Routers and advertised Thread networks through `_meshcop._udp.local.`.
- Home Assistant Thread networks: stored Thread datasets and the preferred Thread network when Home Assistant API access is available.
- Home Assistant reachability: `homeassistant.local`, port `8123`, and Supervisor API presence when exposed.
- Matter Server reachability: best-effort probes for common port `5580` targets.
- OpenThread Border Router reachability: best-effort probes for common port `8081` targets and read-only REST API checks when available.

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
