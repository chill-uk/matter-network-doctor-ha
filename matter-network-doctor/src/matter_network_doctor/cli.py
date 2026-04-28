from __future__ import annotations

import typer
from rich.console import Console

from matter_network_doctor.report import render_report, report_json
from matter_network_doctor.scanner import scan as run_scan
from matter_network_doctor.scanner import scan_ha, scan_ipv6, scan_mdns

app = typer.Typer(help="Inspect local Matter and Thread network readiness.")
console = Console()


def _emit(report, json_output: bool) -> None:
    if json_output:
        typer.echo(report_json(report))
    else:
        render_report(report, console=console)


@app.command()
def scan(
    json_output: bool = typer.Option(False, "--json", help="Output the complete report as JSON."),
    verbose: bool = typer.Option(False, "--verbose", help="Include more raw command output in report details."),
    mdns_timeout: float = typer.Option(4.0, "--mdns-timeout", help="Seconds to wait for mDNS responses."),
) -> None:
    """Run the full diagnostic scan."""
    _emit(run_scan(verbose=verbose, mdns_timeout=mdns_timeout), json_output)


@app.command()
def ipv6(
    json_output: bool = typer.Option(False, "--json", help="Output the complete report as JSON."),
    verbose: bool = typer.Option(False, "--verbose", help="Include more raw command output in report details."),
) -> None:
    """Run IPv6 diagnostics."""
    _emit(scan_ipv6(verbose=verbose), json_output)


@app.command()
def mdns(
    json_output: bool = typer.Option(False, "--json", help="Output the complete report as JSON."),
    mdns_timeout: float = typer.Option(4.0, "--mdns-timeout", help="Seconds to wait for mDNS responses."),
) -> None:
    """Run mDNS, Matter discovery, and Thread discovery diagnostics."""
    _emit(scan_mdns(mdns_timeout=mdns_timeout), json_output)


@app.command()
def ha(
    json_output: bool = typer.Option(False, "--json", help="Output the complete report as JSON."),
    mdns_timeout: float = typer.Option(4.0, "--mdns-timeout", help="Seconds to wait for mDNS responses."),
) -> None:
    """Run Home Assistant, Matter Server, and OTBR reachability diagnostics."""
    _emit(scan_ha(mdns_timeout=mdns_timeout), json_output)


if __name__ == "__main__":
    app()
