import pytest
from itingen.utils.duration import parse_duration, format_duration


class TestParseDuration:
    """Test parsing duration strings to seconds."""

    def test_parse_hours_and_minutes(self):
        assert parse_duration("1h30m") == 5400
        assert parse_duration("2h15m") == 8100

    def test_parse_hours_only(self):
        assert parse_duration("3h") == 10800
        assert parse_duration("1h") == 3600

    def test_parse_minutes_only(self):
        assert parse_duration("30m") == 1800
        assert parse_duration("45m") == 2700

    def test_parse_zero_duration(self):
        assert parse_duration("0h0m") == 0
        assert parse_duration("0m") == 0

    def test_parse_with_spaces(self):
        assert parse_duration("1h 30m") == 5400
        assert parse_duration("2 h 15 m") == 8100

    def test_parse_empty_string(self):
        assert parse_duration("") is None
        assert parse_duration("   ") is None

    def test_parse_invalid_format(self):
        with pytest.raises(ValueError):
            parse_duration("invalid")
        with pytest.raises(ValueError):
            parse_duration("1x30y")


class TestFormatDuration:
    """Test formatting seconds to human-readable duration."""

    def test_format_hours_and_minutes(self):
        assert format_duration(5400) == "1h 30m"
        assert format_duration(8100) == "2h 15m"

    def test_format_hours_only(self):
        assert format_duration(3600) == "1h"
        assert format_duration(7200) == "2h"

    def test_format_minutes_only(self):
        assert format_duration(1800) == "30m"
        assert format_duration(2700) == "45m"

    def test_format_zero_duration(self):
        assert format_duration(0) == "0m"

    def test_format_seconds_rounded(self):
        # Round up to nearest minute
        assert format_duration(90) == "2m"
        assert format_duration(3659) == "1h 1m"

    def test_format_none(self):
        assert format_duration(None) is None
