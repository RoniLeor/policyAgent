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


if TYPE_CHECKING:
    from policyagent.core.models import (
        ExtractedRule,
        ParsedDocument,
        PolicyReport,
        ScoredRule,
        SQLRule,
    )


logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the policy processing pipeline.

    Pipeline stages:
    1. Parser: Extract text from PDF using OCR
    2. Analyzer: Identify and classify billing rules
    3. SQLGen: Generate SQL queries with self-correction
    4. Scorer: Calculate confidence scores via web search
    5. Reporter: Generate HTML report
    """

    def __init__(self, settings: Settings | None = None, mock: bool = False) -> None:
        """Initialize the pipeline.

        Args:
            settings: Application settings. If None, loads from environment.
            mock: If True, use mock LLM client for testing.
        """
        if settings is None:
            settings = Settings()

        self.settings = settings
        self._llm = LLMClient.create(settings, mock=mock)

        # Initialize agents
        self._parser = ParserAgent(self._llm)
        self._analyzer = AnalyzerAgent(self._llm)
        self._sqlgen = SQLGenAgent(self._llm, settings)
        self._scorer = ScorerAgent(self._llm)
        self._reporter = ReporterAgent(self._llm)

    async def run(
        self,
        pdf_path: str | Path,
        output_path: str | Path,
        policy_name: str | None = None,
    ) -> PolicyReport:
        """Run the complete pipeline on a PDF document.

        Args:
            pdf_path: Path to the input PDF file.
            output_path: Path for the output HTML report.
            policy_name: Optional name for the policy (defaults to filename).

        Returns:
            PolicyReport with all extracted and scored rules.
        """
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
        logger.info("Report saved to: %s", output_path)

        return report

    async def parse_only(self, pdf_path: str | Path) -> ParsedDocument:
        """Run only the parsing stage.

        Args:
            pdf_path: Path to the input PDF file.

        Returns:
            ParsedDocument with extracted text.
        """
        return await self._parser.parse(pdf_path)

    async def analyze_only(self, document: ParsedDocument) -> list[ExtractedRule]:
        """Run only the analysis stage.

        Args:
            document: Parsed document to analyze.

        Returns:
            List of extracted rules.
        """
        return await self._analyzer.analyze(document)

    async def generate_sql_only(self, rules: list[ExtractedRule]) -> list[SQLRule]:
        """Run only the SQL generation stage.

        Args:
            rules: List of extracted rules.

        Returns:
            List of SQL rules.
        """
        sql_rules: list[SQLRule] = []
        for rule in rules:
            sql_rule = await self._sqlgen.generate(rule)
            sql_rules.append(sql_rule)
        return sql_rules

    async def score_only(self, sql_rules: list[SQLRule]) -> list[ScoredRule]:
        """Run only the scoring stage.

        Args:
            sql_rules: List of SQL rules.

        Returns:
            List of scored rules.
        """
        scored_rules: list[ScoredRule] = []
        for sql_rule in sql_rules:
            scored_rule = await self._scorer.score(sql_rule)
            scored_rules.append(scored_rule)
        return scored_rules
