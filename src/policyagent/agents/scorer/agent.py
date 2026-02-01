"""Scorer agent for calculating rule confidence scores."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any, cast

from policyagent.core.agent import Agent
from policyagent.core.models import ScoredRule, SearchSource, SQLRule
from policyagent.core.response import AgentResponse, LLMResponse, ToolResult
from policyagent.core.types import AgentRole
from policyagent.core.utils import extract_json_from_response
from policyagent.tools.websearch import WebSearchTool


if TYPE_CHECKING:
    from policyagent.core.llm import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a healthcare billing rule validator.
Validate billing rules by searching for supporting evidence.

## Confidence Scoring
- 90-100%: Multiple authoritative sources confirm the rule exactly
- 70-89%: Sources generally support the rule with minor variations
- 50-69%: Limited evidence or conflicting information
- 0-49%: Weak/no evidence or contradictory information

## Output Format
Return JSON: {"confidence": 85, "sources": [{"title": "", "url": "", "snippet": "", "relevance": 0.9}], "validation_notes": ["..."]}"""


class ScorerAgent(Agent):
    """Agent for scoring rule confidence using web search."""

    def __init__(self, llm: LLMClient) -> None:
        super().__init__(llm=llm, tools=[WebSearchTool()], max_iterations=5)

    @property
    def role(self) -> AgentRole:
        return AgentRole.SCORER

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def format_input(self, input_data: Any) -> str:
        sql_rule = cast("SQLRule", input_data)
        rule = sql_rule.rule
        return f"""Validate the following billing rule and calculate a confidence score.

Rule ID: {rule.id}
Name: {rule.name}
Classification: {rule.classification.value}
Description: {rule.description}
CPT Codes: {', '.join(rule.cpt_codes) or 'None'}

Use web_search to find supporting evidence from CMS guidelines and payer policies."""

    def process_output(self, response: LLMResponse, tool_results: list[ToolResult], total_tokens: int) -> AgentResponse:
        try:
            scoring_data = self._parse_scoring_from_response(response.content)
            return AgentResponse(success=True, output=scoring_data, tool_results=tool_results, total_tokens=total_tokens)
        except Exception as e:
            logger.exception("Failed to parse scoring from response")
            return AgentResponse(success=False, error=f"Failed to parse scoring: {e}",
                output={"confidence": 50, "sources": [], "validation_notes": [str(e)]},
                tool_results=tool_results, total_tokens=total_tokens)

    def _parse_scoring_from_response(self, content: str) -> dict[str, Any]:
        json_str = extract_json_from_response(content)
        try:
            data = json.loads(json_str)
            return {"confidence": float(data.get("confidence", 50)), "sources": data.get("sources", []),
                    "validation_notes": data.get("validation_notes", [])}
        except json.JSONDecodeError:
            match = re.search(r"confidence[:\s]+(\d+)", content.lower())
            return {"confidence": float(match.group(1)) if match else 50, "sources": [],
                    "validation_notes": ["Could not parse structured response"]}

    async def score(self, sql_rule: SQLRule) -> ScoredRule:
        logger.info("Scoring rule: %s", sql_rule.rule.id)
        response = await self.run(sql_rule)
        if response.success and isinstance(response.output, dict):
            scoring_data = cast("dict[str, Any]", response.output)
        else:
            scoring_data = {"confidence": 50, "sources": [], "validation_notes": [f"Scoring failed: {response.error}"]}
        sources: list[SearchSource] = []
        for src in scoring_data.get("sources", []):
            if isinstance(src, dict):
                sources.append(SearchSource(
                    title=str(src.get("title", "")), url=str(src.get("url", "")),
                    snippet=str(src.get("snippet", "")), relevance=float(src.get("relevance", 0.5)),
                ))
        scored_rule = ScoredRule(
            rule=sql_rule, confidence=float(scoring_data.get("confidence", 50)),
            sources=sources, validation_notes=scoring_data.get("validation_notes", []),
        )
        logger.info("Rule %s scored: %.1f%%", sql_rule.rule.id, scored_rule.confidence)
        return scored_rule
