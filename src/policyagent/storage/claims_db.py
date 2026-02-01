"""Claims database for executing rule queries."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

CLAIMS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS patient (
    patient_id TEXT PRIMARY KEY,
    dob DATE,
    gender TEXT
);

CREATE TABLE IF NOT EXISTS provider (
    npi TEXT PRIMARY KEY,
    tin TEXT
);

CREATE TABLE IF NOT EXISTS claim (
    claim_id TEXT PRIMARY KEY,
    patient_id TEXT,
    provider_npi TEXT,
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    FOREIGN KEY (provider_npi) REFERENCES provider(npi)
);

CREATE TABLE IF NOT EXISTS claim_line (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT,
    dos DATE,
    pos TEXT,
    icd10 TEXT,
    cpt_code TEXT,
    units INTEGER DEFAULT 1,
    amount REAL,
    modifiers TEXT,
    FOREIGN KEY (claim_id) REFERENCES claim(claim_id)
);

CREATE INDEX IF NOT EXISTS idx_claim_line_claim_id ON claim_line(claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_line_cpt ON claim_line(cpt_code);
CREATE INDEX IF NOT EXISTS idx_claim_line_dos ON claim_line(dos);
"""


class ClaimsDatabase:
    """SQLite claims database for rule query execution."""

    def __init__(self, db_path: str | Path = "claims.db") -> None:
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
            conn.executescript(CLAIMS_SCHEMA_SQL)

    def execute_query(self, sql: str, limit: int = 100) -> dict[str, Any]:
        """Execute a SQL query and return results.

        Args:
            sql: SQL query to execute.
            limit: Maximum rows to return.

        Returns:
            Dict with columns, rows, and count.
        """
        try:
            # Add LIMIT if not present
            sql_lower = sql.lower().strip()
            if "limit" not in sql_lower:
                sql = f"{sql.rstrip(';')} LIMIT {limit}"

            with self._connection() as conn:
                cursor = conn.execute(sql)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = [dict(row) for row in cursor.fetchall()]

            return {"success": True, "columns": columns, "rows": rows, "count": len(rows)}
        except sqlite3.Error as e:
            return {"success": False, "error": str(e), "columns": [], "rows": [], "count": 0}

    def load_sample_data(self) -> None:
        """Load sample claims data for testing."""
        with self._connection() as conn:
            # Check if data exists
            count = conn.execute("SELECT COUNT(*) FROM claim").fetchone()[0]
            if count > 0:
                return

            # Sample patients
            conn.executemany("INSERT INTO patient VALUES (?, ?, ?)", [
                ("P001", "1985-03-15", "M"), ("P002", "1990-07-22", "F"),
                ("P003", "1978-11-30", "M"), ("P004", "2000-01-10", "F"),
            ])

            # Sample providers
            conn.executemany("INSERT INTO provider VALUES (?, ?)", [
                ("1234567890", "12-3456789"), ("0987654321", "98-7654321"),
            ])

            # Sample claims with violations
            conn.executemany("INSERT INTO claim VALUES (?, ?, ?)", [
                ("CLM001", "P001", "1234567890"), ("CLM002", "P002", "1234567890"),
                ("CLM003", "P003", "0987654321"), ("CLM004", "P004", "0987654321"),
                ("CLM005", "P001", "1234567890"), ("CLM006", "P002", "0987654321"),
            ])

            # Claim lines - some violate rules
            conn.executemany(
                "INSERT INTO claim_line (claim_id, dos, pos, icd10, cpt_code, units, amount, modifiers) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    # CLM001: 69990 without required primary procedure (violation)
                    ("CLM001", "2024-01-15", "11", "H35.30", "69990", 1, 500.00, None),
                    # CLM002: 69990 WITH required primary procedure (OK)
                    ("CLM002", "2024-01-16", "11", "H35.30", "61304", 1, 2000.00, None),
                    ("CLM002", "2024-01-16", "11", "H35.30", "69990", 1, 500.00, None),
                    # CLM003: 97110 with 6 units (violation - exceeds 4)
                    ("CLM003", "2024-01-17", "11", "M54.5", "97110", 6, 180.00, None),
                    # CLM004: 97110 with 3 units (OK)
                    ("CLM004", "2024-01-18", "11", "M54.5", "97110", 3, 90.00, None),
                    # CLM005: Cosmetic procedure (violation)
                    ("CLM005", "2024-01-19", "11", "L90.5", "15780", 1, 1500.00, None),
                    # CLM006: Normal procedure (OK)
                    ("CLM006", "2024-01-20", "11", "J06.9", "99213", 1, 150.00, None),
                ])

    def get_stats(self) -> dict[str, int]:
        """Get database statistics."""
        with self._connection() as conn:
            return {
                "patients": conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0],
                "providers": conn.execute("SELECT COUNT(*) FROM provider").fetchone()[0],
                "claims": conn.execute("SELECT COUNT(*) FROM claim").fetchone()[0],
                "claim_lines": conn.execute("SELECT COUNT(*) FROM claim_line").fetchone()[0],
            }
