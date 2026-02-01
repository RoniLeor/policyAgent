"""policyAgent - AI Agent for healthcare policy rule extraction.

This package provides a multi-agent pipeline for:
- Parsing PDF policy documents
- Extracting billing rules
- Generating SQL implementations
- Validating against industry standards
- Producing HTML reports
"""

from __future__ import annotations

from policyagent.config.settings import Settings
from policyagent.core.models import (
    ExtractedRule,
    ParsedDocument,
    PolicyReport,
    ScoredRule,
    SQLRule,
)
from policyagent.core.types import RuleClassification
from policyagent.orchestrator.pipeline import Pipeline
from policyagent.tools.ocr import download_models


__version__ = "0.1.0"
__author__ = "Roni"

__all__ = [
    "ExtractedRule",
    "ParsedDocument",
    "Pipeline",
    "PolicyReport",
    "RuleClassification",
    "SQLRule",
    "ScoredRule",
    "Settings",
    "download_models",
]
