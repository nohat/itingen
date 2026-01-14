"""Tests for event grouping utility functions."""

from itingen.core.domain.events import Event
from itingen.utils.grouping import group_events_by_date


class TestGroupEventsByDate:
    """Tests for group_events_by_date function."""

    def test_groups_events_with_explicit_date(self):
        """Events with explicit date field are grouped correctly."""
        events = [
            Event(event_heading="Morning", date="2026-01-15"),
            Event(event_heading="Lunch", date="2026-01-15"),
            Event(event_heading="Dinner", date="2026-01-16"),
        ]

        result = group_events_by_date(events)

        assert len(result) == 2
        assert "2026-01-15" in result
        assert "2026-01-16" in result
        assert len(result["2026-01-15"]) == 2
        assert len(result["2026-01-16"]) == 1

    def test_extracts_date_from_time_utc(self):
        """Events without date but with time_utc have date extracted."""
        events = [
            Event(event_heading="Flight", time_utc="2026-01-15T08:00:00Z"),
            Event(event_heading="Arrival", time_utc="2026-01-15T14:00:00+12:00"),
        ]

        result = group_events_by_date(events)

        assert len(result) == 1
        assert "2026-01-15" in result
        assert len(result["2026-01-15"]) == 2

    def test_uses_tbd_for_events_without_date(self):
        """Events without date or time_utc are grouped under 'TBD'."""
        events = [
            Event(event_heading="Unknown time event"),
            Event(event_heading="Another unknown"),
        ]

        result = group_events_by_date(events)

        assert len(result) == 1
        assert "TBD" in result
        assert len(result["TBD"]) == 2

    def test_handles_invalid_time_utc_format(self):
        """Events with malformed time_utc fall back to TBD."""
        events = [
            Event(event_heading="Bad time", time_utc="not-a-date"),
        ]

        result = group_events_by_date(events)

        assert "TBD" in result

    def test_preserves_event_order_within_date(self):
        """Events within the same date maintain their original order."""
        events = [
            Event(event_heading="First", date="2026-01-15"),
            Event(event_heading="Second", date="2026-01-15"),
            Event(event_heading="Third", date="2026-01-15"),
        ]

        result = group_events_by_date(events)

        headings = [e.event_heading for e in result["2026-01-15"]]
        assert headings == ["First", "Second", "Third"]

    def test_empty_list_returns_empty_dict(self):
        """Empty event list returns empty dict."""
        result = group_events_by_date([])
        assert result == {}

    def test_explicit_date_takes_precedence_over_time_utc(self):
        """When both date and time_utc exist, explicit date is used."""
        events = [
            Event(
                event_heading="Explicit date",
                date="2026-01-20",
                time_utc="2026-01-15T10:00:00Z"
            ),
        ]

        result = group_events_by_date(events)

        assert "2026-01-20" in result
        assert "2026-01-15" not in result
