"""SQL validation and execution tool."""

from __future__ import annotations

import logging
from typing import Any

import sqlglot

from policyagent.config.schema import CLAIMS_SCHEMA
from policyagent.core.response import ToolResult
from policyagent.core.tool import Tool


logger = logging.getLogger(__name__)


class SQLTool(Tool):
    """Tool for validating and parsing SQL queries."""

    name = "sql_validator"
    description = "Validate SQL syntax and check against the claims database schema."

    def __init__(self) -> None:
        """Initialize SQL tool."""
        self._schema_tables = self._parse_schema()

    def _parse_schema(self) -> dict[str, list[str]]:
        """Parse schema to extract table and column names."""
        tables: dict[str, list[str]] = {}

        for raw_line in CLAIMS_SCHEMA.strip().split("\n"):
            line = raw_line.strip()
            if line.startswith("CREATE TABLE"):
                # Extract table name and columns
                # Format: CREATE TABLE name (col1, col2, ...);
                parts = line.replace("CREATE TABLE ", "").replace(");", "").split("(")
                if len(parts) == 2:
                    table_name = parts[0].strip()
                    columns = [c.strip() for c in parts[1].split(",")]
                    tables[table_name] = columns

        return tables

    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL query to validate.",
                },
            },
            "required": ["sql"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Validate a SQL query.

        Args:
            **kwargs: Must include 'sql'.

        Returns:
            ToolResult with validation status and parsed query info.
        """
        sql = kwargs.get("sql")
        if not sql:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing required parameter: sql",
            )

        try:
            validation = self._validate_sql(sql)
            return ToolResult(
                tool_name=self.name,
                success=validation["is_valid"],
                output=validation,
                error=validation.get("error"),
            )
        except Exception as e:
            logger.exception("SQL validation failed")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"SQL validation failed: {e}",
            )

    def _validate_sql(self, sql: str) -> dict[str, Any]:
        """Validate SQL query syntax and schema references.

        Args:
            sql: SQL query string.

        Returns:
            Dictionary with validation results.
        """
        result: dict[str, Any] = {
            "is_valid": False,
            "sql": sql,
            "tables_used": [],
            "columns_used": [],
            "warnings": [],
            "error": None,
        }

        # Parse SQL
        try:
            parsed = sqlglot.parse_one(sql)
        except sqlglot.errors.ParseError as e:
            result["error"] = f"SQL syntax error: {e}"
            return result

        # Extract tables
        tables_used: list[str] = []
        for table in parsed.find_all(sqlglot.exp.Table):
            table_name = table.name.lower()
            tables_used.append(table_name)
            if table_name not in self._schema_tables:
                result["warnings"].append(f"Unknown table: {table_name}")

        result["tables_used"] = list(set(tables_used))

        # Extract columns
        columns_used: list[str] = []
        for column in parsed.find_all(sqlglot.exp.Column):
            col_name = column.name.lower()
            columns_used.append(col_name)

            # Check if column exists in any referenced table
            col_found = False
            table_ref = column.table.lower() if column.table else None

            if table_ref and table_ref in self._schema_tables:
                if col_name in self._schema_tables[table_ref]:
                    col_found = True
            else:
                # Check all tables
                for table_cols in self._schema_tables.values():
                    if col_name in table_cols:
                        col_found = True
                        break

            if not col_found:
                result["warnings"].append(f"Unknown column: {col_name}")

        result["columns_used"] = list(set(columns_used))

        # Mark as valid if no errors
        if not result["error"]:
            result["is_valid"] = True

        return result

    def format_sql(self, sql: str) -> str:
        """Format SQL query for readability.

        Args:
            sql: SQL query string.

        Returns:
            Formatted SQL string.
        """
        try:
            parsed = sqlglot.parse_one(sql)
            return parsed.sql(pretty=True)
        except Exception:
            return sql
