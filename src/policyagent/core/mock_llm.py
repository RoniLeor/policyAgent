"""Mock LLM client for testing without API keys."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from policyagent.core.response import LLMResponse, TokenUsage, ToolCall


if TYPE_CHECKING:
    from policyagent.core.types import JSON


class MockLLMClient:
    """Mock LLM client that returns predefined responses for testing."""

    def __init__(self) -> None:
        self._call_count = 0

    async def chat(self, messages: list[JSON], tools: list[JSON] | None = None, temperature: float = 0.0) -> LLMResponse:
        self._call_count += 1
        last_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_msg = str(msg.get("content", ""))
                break
        if "Analyze the following policy document" in last_msg:
            return self._analyzer_response(last_msg)
        elif "Generate a SQL query" in last_msg:
            return self._sqlgen_response(last_msg)
        elif "Validate the following billing rule" in last_msg:
            return self._scorer_response(last_msg, tools)
        return LLMResponse(content="Mock response", tool_calls=[], finish_reason="stop",
                          usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150))

    def _analyzer_response(self, msg: str) -> LLMResponse:
        rules = []
        if "mutual exclusion" in msg.lower() or "cannot be billed" in msg.lower():
            rules.append({"id": "RULE-001", "name": "Microsurgery Add-on Restriction",
                "description": "CPT 69990 cannot be billed with non-microsurgery procedures",
                "classification": "mutual_exclusion", "source_text": "CPT 69990 cannot be billed with non-microsurgery procedures.",
                "cpt_codes": ["69990"], "icd10_codes": [], "modifiers": [],
                "conditions": ["Must be billed with approved microsurgery procedure"]})
        if any(kw in msg.lower() for kw in ["overutilization", "maximum", "limit"]):
            rules.append({"id": "RULE-002", "name": "Therapeutic Exercise Unit Limit",
                "description": "CPT 97110 is limited to 4 units per day", "classification": "overutilization",
                "source_text": "CPT 97110 limited to max 4 units per day per patient.", "cpt_codes": ["97110"],
                "icd10_codes": [], "modifiers": [], "conditions": ["Maximum 4 units per day per patient"]})
        if "not covered" in msg.lower() or "cosmetic" in msg.lower():
            rules.append({"id": "RULE-003", "name": "Cosmetic Procedure Exclusion",
                "description": "Cosmetic procedures are not covered", "classification": "service_not_covered",
                "source_text": "Cosmetic procedures (CPT 15780-15783) not covered.",
                "cpt_codes": ["15780", "15781", "15782", "15783"], "icd10_codes": [], "modifiers": [],
                "conditions": ["Procedure must not be cosmetic"]})
        if not rules:
            rules.append({"id": "RULE-001", "name": "Sample Billing Rule", "description": "Sample rule",
                "classification": "mutual_exclusion", "source_text": "Sample policy text", "cpt_codes": ["99213"],
                "icd10_codes": [], "modifiers": [], "conditions": []})
        return LLMResponse(content=f"```json\n{json.dumps(rules, indent=2)}\n```", tool_calls=[], finish_reason="stop",
                          usage=TokenUsage(prompt_tokens=500, completion_tokens=300, total_tokens=800))

    def _sqlgen_response(self, msg: str) -> LLMResponse:
        if "69990" in msg or "mutual_exclusion" in msg.lower():
            sql = "SELECT cl.* FROM claim_line cl JOIN claim c ON cl.claim_id = c.claim_id WHERE cl.cpt_code = '69990' AND NOT EXISTS (SELECT 1 FROM claim_line cl2 WHERE cl2.claim_id = cl.claim_id AND cl2.cpt_code IN ('61304', '61305', '61312', '61313'))"
            exp = "Finds claims with 69990 lacking approved primary procedure"
        elif "97110" in msg or "overutilization" in msg.lower():
            sql = "SELECT c.claim_id, cl.dos, SUM(cl.units) as total_units FROM claim_line cl JOIN claim c ON cl.claim_id = c.claim_id WHERE cl.cpt_code = '97110' GROUP BY c.claim_id, cl.dos, c.patient_id HAVING SUM(cl.units) > 4"
            exp = "Identifies claims where therapeutic exercise units exceed 4 per day"
        elif "cosmetic" in msg.lower() or "service_not_covered" in msg.lower():
            sql = "SELECT cl.* FROM claim_line cl WHERE cl.cpt_code IN ('15780', '15781', '15782', '15783')"
            exp = "Finds claims with cosmetic procedure codes that are not covered"
        else:
            sql, exp = "SELECT cl.* FROM claim_line cl WHERE cl.cpt_code = '99213'", "Sample query"
        return LLMResponse(content=f'```json\n{{"sql": "{sql}", "explanation": "{exp}"}}\n```', tool_calls=[],
                          finish_reason="stop", usage=TokenUsage(prompt_tokens=400, completion_tokens=200, total_tokens=600))

    def _scorer_response(self, msg: str, tools: list[JSON] | None) -> LLMResponse:
        if tools and self._call_count % 2 == 1:
            match = re.search(r"Name: (.+?)\\n", msg)
            name = match.group(1) if match else "billing rule"
            return LLMResponse(content="I'll search for validation.", tool_calls=[
                ToolCall(id=f"call_{self._call_count}", name="web_search", arguments={"query": f"CMS {name} guidelines"})
            ], finish_reason="tool_calls", usage=TokenUsage(prompt_tokens=300, completion_tokens=100, total_tokens=400))
        conf = 85 if "69990" in msg else 78 if "97110" in msg else 72
        return LLMResponse(content=f'''```json
{{"confidence": {conf}, "sources": [{{"title": "CMS Medicare Claims Processing Manual", "url": "https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals", "snippet": "Guidelines...", "relevance": 0.9}}, {{"title": "AMA CPT Code Guidelines", "url": "https://www.ama-assn.org/practice-management/cpt", "snippet": "Official CPT...", "relevance": 0.85}}], "validation_notes": ["Rule aligns with CMS guidelines", "Confirmed by industry standards"]}}
```''', tool_calls=[], finish_reason="stop", usage=TokenUsage(prompt_tokens=400, completion_tokens=250, total_tokens=650))
