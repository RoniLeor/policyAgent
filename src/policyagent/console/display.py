"""Display components for console output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree


if TYPE_CHECKING:
    from rich.console import Console

    from policyagent.core.models import ExtractedRule, PolicyReport, ScoredRule


def print_rules_extracted(console: Console, rules: list[ExtractedRule]) -> None:
    """Print extracted rules summary."""
    if not rules:
        console.print("  [yellow]⚠[/yellow] No rules extracted")
        return
    by_class: dict[str, list[ExtractedRule]] = {}
    for rule in rules:
        key = rule.classification.value
        by_class.setdefault(key, []).append(rule)
    tree = Tree("[bold]Extracted Rules[/bold]")
    for classification, class_rules in by_class.items():
        branch = tree.add(
            f"[cyan]{classification.replace('_', ' ').title()}[/cyan] ({len(class_rules)})"
        )
        for rule in class_rules[:3]:
            branch.add(f"[dim]{rule.id}[/dim] {rule.name}")
        if len(class_rules) > 3:
            branch.add(f"[dim]... and {len(class_rules) - 3} more[/dim]")
    console.print(tree)


def print_report_summary(console: Console, report: PolicyReport) -> None:
    """Print final report summary."""
    console.print()
    table = Table(title="Report Summary", border_style="blue")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Total Rules", str(len(report.rules)))
    table.add_row("Total Pages", str(report.total_pages))
    table.add_row("Processing Time", f"{report.processing_time_seconds:.1f}s")
    by_class: dict[str, int] = {}
    for rule in report.rules:
        key = rule.rule.rule.classification.value
        by_class[key] = by_class.get(key, 0) + 1
    for classification, count in by_class.items():
        table.add_row(f"  {classification.replace('_', ' ').title()}", str(count))
    if report.rules:
        confidences = [r.confidence for r in report.rules]
        table.add_row("Avg Confidence", f"{sum(confidences) / len(confidences):.1f}%")
        table.add_row("High Confidence (>80%)", str(sum(1 for c in confidences if c >= 80)))
    console.print(table)


def print_rules_table(console: Console, rules: list[ScoredRule]) -> None:
    """Print detailed rules table."""
    if not rules:
        return
    table = Table(title="Rules Detail", border_style="dim")
    table.add_column("ID", style="dim", width=12)
    table.add_column("Name", width=30)
    table.add_column("Type", width=15)
    table.add_column("CPT Codes", width=15)
    table.add_column("Conf", justify="right", width=6)
    for rule in rules:
        r = rule.rule.rule
        conf_color = (
            "green" if rule.confidence >= 80 else "yellow" if rule.confidence >= 50 else "red"
        )
        cpt_str = ", ".join(r.cpt_codes[:3]) + ("..." if len(r.cpt_codes) > 3 else "")
        table.add_row(
            r.id,
            r.name[:28] + "..." if len(r.name) > 30 else r.name,
            r.classification.value.replace("_", " "),
            cpt_str,
            f"[{conf_color}]{rule.confidence:.0f}%[/{conf_color}]",
        )
    console.print(table)


def print_search_results(
    console: Console, query_info: dict[str, Any], rules: list[ScoredRule]
) -> None:
    """Print search results."""
    query_parts = []
    if query_info.get("cpt_codes"):
        query_parts.append(f"CPT: {', '.join(query_info['cpt_codes'])}")
    if query_info.get("classification"):
        query_parts.append(f"Type: {query_info['classification']}")
    if query_info.get("vendor"):
        query_parts.append(f"Vendor: {query_info['vendor']}")
    if query_info.get("text"):
        query_parts.append(f"Text: {query_info['text']}")
    query_str = " | ".join(query_parts) if query_parts else "All rules"
    console.print(
        Panel(
            f"[bold]Query:[/bold] {query_str}\n[bold]Results:[/bold] {len(rules)} rules found",
            title="Search Results",
            border_style="blue",
        )
    )
    if rules:
        print_rules_table(console, rules)


def print_db_stats(console: Console, stats: dict[str, Any]) -> None:
    """Print database statistics."""
    table = Table(title="Rule Database Statistics", border_style="blue")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Total Rules", str(stats["total_rules"]))
    table.add_row("Average Confidence", f"{stats['average_confidence']}%")
    for classification, count in stats.get("by_classification", {}).items():
        table.add_row(f"  {classification.replace('_', ' ').title()}", str(count))
    console.print()
    console.print(table)
    if stats.get("by_vendor"):
        vendor_table = Table(title="Rules by Vendor", border_style="dim")
        vendor_table.add_column("Vendor")
        vendor_table.add_column("Rules", justify="right")
        for vendor, count in stats["by_vendor"].items():
            vendor_table.add_row(vendor, str(count))
        console.print(vendor_table)
