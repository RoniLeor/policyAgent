"""Core type definitions and enums."""

from __future__ import annotations

from enum import Enum
from typing import TypeAlias


# Type aliases for clarity
JSON: TypeAlias = dict[str, "JSONValue"]
JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | JSON


class RuleClassification(str, Enum):
    """Classification types for billing rules."""

    MUTUAL_EXCLUSION = "mutual_exclusion"
    OVERUTILIZATION = "overutilization"
    SERVICE_NOT_COVERED = "service_not_covered"


class AgentRole(str, Enum):
    """Roles for agents in the pipeline."""

    PARSER = "parser"
    ANALYZER = "analyzer"
    SQLGEN = "sqlgen"
    SCORER = "scorer"
    REPORTER = "reporter"


class MessageRole(str, Enum):
    """Roles for messages in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
