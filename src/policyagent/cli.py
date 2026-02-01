"""Command-line interface for policyAgent."""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from policyagent.config.settings import Settings
from policyagent.console.logger import PipelineConsole
from policyagent.core.types import RuleClassification
from policyagent.orchestrator.pipeline import Pipeline
from policyagent.storage.claims_db import ClaimsDatabase
from policyagent.storage.repository import RuleRepository
from policyagent.tools.html import create_default_template


if TYPE_CHECKING:
    from policyagent.core.models import ScoredRule

console = PipelineConsole()


async def run_pipeline(  # noqa: PLR0915
    pdf_path: str,
    output_path: str,
    policy_name: str | None = None,
    save_to_db: bool = True,
    db_path: str = "rules.db",
    mock: bool = False,
    claims_db_path: str | None = None,
) -> None:
    """Run the policy processing pipeline."""
    settings = Settings()
    console.setup_logging(settings.log_level)
    pdf_path_obj = Path(pdf_path)
    if policy_name is None:
        policy_name = pdf_path_obj.stem
    console.print_header(policy_name, pdf_path)
    if mock:
        console.console.print("[yellow]Running in MOCK mode (no API calls)[/yellow]\n")
    create_default_template()

    # Setup claims database if provided
    claims_db = None
    if claims_db_path:
        claims_db = ClaimsDatabase(claims_db_path)
        stats = claims_db.get_stats()
        console.console.print(
            f"[cyan]Claims DB:[/cyan] {stats['claims']} claims, {stats['claim_lines']} lines\n"
        )

    pipeline = Pipeline(settings, mock=mock, claims_db=claims_db)

    with console.pipeline_progress() as progress:
        console.print_stage_start(1, "Parsing PDF", "📄")
        task1 = console.create_stage_task(progress, "Parsing PDF...", total=None)
        document = await pipeline.parse_only(pdf_path_obj)
        progress.update(task1, completed=True)
        console.print_stage_complete(1, "Parsed", f"{document.page_count} pages")

        console.print_stage_start(2, "Analyzing document", "🔍")
        task2 = console.create_stage_task(progress, "Extracting rules...", total=None)
        rules = await pipeline.analyze_only(document)
        progress.update(task2, completed=True)
        console.print_stage_complete(2, "Extracted", f"{len(rules)} rules")
        console.print_rules_extracted(rules)

        console.print_stage_start(3, "Generating SQL", "💾")
        task3 = console.create_stage_task(progress, "Generating SQL...", total=len(rules))
        sql_rules = []
        for rule in rules:
            sql_rule = await pipeline._sqlgen.generate(rule)
            sql_rules.append(sql_rule)
            progress.update(task3, advance=1)
            console.print_sql_generation(rule.id, bool(sql_rule.sql), sql_rule.retry_count)
        console.print_stage_complete(3, "SQL Generated", f"{len(sql_rules)} queries")

        console.print_stage_start(4, "Scoring rules", "🎯")
        task4 = console.create_stage_task(progress, "Scoring confidence...", total=len(sql_rules))
        scored_rules: list[ScoredRule] = []
        for sql_rule in sql_rules:
            scored_rule = await pipeline._scorer.score(sql_rule)
            scored_rules.append(scored_rule)
            progress.update(task4, advance=1)
            console.print_scoring(sql_rule.rule.id, scored_rule.confidence)
        avg_conf = (
            sum(r.confidence for r in scored_rules) / len(scored_rules) if scored_rules else 0
        )
        console.print_stage_complete(4, "Scored", f"avg: {avg_conf:.0f}%")

        # Execute queries if claims database is available
        if claims_db:
            console.print_stage_start(5, "Executing queries", "🔎")
            scored_rules = pipeline.execute_queries(scored_rules)
            total_violations = sum(r.query_result.violation_count for r in scored_rules)
            console.print_stage_complete(
                5, "Queries executed", f"{total_violations} violations found"
            )

        console.print_stage_start(6 if claims_db else 5, "Generating report", "📊")
        task5 = console.create_stage_task(progress, "Creating HTML...", total=None)
        report = await pipeline._reporter.generate_report(
            policy_name=policy_name,
            source_path=str(pdf_path_obj.absolute()),
            rules=scored_rules,
            output_path=output_path,
            total_pages=document.page_count,
            processing_time=time.time(),
        )
        progress.update(task5, completed=True)
        console.print_stage_complete(6 if claims_db else 5, "Report generated")

    if save_to_db and scored_rules:
        repo = RuleRepository(db_path)
        repo.save_rules(policy_name, scored_rules)
        console.print_onboarding_complete(policy_name, len(scored_rules))
    console.print_report_summary(report)
    console.print_success(output_path)


