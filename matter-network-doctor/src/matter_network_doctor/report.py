from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from matter_network_doctor.models import DiagnosticReport, Status


STATUS_STYLE = {
    Status.PASS: "green",
    Status.WARN: "yellow",
    Status.FAIL: "red",
    Status.INFO: "cyan",
    Status.SKIP: "dim",
}


def report_json(report: DiagnosticReport) -> str:
    return report.model_dump_json(indent=2)


def _count_statuses(report: DiagnosticReport) -> dict[Status, int]:
    counts = {status: 0 for status in Status}
    for section, results in report.sections.items():
        if section in {"Summary", "Suggestions"}:
            continue
        for result in results:
            counts[result.status] += 1
    return counts


def _overall_summary(report: DiagnosticReport) -> str:
    results = report.sections.get("Summary", [])
    if results:
        return results[0].summary
    return "Matter Network Doctor completed its checks."


def _suggestion_text(report: DiagnosticReport) -> list[str]:
    results = report.sections.get("Suggestions", [])
    if not results:
        return []
    suggestions = results[0].details.get("suggestions", [])
    return [str(suggestion) for suggestion in suggestions]


def _detected_thread_networks(report: DiagnosticReport) -> list[str]:
    networks = []
    for result in report.sections.get("Thread Discovery", []):
        if result.id.startswith("thread.mdns_network."):
            name = result.title.removeprefix("Advertised network: ").strip()
            if name:
                networks.append(name)
        if result.id.startswith("thread.ha_dataset."):
            name = result.title.removeprefix("HA network: ").strip()
            if name and name not in networks:
                networks.append(name)
    return networks


def _render_user_summary(report: DiagnosticReport, console: Console) -> None:
    counts = _count_statuses(report)
    summary_results = report.sections.get("Summary", [])
    summary_style = STATUS_STYLE[summary_results[0].status] if summary_results else ""
    summary = Text(_overall_summary(report), style=summary_style)
    panel = Text()
    panel.append(summary)
    panel.append("\n\n")
    panel.append(f"Checks passed: {counts[Status.PASS]}", style="green")
    if counts[Status.WARN]:
        panel.append(f"\nWarnings: {counts[Status.WARN]}", style="yellow")
    if counts[Status.FAIL]:
        panel.append(f"\nProblems: {counts[Status.FAIL]}", style="red")
    if counts[Status.SKIP]:
        panel.append(f"\nOptional checks skipped: {counts[Status.SKIP]}", style="dim")

    thread_networks = _detected_thread_networks(report)
    if thread_networks:
        panel.append("\n\nDetected Thread network")
        if len(thread_networks) != 1:
            panel.append("s")
        panel.append(": ")
        panel.append(", ".join(thread_networks), style="cyan")

    suggestions = [item for item in _suggestion_text(report) if item != "No specific suggestions generated."]
    if suggestions:
        panel.append("\n\nWhat to try next:\n", style="bold")
        for suggestion in suggestions[:3]:
            panel.append(f"- {suggestion}\n")
    else:
        panel.append("\n\nNo immediate action is suggested.", style="green")

    console.print(Panel(panel, title="Quick Result", expand=True))


def render_report(report: DiagnosticReport, console: Console | None = None) -> None:
    out = console or Console()
    heading = Text("Matter Network Doctor", style="bold")
    heading.append(f"\nGenerated: {report.generated_at}", style="dim")
    out.print(Panel(heading, expand=False))
    _render_user_summary(report, out)

    for section, results in report.sections.items():
        table_title = "What To Try Next" if section == "Suggestions" else section
        table = Table(title=table_title, show_header=True, header_style="bold", expand=True)
        table.add_column("Status", width=8, no_wrap=True)
        table.add_column("Check", min_width=22)
        table.add_column("Result")

        for result in results:
            table.add_row(
                result.status.value.upper(),
                result.title,
                result.summary,
                style=STATUS_STYLE[result.status],
            )

        out.print(table)

        if section == "Suggestions":
            suggestions = results[0].details.get("suggestions", []) if results else []
            for suggestion in suggestions:
                out.print(f"  - {suggestion}", style="dim")
