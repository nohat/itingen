"""
Unit tests for JSON repair utility (TD-002).

Tests the LLM JSON parsing fix that handles trailing commas in objects and arrays.
"""

import json
from itingen.utils.json_repair import extract_json


class TestJsonRepair:
    """Test JSON repair functionality."""

    def test_repair_trailing_comma_object(self):
        """TD-002: Fix trailing comma in JSON object."""
        malformed = '{"key": "value",}'
        repaired = extract_json(malformed)
        assert repaired is not None
        parsed = json.loads(repaired)
        assert parsed == {"key": "value"}

    def test_repair_trailing_comma_array(self):
        """TD-002: Fix trailing comma in JSON array."""
        malformed = '["a", "b",]'
        repaired = extract_json(malformed)
        assert repaired is not None
        parsed = json.loads(repaired)
        assert parsed == ["a", "b"]

    def test_repair_multiple_trailing_commas(self):
        """TD-002: Fix multiple trailing commas in nested structures."""
        malformed = '{"a": [1, 2,], "b": "c",}'
        repaired = extract_json(malformed)
        assert repaired is not None
        parsed = json.loads(repaired)
        assert parsed == {"a": [1, 2], "b": "c"}

    def test_no_change_valid_json(self):
        """TD-002: Don't modify valid JSON."""
        valid = '{"key": "value"}'
        repaired = extract_json(valid)
        assert repaired == valid

    def test_extract_from_markdown_code_fence(self):
        """Extract JSON from markdown code fence."""
        markdown = '''```json
{"key": "value"}
```'''
        repaired = extract_json(markdown)
        assert repaired is not None
        parsed = json.loads(repaired)
        assert parsed == {"key": "value"}

    def test_extract_from_code_fence_no_language(self):
        """Extract JSON from code fence without language specifier."""
        markdown = '''```
{"key": "value"}
```'''
        repaired = extract_json(markdown)
        assert repaired is not None
        parsed = json.loads(repaired)
        assert parsed == {"key": "value"}

    def test_extract_json_with_surrounding_text(self):
        """Extract JSON embedded in surrounding text."""
        text = 'Here is some JSON: {"key": "value"} and more text'
        repaired = extract_json(text)
        assert repaired is not None
        parsed = json.loads(repaired)
        assert parsed == {"key": "value"}

    def test_extract_array_with_surrounding_text(self):
        """Extract JSON array embedded in text."""
        text = 'Result: ["a", "b", "c"] is the answer'
        repaired = extract_json(text)
        assert repaired is not None
        parsed = json.loads(repaired)
        assert parsed == ["a", "b", "c"]

    def test_return_none_for_empty_string(self):
        """Return None for empty input."""
        assert extract_json("") is None
        assert extract_json("   ") is None

    def test_return_none_for_no_json(self):
        """Return None when no JSON found."""
        assert extract_json("just plain text") is None

    def test_nested_structures_with_trailing_commas(self):
        """Handle deeply nested structures with trailing commas."""
        malformed = '{"outer": {"inner": [1, 2, 3,],},}'
        repaired = extract_json(malformed)
        assert repaired is not None
        parsed = json.loads(repaired)
        assert parsed == {"outer": {"inner": [1, 2, 3]}}

    def test_extract_single_structure_from_text(self):
        """Extract a single JSON structure when embedded in text.

        Note: When multiple separate JSON structures exist, the function
        extracts from first opening to last closing bracket, which may not
        be valid JSON. This matches the original implementation behavior.
        """
        text = 'Result is: {"key": "value"} (end)'
        repaired = extract_json(text)
        assert repaired is not None
        parsed = json.loads(repaired)
        assert parsed == {"key": "value"}

    def test_extract_first_valid_json_with_multiple_structures(self):
        """Extract only the first valid JSON structure when multiple exist."""
        text = 'Here is [1, 2] and then {"a": 1}'
        repaired = extract_json(text)
        assert repaired is not None
        # Currently this would return '[1, 2] and then {"a": 1}' which is invalid
        parsed = json.loads(repaired)
        assert parsed == [1, 2]