async def search_rules(
    cpt_codes: list[str] | None = None,
    classification: str | None = None,
    vendor: str | None = None,
    text: str | None = None,
    db_path: str = "rules.db",
) -> None:
    """Search rules in the database."""
    repo = RuleRepository(db_path)
    class_enum = None
    if classification:
        try:
            class_enum = RuleClassification(classification)
        except ValueError:
            console.print_error(f"Invalid classification: {classification}")
            return
    rules = repo.search(
        cpt_codes=cpt_codes, classification=class_enum, vendor=vendor, text_query=text
    )
    console.print_search_results(
        {"cpt_codes": cpt_codes, "classification": classification, "vendor": vendor, "text": text},
        rules,
    )


async def show_stats(db_path: str = "rules.db") -> None:
    """Show database statistics."""
    repo = RuleRepository(db_path)
    console.print_db_stats(repo.get_stats())


async def init_claims_db(db_path: str = "claims.db", load_sample: bool = True) -> None:
    """Initialize claims database with sample data."""
    claims_db = ClaimsDatabase(db_path)
    if load_sample:
        claims_db.load_sample_data()
        console.console.print(f"[green]✓[/green] Claims database initialized at {db_path}")
        stats = claims_db.get_stats()
        console.console.print(
            f"  Patients: {stats['patients']}, Claims: {stats['claims']}, "
            f"Lines: {stats['claim_lines']}"
        )


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="policyagent", description="AI Agent for Healthcare Policy Analysis"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    proc = subparsers.add_parser("process", help="Process a policy PDF")
    proc.add_argument("pdf_path", help="Path to the input PDF file")
    proc.add_argument("output_path", help="Path for the output HTML report")
    proc.add_argument("--name", "-n", help="Policy name")
    proc.add_argument("--no-save", action="store_true", help="Don't save rules to database")
    proc.add_argument("--db", default="rules.db", help="Rules database path")
    proc.add_argument("--claims-db", help="Claims database path for query execution")
    proc.add_argument("--mock", action="store_true", help="Use mock LLM for testing")

    srch = subparsers.add_parser("search", help="Search rules in database")
    srch.add_argument("--cpt", help="CPT codes (comma-separated)")
    srch.add_argument(
        "--type", choices=["mutual_exclusion", "overutilization", "service_not_covered"]
    )
    srch.add_argument("--vendor", help="Vendor/policy name")
    srch.add_argument("--text", "-t", help="Text search query")
    srch.add_argument("--db", default="rules.db", help="Database path")

    stats_cmd = subparsers.add_parser("stats", help="Show database statistics")
    stats_cmd.add_argument("--db", default="rules.db", help="Database path")

    init_cmd = subparsers.add_parser(
        "init-claims", help="Initialize claims database with sample data"
    )
    init_cmd.add_argument("--db", default="claims.db", help="Claims database path")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "process":
            if not Path(args.pdf_path).exists():
                console.print_error(f"PDF file not found: {args.pdf_path}")
                sys.exit(1)
            asyncio.run(
                run_pipeline(
                    args.pdf_path,
                    args.output_path,
                    args.name,
                    not args.no_save,
                    args.db,
                    args.mock,
                    args.claims_db,
                )
            )
        elif args.command == "search":
            asyncio.run(
                search_rules(
                    args.cpt.split(",") if args.cpt else None,
                    args.type,
                    args.vendor,
                    args.text,
                    args.db,
                )
            )
        elif args.command == "stats":
            asyncio.run(show_stats(args.db))
        elif args.command == "init-claims":
            asyncio.run(init_claims_db(args.db))
    except KeyboardInterrupt:
        console.console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
