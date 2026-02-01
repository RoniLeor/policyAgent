"""Converters for database rows to model objects."""

from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING, Any

from policyagent.core.models import ExtractedRule, ScoredRule, SearchSource, SQLRule
from policyagent.core.types import RuleClassification


if TYPE_CHECKING:
    from collections.abc import Iterator
    from contextlib import contextmanager


def row_to_scored_rule(
    row: sqlite3.Row, get_connection: Any
) -> ScoredRule:
    """Convert database row to ScoredRule object."""
    with get_connection() as conn:
        cpt_rows = conn.execute(
            "SELECT cpt_code FROM rule_cpt_codes WHERE rule_id = ?", (row["id"],)
        ).fetchall()
        cpt_codes = [r["cpt_code"] for r in cpt_rows]

        icd_rows = conn.execute(
            "SELECT icd10_code FROM rule_icd10_codes WHERE rule_id = ?", (row["id"],)
        ).fetchall()
        icd10_codes = [r["icd10_code"] for r in icd_rows]

        mod_rows = conn.execute(
            "SELECT modifier FROM rule_modifiers WHERE rule_id = ?", (row["id"],)
        ).fetchall()
        modifiers = [r["modifier"] for r in mod_rows]

    extracted = ExtractedRule(
        id=row["id"],
        name=row["name"],
        description=row["description"] or "",
        classification=RuleClassification(row["classification"]),
        source_text=row["source_text"] or "",
        cpt_codes=cpt_codes,
        icd10_codes=icd10_codes,
        modifiers=modifiers,
        conditions=[],
    )

    sql_rule = SQLRule(
        rule=extracted,
        sql=row["sql_query"] or "",
        sql_formatted=row["sql_formatted"] or "",
        validation_warnings=[],
        retry_count=0,
    )

    sources_data = json.loads(row["sources"] or "[]")
    sources = [SearchSource(**s) for s in sources_data]
    validation_notes = json.loads(row["validation_notes"] or "[]")

    return ScoredRule(
        rule=sql_rule,
        confidence=row["confidence"],
        sources=sources,
        validation_notes=validation_notes,
    )
