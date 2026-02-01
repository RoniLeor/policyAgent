"""Beautiful console logging for the pipeline."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text

from policyagent.console.display import (
    print_db_stats,
    print_report_summary,
    print_rules_extracted,
    print_rules_table,
    print_search_results,
)


if TYPE_CHECKING:
    from collections.abc import Iterator

    from policyagent.core.models import ExtractedRule, PolicyReport, ScoredRule


class PipelineConsole:
    """Rich console interface for pipeline progress and results."""

    def __init__(self, verbose: bool = False) -> None:
        self.console = Console()
        self.verbose = verbose
        self._progress: Progress | None = None

    def setup_logging(self, level: str = "INFO") -> None:
        logging.basicConfig(
            level=level if self.verbose else "WARNING",
            format="%(message)s",
            handlers=[
                RichHandler(
                    console=self.console, rich_tracebacks=True, show_time=False, show_path=False
                )
            ],
            force=True,
        )

    def print_header(self, policy_name: str, pdf_path: str) -> None:
        header = Text()
        header.append("policyAgent", style="bold blue")
        header.append(" - Healthcare Policy Analyzer\n\n", style="dim")
        header.append("Policy: ", style="bold")
        header.append(f"{policy_name}\n", style="green")
        header.append("Source: ", style="bold")
        header.append(str(pdf_path), style="dim")
        self.console.print(Panel(header, border_style="blue"))
        self.console.print()

    @contextmanager
    def pipeline_progress(self) -> Iterator[Progress]:
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
            expand=False,
        )
        with self._progress:
            yield self._progress

    def create_stage_task(
        self, progress: Progress, description: str, total: int | None = None
    ) -> TaskID:
        return progress.add_task(description, total=total)

    def print_stage_start(self, stage: int, name: str, icon: str = "🔄") -> None:
        self.console.print(f"\n{icon} [bold]Stage {stage}/5:[/bold] {name}")

    def print_stage_complete(
        self, stage: int, name: str, details: str = "", icon: str = "✓"
    ) -> None:
        self.console.print(f"  [green]{icon}[/green] {name} [dim]{details}[/dim]")

    def print_rules_extracted(self, rules: list[ExtractedRule]) -> None:
        print_rules_extracted(self.console, rules)

    def print_sql_generation(self, rule_id: str, success: bool, retries: int) -> None:
        if success:
            status, retry_text = (
                "[green]✓[/green]",
                f" [dim](retries: {retries})[/dim]" if retries > 0 else "",
            )
        else:
            status, retry_text = "[red]✗[/red]", f" [dim](failed after {retries} retries)[/dim]"
        self.console.print(f"  {status} {rule_id}{retry_text}")

    def print_scoring(self, rule_id: str, confidence: float) -> None:
        color = "green" if confidence >= 80 else "yellow" if confidence >= 50 else "red"
        bar_width, filled = 20, int(confidence / 100 * 20)
        bar = "█" * filled + "░" * (bar_width - filled)
        self.console.print(f"  {rule_id}: [{color}]{bar}[/{color}] {confidence:.0f}%")

    def print_report_summary(self, report: PolicyReport) -> None:
        print_report_summary(self.console, report)

    def print_rules_table(self, rules: list[ScoredRule]) -> None:
        print_rules_table(self.console, rules)

    def print_success(self, output_path: str) -> None:
        self.console.print()
        self.console.print(
            Panel(
                f"[green]✓ Report generated successfully![/green]\n\n"
                f"[bold]Output:[/bold] {output_path}",
                title="[green]Complete[/green]",
                border_style="green",
            )
        )

    def print_error(self, error: str) -> None:
        self.console.print()
        self.console.print(
            Panel(f"[red]{error}[/red]", title="[red]Error[/red]", border_style="red")
        )

    def print_search_results(self, query_info: dict[str, Any], rules: list[ScoredRule]) -> None:
        print_search_results(self.console, query_info, rules)

    def print_onboarding_complete(self, vendor: str, rule_count: int) -> None:
        self.console.print()
        self.console.print(
            Panel(
                f"[green]✓ Onboarding complete![/green]\n\n"
                f"[bold]Vendor:[/bold] {vendor}\n[bold]Rules indexed:[/bold] {rule_count}",
                title="[green]Indexed[/green]",
                border_style="green",
            )
        )

    def print_db_stats(self, stats: dict[str, Any]) -> None:
        print_db_stats(self.console, stats)
