"""SQL generation agent with self-correction loop."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any, cast

from policyagent.config.schema import CLAIMS_SCHEMA
from policyagent.config.settings import Settings
from policyagent.core.agent import Agent
from policyagent.core.models import ExtractedRule, SQLRule
from policyagent.core.response import AgentResponse, LLMResponse, ToolResult
from policyagent.core.types import AgentRole
from policyagent.core.utils import extract_json_from_response
from policyagent.tools.sql import SQLTool


if TYPE_CHECKING:
    from policyagent.core.llm import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a SQL expert specializing in healthcare claims database queries.
Generate SQL queries that implement billing rules.

## Database Schema
{schema}

## Requirements
1. Generate SELECT queries that identify claims violating the rule
2. Use proper JOIN syntax and EXISTS clauses for complex conditions

## Output Format
Return JSON: {{"sql": "SELECT...", "explanation": "..."}}
If validator returns errors, fix and retry (up to {max_retries} attempts)."""


class SQLGenAgent(Agent):
    """Agent for generating SQL queries with self-correction."""

    def __init__(self, llm: LLMClient, settings: Settings | None = None) -> None:
        sql_tool = SQLTool()
        super().__init__(llm=llm, tools=[sql_tool], max_iterations=10)
        self._sql_tool = sql_tool
        if settings is None:
            settings = Settings()
        self._max_retries = settings.sql.max_retries

    @property
    def role(self) -> AgentRole:
        return AgentRole.SQLGEN

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(schema=CLAIMS_SCHEMA, max_retries=self._max_retries)

    def format_input(self, input_data: Any) -> str:
        rule = input_data
        return f"""Generate SQL to identify claims violating this billing rule:

Rule ID: {rule.id}
Name: {rule.name}
Classification: {rule.classification.value}
Description: {rule.description}
CPT Codes: {', '.join(rule.cpt_codes) or 'None'}
ICD-10 Codes: {', '.join(rule.icd10_codes) or 'None'}
Modifiers: {', '.join(rule.modifiers) or 'None'}
Conditions: {'; '.join(rule.conditions) or 'None'}
Source Text: {rule.source_text}

Generate SQL and use sql_validator to validate it."""

    def process_output(self, response: LLMResponse, tool_results: list[ToolResult], total_tokens: int) -> AgentResponse:
        try:
            sql = self._extract_sql_from_response(response.content)
            return AgentResponse(success=True, output=sql, tool_results=tool_results, total_tokens=total_tokens)
        except Exception as e:
            logger.exception("Failed to extract SQL from response")
            return AgentResponse(success=False, error=f"Failed to extract SQL: {e}", tool_results=tool_results, total_tokens=total_tokens)

    def _extract_sql_from_response(self, content: str) -> str:
        json_str = extract_json_from_response(content)
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "sql" in data:
                return data["sql"]
        except json.JSONDecodeError:
            pass
        sql_match = re.search(r"```(?:sql)?\s*([\s\S]*?)```", content)
        if sql_match:
            return sql_match.group(1).strip()
        if content.strip().upper().startswith("SELECT"):
            return content.strip()
        msg = "Could not extract SQL from response"
        raise ValueError(msg)

    async def generate(self, rule: ExtractedRule) -> SQLRule:
        logger.info("Generating SQL for rule: %s", rule.id)
        retry_count, sql, warnings = 0, "", []
        for attempt in range(self._max_retries + 1):
            response = await self.run(rule)
            if not response.success:
                logger.warning("SQL generation attempt %d failed: %s", attempt + 1, response.error)
                retry_count = attempt + 1
                continue
            sql = str(response.output)
            validation = await self._sql_tool.execute(sql=sql)
            if validation.success and isinstance(validation.output, dict):
                output_dict = cast("dict[str, Any]", validation.output)
                warnings = output_dict.get("warnings", [])
                if not warnings:
                    logger.info("SQL validated successfully for rule %s", rule.id)
                    break
                logger.warning("SQL has warnings: %s", warnings)
            retry_count = attempt + 1
        return SQLRule(rule=rule, sql=sql, sql_formatted=self._sql_tool.format_sql(sql),
                      validation_warnings=warnings, retry_count=retry_count)
