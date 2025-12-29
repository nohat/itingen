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
    2. Finds a balanced JSON structure ([ or { to matching ] or })
    3. Repairs trailing commas in objects and arrays (TD-002)

    Args:
        text: Input text that may contain JSON, possibly in markdown code fence

    Returns:
        Repaired JSON string, or None if no valid JSON structure found
    """
    if not text:
        return None

    t = text.strip()

    # Remove markdown code fences
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```\s*$", "", t)

    # Find first JSON boundary
    start = -1
    for i, ch in enumerate(t):
        if ch in ("[", "{"):
            start = i
            break

    if start == -1:
        return None

    # Find matching closing bracket with basic counting
    # Note: This doesn't handle brackets inside strings perfectly,
    # but is much better than rfind.
    bracket_stack = []
    end = -1
    in_string = False
    escape = False

    for i in range(start, len(t)):
        ch = t[i]
        
        if escape:
            escape = False
            continue
            
        if ch == '"':
            in_string = not in_string
            continue
            
        if in_string:
            if ch == '\\':
                escape = True
            continue

        if ch in ("[", "{"):
            bracket_stack.append(ch)
        elif ch == "]":
            if bracket_stack and bracket_stack[-1] == "[":
                bracket_stack.pop()
            else:
                return None # Unbalanced
        elif ch == "}":
            if bracket_stack and bracket_stack[-1] == "{":
                bracket_stack.pop()
            else:
                return None # Unbalanced

        if not bracket_stack:
            end = i
            break

    if end == -1:
        return None

    json_str = t[start : end + 1].strip()

    # TD-002: Repair trailing commas in objects and arrays
    # Regex: comma followed by optional whitespace and closing bracket/brace
    json_str = re.sub(r",\s*([\]}])", r"\1", json_str)

    return json_str
