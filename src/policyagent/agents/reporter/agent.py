"""Reporter agent for generating HTML reports."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from policyagent.core.agent import Agent
from policyagent.core.models import PolicyReport, ScoredRule
from policyagent.core.response import AgentResponse, LLMResponse, ToolResult
from policyagent.core.types import AgentRole
from policyagent.tools.html import HTMLTool


if TYPE_CHECKING:
    from pathlib import Path

    from policyagent.core.llm import LLMClient


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a report generation specialist.
Your task is to compile billing rules into a formatted HTML report.

## Report Requirements

1. Include all extracted rules with their classifications
2. Show SQL implementations with proper formatting
3. Display confidence scores with visual indicators
4. List validation sources with links
5. Provide summary statistics

Use the html_report tool to generate the final HTML file."""


class ReporterAgent(Agent):
    """Agent for generating HTML reports from scored rules."""

    def __init__(self, llm: LLMClient) -> None:
        """Initialize the reporter agent.

        Args:
            llm: LLM client for report generation.
        """
        html_tool = HTMLTool()
        super().__init__(llm=llm, tools=[html_tool], max_iterations=3)
        self._html_tool = html_tool

    @property
    def role(self) -> AgentRole:
        """Get the agent's role."""
        return AgentRole.REPORTER

    @property
    def system_prompt(self) -> str:
        """Get the agent's system prompt."""
        return SYSTEM_PROMPT

    def format_input(self, input_data: Any) -> str:
        """Format input data as a user message.

        Args:
            input_data: Dictionary with report data.

        Returns:
            Formatted user message.
        """
        return f"Generate an HTML report for the policy analysis. Report data: {input_data}"

    def process_output(
        self,
        response: LLMResponse,
        tool_results: list[ToolResult],
        total_tokens: int,
    ) -> AgentResponse:
        """Process the final LLM response into an AgentResponse.

        Args:
            response: Final LLM response.
            tool_results: Results from all tool executions.
            total_tokens: Total tokens used.

        Returns:
            AgentResponse with report path.
        """
        # Find the HTML tool result
        for result in tool_results:
            if result.tool_name == "html_report" and result.success:
                return AgentResponse(
                    success=True,
                    output=result.output,
                    tool_results=tool_results,
                    total_tokens=total_tokens,
                )

        return AgentResponse(
            success=False,
            error="HTML report generation failed",
            tool_results=tool_results,
            total_tokens=total_tokens,
        )

    async def generate_report(
        self,
        policy_name: str,
        source_path: str,
        rules: list[ScoredRule],
        output_path: str | Path,
        total_pages: int = 0,
        processing_time: float = 0.0,
    ) -> PolicyReport:
        """Generate HTML report directly without LLM reasoning.

        This is the primary method for report generation, using tools directly.

        Args:
            policy_name: Name of the policy document.
            source_path: Path to source PDF.
            rules: List of scored rules.
            output_path: Path for output HTML file.
            total_pages: Total pages in source document.
            processing_time: Total processing time in seconds.

        Returns:
            PolicyReport with generation details.
        """
        logger.info("Generating report for: %s", policy_name)

        # Calculate total violations
        total_violations = sum(r.query_result.violation_count for r in rules)

        # Create report model
        report = PolicyReport(
            policy_name=policy_name,
            source_path=source_path,
            generated_at=datetime.now(),
            rules=rules,
            total_pages=total_pages,
            processing_time_seconds=processing_time,
            total_violations=total_violations,
        )

        # Generate HTML
        template_data = report.to_template_data()
        result = await self._html_tool.execute(
            report_data=template_data,
            output_path=str(output_path),
        )

        if result.success:
            logger.info("Report generated: %s", output_path)
        else:
            logger.error("Report generation failed: %s", result.error)

        return report
