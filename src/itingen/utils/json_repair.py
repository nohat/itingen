"""
JSON repair utility (TD-002).

Handles common LLM JSON formatting issues, particularly trailing commas
in objects and arrays. Also extracts JSON from markdown code fences and
surrounding text.
"""

import re
from typing import Optional


def extract_json(text: str) -> Optional[str]:
    """
    Extract and repair JSON from text that may contain markdown or surrounding content.

    This function:
    1. Strips markdown code fences (```json or ```)
    2. Finds JSON boundaries ([ or { to ] or })
    3. Repairs trailing commas in objects and arrays (TD-002)

    Args:
        text: Input text that may contain JSON, possibly in markdown code fence

    Returns:
        Repaired JSON string, or None if no valid JSON structure found

    Example:
        >>> extract_json('{"key": "value",}')
        '{"key": "value"}'

        >>> extract_json('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'

        >>> extract_json('Here is: {"a": 1} and more')
        '{"a": 1}'
    """
    if not text:
        return None

    t = text.strip()

    # Remove markdown code fences
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```\s*$", "", t)

    # Find JSON boundaries
    start = None
    for ch in ("[", "{"):
        i = t.find(ch)
        if i != -1:
            start = i if start is None else min(start, i)

    if start is None:
        return None

    end = max(t.rfind("]"), t.rfind("}"))
    if end == -1 or end <= start:
        return None

    json_str = t[start : end + 1].strip()

    # TD-002: Repair trailing commas in objects and arrays
    # Regex: comma followed by optional whitespace and closing bracket/brace
    json_str = re.sub(r",\s*([\]}])", r"\1", json_str)

    return json_str
