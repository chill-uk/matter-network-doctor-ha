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


def render_report(report: DiagnosticReport, console: Console | None = None) -> None:
    out = console or Console()
    heading = Text("Matter Network Doctor", style="bold")
    heading.append(f"\nGenerated: {report.generated_at}", style="dim")
    out.print(Panel(heading, expand=False))

    for section, results in report.sections.items():
        table = Table(title=section, show_header=True, header_style="bold", expand=True)
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

