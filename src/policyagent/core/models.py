"""Data models for the policy agent system."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from policyagent.core.types import RuleClassification  # noqa: TC001 - Pydantic needs at runtime


class ParsedPage(BaseModel):
    """Parsed content from a single PDF page."""
    page_number: int
    text: str
    boxes: list[dict[str, Any]] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    """Parsed content from a PDF document."""
    path: str
    page_count: int
    pages: list[ParsedPage] = Field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)


class ExtractedRule(BaseModel):
    """A billing rule extracted from a policy document."""
    id: str
    name: str
    description: str
    classification: RuleClassification
    source_text: str
    cpt_codes: list[str] = Field(default_factory=list)
    icd10_codes: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)


class SQLRule(BaseModel):
    """A rule with its SQL implementation."""
    rule: ExtractedRule
    sql: str
    sql_formatted: str
    validation_warnings: list[str] = Field(default_factory=list)
    retry_count: int = 0


class SearchSource(BaseModel):
    """A web search source for rule validation."""
    title: str
    url: str
    snippet: str
    relevance: float = Field(ge=0.0, le=1.0, default=0.5)


class QueryResult(BaseModel):
    """Result of executing a rule's SQL query."""
    executed: bool = False
    violation_count: int = 0
    violations: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    error: str | None = None


class ScoredRule(BaseModel):
    """A rule with confidence score and sources."""
    rule: SQLRule
    confidence: float = Field(ge=0.0, le=100.0)
    sources: list[SearchSource] = Field(default_factory=list)
    validation_notes: list[str] = Field(default_factory=list)
    query_result: QueryResult = Field(default_factory=QueryResult)


class PolicyReport(BaseModel):
    """Complete report for a policy document."""
    policy_name: str
    source_path: str
    generated_at: datetime = Field(default_factory=datetime.now)
    rules: list[ScoredRule] = Field(default_factory=list)
    total_pages: int = 0
    processing_time_seconds: float = 0.0
    total_violations: int = 0

    def to_template_data(self) -> dict[str, Any]:
        """Convert to data for HTML template."""
        return {
            "policy_name": self.policy_name,
            "source_path": self.source_path,
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "total_pages": self.total_pages,
            "processing_time": f"{self.processing_time_seconds:.1f}s",
            "total_violations": self.total_violations,
            "rules": [
                {
                    "id": sr.rule.rule.id,
                    "name": sr.rule.rule.name,
                    "description": sr.rule.rule.description,
                    "classification": sr.rule.rule.classification.value,
                    "cpt_codes": sr.rule.rule.cpt_codes,
                    "source_text": sr.rule.rule.source_text,
                    "sql": sr.rule.sql_formatted,
                    "confidence": sr.confidence,
                    "sources": [{"title": s.title, "url": s.url} for s in sr.sources],
                    "violation_count": sr.query_result.violation_count,
                    "violations": sr.query_result.violations[:10],  # Limit to 10 for display
                    "columns": sr.query_result.columns,
                    "query_executed": sr.query_result.executed,
                }
                for sr in self.rules
            ],
        }
