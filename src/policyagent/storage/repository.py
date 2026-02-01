"""SQLite-based rule repository with indexed search."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from policyagent.core.models import ScoredRule
from policyagent.core.types import RuleClassification
from policyagent.storage.converters import row_to_scored_rule
from policyagent.storage.schema import INIT_SCHEMA


if TYPE_CHECKING:
    from collections.abc import Iterator


class RuleRepository:
    """SQLite repository for storing and retrieving billing rules."""

    def __init__(self, db_path: str | Path = "rules.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.executescript(INIT_SCHEMA)

    def save_rule(self, vendor: str, scored_rule: ScoredRule) -> str:
        rule = scored_rule.rule.rule
        sql_rule = scored_rule.rule
        with self._connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO rules
                (id, vendor, name, description, classification, source_text,
                 sql_query, sql_formatted, confidence, validation_notes, sources, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (rule.id, vendor, rule.name, rule.description, rule.classification.value,
                 rule.source_text, sql_rule.sql, sql_rule.sql_formatted, scored_rule.confidence,
                 json.dumps(scored_rule.validation_notes),
                 json.dumps([s.model_dump() for s in scored_rule.sources]),
                 datetime.now().isoformat()),
            )
            conn.execute("DELETE FROM rule_cpt_codes WHERE rule_id = ?", (rule.id,))
            for cpt in rule.cpt_codes:
                conn.execute("INSERT INTO rule_cpt_codes VALUES (?, ?)", (rule.id, cpt))
            conn.execute("DELETE FROM rule_icd10_codes WHERE rule_id = ?", (rule.id,))
            for icd in rule.icd10_codes:
                conn.execute("INSERT INTO rule_icd10_codes VALUES (?, ?)", (rule.id, icd))
            conn.execute("DELETE FROM rule_modifiers WHERE rule_id = ?", (rule.id,))
            for mod in rule.modifiers:
                conn.execute("INSERT INTO rule_modifiers VALUES (?, ?)", (rule.id, mod))
        return rule.id

    def save_rules(self, vendor: str, rules: list[ScoredRule]) -> list[str]:
        return [self.save_rule(vendor, r) for r in rules]

    def find_by_cpt_code(self, cpt_code: str) -> list[ScoredRule]:
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT DISTINCT r.* FROM rules r
                JOIN rule_cpt_codes c ON r.id = c.rule_id
                WHERE c.cpt_code = ? ORDER BY r.confidence DESC""", (cpt_code,)
            ).fetchall()
        return [row_to_scored_rule(r, self._connection) for r in rows]

    def find_by_cpt_codes(self, cpt_codes: list[str]) -> list[ScoredRule]:
        if not cpt_codes:
            return []
        ph = ",".join("?" * len(cpt_codes))
        with self._connection() as conn:
            rows = conn.execute(
                f"""SELECT DISTINCT r.* FROM rules r
                JOIN rule_cpt_codes c ON r.id = c.rule_id
                WHERE c.cpt_code IN ({ph}) ORDER BY r.confidence DESC""", cpt_codes
            ).fetchall()
        return [row_to_scored_rule(r, self._connection) for r in rows]

    def find_by_classification(self, classification: RuleClassification) -> list[ScoredRule]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM rules WHERE classification = ? ORDER BY confidence DESC",
                (classification.value,)
            ).fetchall()
        return [row_to_scored_rule(r, self._connection) for r in rows]

    def find_by_vendor(self, vendor: str) -> list[ScoredRule]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM rules WHERE vendor = ? ORDER BY id", (vendor,)
            ).fetchall()
        return [row_to_scored_rule(r, self._connection) for r in rows]

    def search_text(self, query: str, limit: int = 20) -> list[ScoredRule]:
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT r.* FROM rules r JOIN rules_fts fts ON r.id = fts.id
                WHERE rules_fts MATCH ? ORDER BY rank LIMIT ?""", (query, limit)
            ).fetchall()
        return [row_to_scored_rule(r, self._connection) for r in rows]

    def search(
        self, cpt_codes: list[str] | None = None, icd10_codes: list[str] | None = None,
        classification: RuleClassification | None = None, vendor: str | None = None,
        text_query: str | None = None, min_confidence: float = 0.0
    ) -> list[ScoredRule]:
        conditions, params, joins = ["r.confidence >= ?"], [min_confidence], []
        if cpt_codes:
            joins.append("JOIN rule_cpt_codes cpt ON r.id = cpt.rule_id")
            conditions.append(f"cpt.cpt_code IN ({','.join('?' * len(cpt_codes))})")
            params.extend(cpt_codes)
        if icd10_codes:
            joins.append("JOIN rule_icd10_codes icd ON r.id = icd.rule_id")
            conditions.append(f"icd.icd10_code IN ({','.join('?' * len(icd10_codes))})")
            params.extend(icd10_codes)
        if classification:
            conditions.append("r.classification = ?")
            params.append(classification.value)
        if vendor:
            conditions.append("r.vendor = ?")
            params.append(vendor)
        if text_query:
            joins.append("JOIN rules_fts fts ON r.id = fts.id")
            conditions.append("rules_fts MATCH ?")
            params.append(text_query)
        query = f"SELECT DISTINCT r.* FROM rules r {' '.join(joins)} WHERE {' AND '.join(conditions)} ORDER BY r.confidence DESC"
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [row_to_scored_rule(r, self._connection) for r in rows]

    def get_all_vendors(self) -> list[str]:
        with self._connection() as conn:
            rows = conn.execute("SELECT DISTINCT vendor FROM rules ORDER BY vendor").fetchall()
        return [r["vendor"] for r in rows]

    def get_stats(self) -> dict[str, Any]:
        with self._connection() as conn:
            total = conn.execute("SELECT COUNT(*) as cnt FROM rules").fetchone()["cnt"]
            by_class = conn.execute(
                "SELECT classification, COUNT(*) as cnt FROM rules GROUP BY classification"
            ).fetchall()
            by_vendor = conn.execute(
                "SELECT vendor, COUNT(*) as cnt FROM rules GROUP BY vendor"
            ).fetchall()
            avg_conf = conn.execute("SELECT AVG(confidence) as avg FROM rules").fetchone()["avg"]
        return {
            "total_rules": total,
            "by_classification": {r["classification"]: r["cnt"] for r in by_class},
            "by_vendor": {r["vendor"]: r["cnt"] for r in by_vendor},
            "average_confidence": round(avg_conf or 0, 1),
        }

    def delete_vendor(self, vendor: str) -> int:
        with self._connection() as conn:
            result = conn.execute("DELETE FROM rules WHERE vendor = ?", (vendor,))
            return result.rowcount
