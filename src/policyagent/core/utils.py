"""Utility functions for the policy agent system."""

from __future__ import annotations

import re


def extract_json_from_response(content: str) -> str:
    """Extract JSON string from LLM response content.

    Handles JSON wrapped in markdown code blocks (```json or ```)
    or plain JSON text.

    Args:
        content: LLM response content that may contain JSON.

    Returns:
        Extracted JSON string, stripped of markdown formatting.
    """
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    return json_match.group(1).strip() if json_match else content.strip()
