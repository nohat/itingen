"""
Unit tests for fingerprint utility.

Tests the compute_fingerprint function that generates stable SHA256 hashes
for payload caching in AI and Maps API integrations.
"""

import pytest
from itingen.utils.fingerprint import compute_fingerprint


class TestFingerprint:
    """Test fingerprint generation utility."""

    def test_fingerprint_stable(self):
        """Fingerprints are stable for identical inputs."""
        payload = {"prompt": "test", "model": "gemini"}
        fp1 = compute_fingerprint(payload)
        fp2 = compute_fingerprint(payload)
        assert fp1 == fp2

    def test_fingerprint_changes_on_modification(self):
        """Fingerprints change when payload changes."""
        payload1 = {"prompt": "test1", "model": "gemini"}
        payload2 = {"prompt": "test2", "model": "gemini"}
        assert compute_fingerprint(payload1) != compute_fingerprint(payload2)

    def test_fingerprint_key_order_independent(self):
        """Fingerprints ignore key order (sorted serialization)."""
        payload1 = {"a": 1, "b": 2}
        payload2 = {"b": 2, "a": 1}
        assert compute_fingerprint(payload1) == compute_fingerprint(payload2)

    def test_fingerprint_returns_hex_string(self):
        """Fingerprint returns a hex-encoded SHA256 hash."""
        payload = {"test": "data"}
        fp = compute_fingerprint(payload)
        # SHA256 hex digest is 64 characters
        assert len(fp) == 64
        # All characters should be valid hex
        assert all(c in "0123456789abcdef" for c in fp)

    def test_fingerprint_nested_structures(self):
        """Fingerprints handle nested data structures."""
        payload = {
            "outer": {
                "inner": {
                    "deep": ["list", "of", "items"]
                }
            }
        }
        fp = compute_fingerprint(payload)
        assert len(fp) == 64

    def test_fingerprint_list_payload(self):
        """Fingerprints work with list payloads."""
        payload = ["a", "b", "c"]
        fp1 = compute_fingerprint(payload)
        fp2 = compute_fingerprint(payload)
        assert fp1 == fp2

    def test_fingerprint_string_payload(self):
        """Fingerprints work with string payloads."""
        payload = "simple string"
        fp1 = compute_fingerprint(payload)
        fp2 = compute_fingerprint(payload)
        assert fp1 == fp2

    def test_fingerprint_number_payload(self):
        """Fingerprints work with numeric payloads."""
        payload = 42
        fp1 = compute_fingerprint(payload)
        fp2 = compute_fingerprint(payload)
        assert fp1 == fp2
