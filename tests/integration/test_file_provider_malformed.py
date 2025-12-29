import pytest
from itingen.providers.file_provider import LocalFileProvider

@pytest.fixture
def malformed_trip_dir(tmp_path):
    trip_dir = tmp_path / "malformed_trip"
    events_dir = trip_dir / "events"
    events_dir.mkdir(parents=True)
    (trip_dir / "venues").mkdir()
    return trip_dir

def test_missing_event_header(malformed_trip_dir):
    """Test parsing Markdown with missing '### Event:' headers."""
    md_content = """
- date: 2025-01-01
- city: Tokyo

This is just some text.
- key: value
"""
    (malformed_trip_dir / "events" / "2025-01-01.md").write_text(md_content)
    
    provider = LocalFileProvider(malformed_trip_dir)
    events = provider.get_events()
    
    # Should probably return no events since no '### Event:' was found
    assert len(events) == 0

def test_event_with_no_fields(malformed_trip_dir):
    """Test an event block that has a header but no fields."""
    md_content = """
- date: 2025-01-01

### Event: Empty Event
"""
    (malformed_trip_dir / "events" / "2025-01-01.md").write_text(md_content)
    
    provider = LocalFileProvider(malformed_trip_dir)
    events = provider.get_events()
    
    assert len(events) == 1
    assert events[0].event_heading == "Empty Event"
    assert events[0].date == "2025-01-01"

def test_malformed_fields(malformed_trip_dir):
    """Test fields with missing colons or bad indentation."""
    md_content = """
- date: 2025-01-01

### Event: Bad Fields
- Valid Key: Value
- MissingColonValue
  - Indented: but not a list item
- Another Key : Another Value
"""
    (malformed_trip_dir / "events" / "2025-01-01.md").write_text(md_content)
    
    provider = LocalFileProvider(malformed_trip_dir)
    events = provider.get_events()
    
    assert len(events) == 1
    # Check that "Valid Key" was parsed
    assert getattr(events[0], "Valid Key") == "Value"
    # Check that "Another Key" was parsed (with spacing normalization)
    assert getattr(events[0], "Another Key") == "Another Value"
    # "MissingColonValue" should probably be ignored or handled gracefully
    assert not hasattr(events[0], "MissingColonValue")

def test_duplicate_event_headings(malformed_trip_dir):
    """Test that multiple events with the same heading are handled."""
    md_content = """
- date: 2025-01-01

### Event: Duplicate
- id: first
### Event: Duplicate
- id: second
"""
    (malformed_trip_dir / "events" / "2025-01-01.md").write_text(md_content)
    
    provider = LocalFileProvider(malformed_trip_dir)
    events = provider.get_events()
    
    assert len(events) == 2
    assert events[0].event_heading == "Duplicate"
    assert events[0].id == "first"
    assert events[1].event_heading == "Duplicate"
    assert events[1].id == "second"

def test_interleaved_text_and_events(malformed_trip_dir):
    """Test that text between event blocks doesn't break parsing."""
    md_content = """
- date: 2025-01-01

### Event: Event 1
- key1: value1

Some random text here.
More text.

### Event: Event 2
- key2: value2
"""
    (malformed_trip_dir / "events" / "2025-01-01.md").write_text(md_content)
    
    provider = LocalFileProvider(malformed_trip_dir)
    events = provider.get_events()
    
    assert len(events) == 2
    assert events[0].event_heading == "Event 1"
    assert events[1].event_heading == "Event 2"
    assert getattr(events[0], "key1") == "value1"
    assert getattr(events[1], "key2") == "value2"
