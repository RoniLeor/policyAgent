"""Analyzer agent for identifying and classifying billing rules."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, cast

from policyagent.core.agent import Agent
from policyagent.core.models import ExtractedRule, ParsedDocument
from policyagent.core.response import AgentResponse, LLMResponse, ToolResult
from policyagent.core.types import AgentRole, RuleClassification
from policyagent.core.utils import extract_json_from_response


if TYPE_CHECKING:
    from policyagent.core.llm import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a healthcare billing rule analyst.
Identify and classify billing rules from policy document text.

## Rule Classifications
1. **mutual_exclusion**: Services that cannot be billed together
2. **overutilization**: Limits on service frequency or units
3. **service_not_covered**: Services not covered under specific conditions

## Output Format
Return a JSON array with objects containing: id, name, description, classification,
source_text, cpt_codes, icd10_codes, modifiers, conditions.

Example:
```json
[{"id": "RULE-001", "name": "Microsurgery Add-on Restriction",
  "description": "CPT 69990 can only be billed with approved primary procedures",
  "classification": "mutual_exclusion", "source_text": "Code 69990 is only billable...",
  "cpt_codes": ["69990"], "icd10_codes": [], "modifiers": [], "conditions": []}]
```"""


class AnalyzerAgent(Agent):
    """Agent for analyzing policy text and extracting billing rules."""

    def __init__(self, llm: LLMClient) -> None:
        super().__init__(llm=llm, tools=[], max_iterations=3)

    @property
    def role(self) -> AgentRole:
        return AgentRole.ANALYZER

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def format_input(self, input_data: Any) -> str:
        text = input_data.full_text if isinstance(input_data, ParsedDocument) else str(input_data)
        return f"Analyze the following policy document text and extract all billing rules.\n\nDocument Text:\n---\n{text}\n---\n\nReturn your analysis as a JSON array."

    def process_output(self, response: LLMResponse, tool_results: list[ToolResult], total_tokens: int) -> AgentResponse:
        try:
            rules = self._parse_rules_from_response(response.content)
            return AgentResponse(success=True, output=rules, tool_results=tool_results, total_tokens=total_tokens)
        except Exception as e:
            logger.exception("Failed to parse rules from response")
            return AgentResponse(success=False, error=f"Failed to parse rules: {e}", tool_results=tool_results, total_tokens=total_tokens)

    def _parse_rules_from_response(self, content: str) -> list[ExtractedRule]:
        json_str = extract_json_from_response(content)
        raw_data = json.loads(json_str)
        data: list[dict[str, Any]] = raw_data if isinstance(raw_data, list) else [raw_data]
        rules: list[ExtractedRule] = []
        for i, item in enumerate(data):
            try:
                classification = RuleClassification(item.get("classification", "mutual_exclusion"))
            except ValueError:
                classification = RuleClassification.MUTUAL_EXCLUSION
            rules.append(ExtractedRule(
                id=item.get("id", f"RULE-{i + 1:03d}"), name=item.get("name", f"Rule {i + 1}"),
                description=item.get("description", ""), classification=classification,
                source_text=item.get("source_text", ""), cpt_codes=item.get("cpt_codes", []),
                icd10_codes=item.get("icd10_codes", []), modifiers=item.get("modifiers", []),
                conditions=item.get("conditions", []),
            ))
        return rules

    async def analyze(self, document: ParsedDocument) -> list[ExtractedRule]:
        logger.info("Analyzing document: %s", document.path)
        response = await self.run(document)
        if response.success and isinstance(response.output, list):
            rules = cast("list[ExtractedRule]", response.output)
            logger.info("Extracted %d rules", len(rules))
            return rules
        logger.error("Analysis failed: %s", response.error)
        return []
