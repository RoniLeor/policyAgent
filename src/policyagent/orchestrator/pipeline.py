"""Pipeline orchestrator for the policy agent system."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from policyagent.agents.analyzer import AnalyzerAgent
from policyagent.agents.parser import ParserAgent
from policyagent.agents.reporter import ReporterAgent
from policyagent.agents.scorer import ScorerAgent
from policyagent.agents.sqlgen import SQLGenAgent
from policyagent.config.settings import Settings
from policyagent.core.llm import LLMClient
from policyagent.core.models import QueryResult


if TYPE_CHECKING:
    from policyagent.core.models import (
        ExtractedRule,
        ParsedDocument,
        PolicyReport,
        ScoredRule,
        SQLRule,
    )
    from policyagent.storage.claims_db import ClaimsDatabase

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the policy processing pipeline."""

    def __init__(
        self,
        settings: Settings | None = None,
        mock: bool = False,
        claims_db: ClaimsDatabase | None = None,
    ) -> None:
        if settings is None:
            settings = Settings()
        self.settings = settings
        self._llm = LLMClient.create(settings, mock=mock)
        self._claims_db = claims_db

        self._parser = ParserAgent(self._llm)
        self._analyzer = AnalyzerAgent(self._llm)
        self._sqlgen = SQLGenAgent(self._llm, settings)
        self._scorer = ScorerAgent(self._llm)
        self._reporter = ReporterAgent(self._llm)

        # Connect claims database to SQL tool if provided
        if claims_db:
            self._sqlgen._sql_tool.set_claims_db(claims_db)

    def set_claims_db(self, claims_db: ClaimsDatabase) -> None:
        """Set or update the claims database."""
        self._claims_db = claims_db
        self._sqlgen._sql_tool.set_claims_db(claims_db)

    async def run(
        self, pdf_path: str | Path, output_path: str | Path, policy_name: str | None = None
    ) -> PolicyReport:
        """Run the complete pipeline on a PDF document."""
        start_time = time.time()
        pdf_path = Path(pdf_path)
        output_path = Path(output_path)
        if policy_name is None:
            policy_name = pdf_path.stem

        logger.info("Starting pipeline for: %s", pdf_path.name)

        # Stage 1: Parse PDF
        logger.info("Stage 1/5: Parsing PDF")
        document = await self._parser.parse(pdf_path)
        logger.info("Parsed %d pages", document.page_count)

        # Stage 2: Analyze for rules
        logger.info("Stage 2/5: Analyzing document")
        rules = await self._analyzer.analyze(document)
        logger.info("Extracted %d rules", len(rules))

        # Stage 3: Generate SQL for each rule
        logger.info("Stage 3/5: Generating SQL")
        sql_rules: list[SQLRule] = []
        for rule in rules:
            sql_rule = await self._sqlgen.generate(rule)
            sql_rules.append(sql_rule)
        logger.info("Generated SQL for %d rules", len(sql_rules))

        # Stage 4: Score each rule
        logger.info("Stage 4/5: Scoring rules")
        scored_rules: list[ScoredRule] = []
        for sql_rule in sql_rules:
            scored_rule = await self._scorer.score(sql_rule)
            scored_rules.append(scored_rule)
        logger.info("Scored %d rules", len(scored_rules))

        # Execute queries against claims database if available
        if self._claims_db:
            logger.info("Executing queries against claims database")
            scored_rules = self._execute_queries(scored_rules)

        # Stage 5: Generate report
        logger.info("Stage 5/5: Generating report")
        processing_time = time.time() - start_time
        report = await self._reporter.generate_report(
            policy_name=policy_name,
            source_path=str(pdf_path.absolute()),
            rules=scored_rules,
            output_path=output_path,
            total_pages=document.page_count,
            processing_time=processing_time,
        )

        logger.info("Pipeline complete in %.1fs", processing_time)
        return report

    def _execute_queries(self, scored_rules: list[ScoredRule]) -> list[ScoredRule]:
        """Execute SQL queries for each rule and add results."""
        if not self._claims_db:
            return scored_rules

        for scored_rule in scored_rules:
            sql = scored_rule.rule.sql
            if not sql:
                continue
            try:
                result = self._claims_db.execute_query(sql)
                if result["success"]:
                    scored_rule.query_result = QueryResult(
                        executed=True,
                        violation_count=result["count"],
                        violations=result["rows"],
                        columns=result["columns"],
                    )
                else:
                    scored_rule.query_result = QueryResult(executed=True, error=result.get("error"))
            except Exception as e:
                logger.warning("Query execution failed for %s: %s", scored_rule.rule.rule.id, e)
                scored_rule.query_result = QueryResult(executed=True, error=str(e))
        return scored_rules

    async def parse_only(self, pdf_path: str | Path) -> ParsedDocument:
        return await self._parser.parse(pdf_path)

    async def analyze_only(self, document: ParsedDocument) -> list[ExtractedRule]:
        return await self._analyzer.analyze(document)

    async def generate_sql_only(self, rules: list[ExtractedRule]) -> list[SQLRule]:
        return [await self._sqlgen.generate(rule) for rule in rules]

    async def score_only(self, sql_rules: list[SQLRule]) -> list[ScoredRule]:
        return [await self._scorer.score(sql_rule) for sql_rule in sql_rules]

    def execute_queries(self, scored_rules: list[ScoredRule]) -> list[ScoredRule]:
        """Execute queries for already scored rules."""
        return self._execute_queries(scored_rules)
