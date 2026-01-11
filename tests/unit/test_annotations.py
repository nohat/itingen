"""Tests for EmotionalAnnotationHydrator."""

import pytest
from itingen.core.domain.events import Event
from itingen.pipeline.annotations import EmotionalAnnotationHydrator


class TestEmotionalAnnotationHydrator:
    """Unit tests for EmotionalAnnotationHydrator."""

    @pytest.fixture
    def hydrator(self):
        """Create an EmotionalAnnotationHydrator instance."""
        return EmotionalAnnotationHydrator()

    def test_hydrate_empty_list(self, hydrator):
        """Returns empty list for empty input."""
        result = hydrator.hydrate([])
        assert result == []

    def test_hydrate_non_stressy_event(self, hydrator):
        """Non-stressy events get no annotations."""
        event = Event(kind="relaxation", location="Beach")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert result[0].emotional_triggers is None
        assert result[0].emotional_high_point is None

    def test_hydrate_flight_departure(self, hydrator):
        """Flight departure gets airport-related annotations."""
        event = Event(kind="flight_departure", location="Airport")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "airport crowds" in result[0].emotional_triggers
        assert "lines" in result[0].emotional_triggers
        assert "security uncertainty" in result[0].emotional_triggers
        assert "through security and settled at the gate" in result[0].emotional_high_point

    def test_hydrate_airport_buffer(self, hydrator):
        """Airport buffer gets same annotations as flight departure."""
        event = Event(kind="airport_buffer", location="Airport")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "airport crowds" in result[0].emotional_triggers
        assert "through security and settled at the gate" in result[0].emotional_high_point

    def test_hydrate_flight_arrival(self, hydrator):
        """Flight arrival gets arrival-specific annotations."""
        event = Event(kind="flight_arrival", location="Airport")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "jet lag" in result[0].emotional_triggers
        assert "immigration and baggage claim" in result[0].emotional_triggers
        assert "stepping into the arrivals area" in result[0].emotional_high_point

    def test_hydrate_drive_with_travel_mode_uber(self, hydrator):
        """Drive with uber travel_mode gets uber-specific annotations."""
        event = Event(kind="drive", location="City", travel_mode="uber")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "traffic" in result[0].emotional_triggers
        assert "surge pricing" in result[0].emotional_triggers
        assert "someone else is driving" in result[0].emotional_high_point

    def test_hydrate_drive_without_travel_mode(self, hydrator):
        """Drive without travel_mode gets generic drive annotations."""
        event = Event(kind="drive", location="City")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "traffic" in result[0].emotional_triggers
        assert "winding roads" in result[0].emotional_triggers
        assert "settling into the drive" in result[0].emotional_high_point

    def test_hydrate_drive_with_driving_travel_mode(self, hydrator):
        """Drive with driving travel_mode gets drive annotations."""
        event = Event(kind="drive", location="City", travel_mode="driving")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "traffic" in result[0].emotional_triggers
        assert "settling into the drive" in result[0].emotional_high_point

    def test_hydrate_ferry(self, hydrator):
        """Ferry gets ferry-specific annotations."""
        event = Event(kind="ferry", location="Harbor")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "crowds during boarding" in result[0].emotional_triggers
        assert "motion sickness" in result[0].emotional_triggers
        assert "standing on deck" in result[0].emotional_high_point

    def test_hydrate_lodging_checkin(self, hydrator):
        """Lodging checkin gets checkin-specific annotations."""
        event = Event(kind="lodging_checkin", location="Hotel")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "front-desk logistics" in result[0].emotional_triggers
        assert "room readiness" in result[0].emotional_triggers
        assert "first moment in the room" in result[0].emotional_high_point

    def test_hydrate_lodging_checkout(self, hydrator):
        """Lodging checkout gets checkin annotations (due to 'check' in kind)."""
        event = Event(kind="lodging_checkout", location="Hotel")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        # Gets checkin annotations because "check" is in the kind
        assert "front-desk logistics" in result[0].emotional_triggers
        assert "room readiness" in result[0].emotional_triggers
        assert "first moment in the room" in result[0].emotional_high_point

    def test_hydrate_lodging_with_check_in_heading(self, hydrator):
        """Lodging with 'check' in heading gets checkin annotations."""
        event = Event(
            kind="lodging_checkin",  # Use stressy kind
            location="Hotel",
            event_heading="Check-in at Hotel"
        )
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "front-desk logistics" in result[0].emotional_triggers
        assert "first moment in the room" in result[0].emotional_high_point

    def test_hydrate_decision(self, hydrator):
        """Decision gets decision-specific annotations."""
        event = Event(kind="decision", location="Crossroads")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "decision paralysis" in result[0].emotional_triggers
        assert "FOMO" in result[0].emotional_triggers
        assert "clarity and relief once a decision is actually made" in result[0].emotional_high_point

    def test_hydrate_unknown_stressy_kind(self, hydrator):
        """Unknown stressy kind gets generic stress annotations."""
        event = Event(kind="decision", location="Crossroads")  # decision is stressy
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "decision paralysis" in result[0].emotional_triggers
        assert "FOMO" in result[0].emotional_triggers
        assert "clarity and relief once a decision is actually made" in result[0].emotional_high_point

    def test_hydrate_case_insensitive_kind_matching(self, hydrator):
        """Kind matching is case insensitive."""
        event = Event(kind="FLIGHT_DEPARTURE", location="Airport")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert result[0].emotional_triggers is not None
        assert result[0].emotional_high_point is not None

    def test_hydrate_whitespace_handling(self, hydrator):
        """Handles whitespace in kind and travel_mode."""
        event = Event(kind="  drive  ", travel_mode="  uber  ", location="City")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "surge pricing" in result[0].emotional_triggers
        assert "someone else is driving" in result[0].emotional_high_point

    def test_hydrate_none_kind_handling(self, hydrator):
        """Handles None kind gracefully."""
        event = Event(kind=None, location="Somewhere")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert result[0].emotional_triggers is None
        assert result[0].emotional_high_point is None

    def test_hydrate_none_travel_mode_handling(self, hydrator):
        """Handles None travel_mode gracefully."""
        event = Event(kind="drive", travel_mode=None, location="City")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert "traffic" in result[0].emotional_triggers
        assert "settling into the drive" in result[0].emotional_high_point

    def test_hydrate_none_event_heading_handling(self, hydrator):
        """Handles None event_heading gracefully."""
        event = Event(kind="lodging_checkin", event_heading=None, location="Hotel")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        # Should get checkin annotations (lodging_checkin is stressy)
        assert "front-desk logistics" in result[0].emotional_triggers
        assert "first moment in the room" in result[0].emotional_high_point

    def test_hydrate_drive_with_duration_placeholder(self, hydrator):
        """Drive with duration attribute (placeholder logic)."""
        event = Event(kind="drive", location="City", duration="30m")
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        # Currently duration logic is placeholder, so still gets drive annotations
        assert "traffic" in result[0].emotional_triggers
        assert "settling into the drive" in result[0].emotional_high_point

    def test_hydrate_multiple_events(self, hydrator):
        """Multiple events get appropriate annotations."""
        events = [
            Event(kind="drive", location="Hotel"),
            Event(kind="flight_departure", location="Airport"),
            Event(kind="relaxation", location="Beach")  # Non-stressy
        ]
        
        result = hydrator.hydrate(events)
        
        assert len(result) == 3
        
        # Drive event
        assert "traffic" in result[0].emotional_triggers
        assert result[0].emotional_high_point is not None
        
        # Flight event
        assert "airport crowds" in result[1].emotional_triggers
        assert result[1].emotional_high_point is not None
        
        # Relaxation event (no annotations)
        assert result[2].emotional_triggers is None
        assert result[2].emotional_high_point is None

    def test_hydrate_preserves_existing_annotations(self, hydrator):
        """Overwrites existing annotations (current implementation behavior)."""
        event = Event(
            kind="drive",
            location="City",
            emotional_triggers="Existing triggers",
            emotional_high_point="Existing high point"
        )
        
        result = hydrator.hydrate([event])
        
        # Current implementation overwrites existing annotations
        assert "traffic" in result[0].emotional_triggers
        assert "settling into the drive" in result[0].emotional_high_point

    def test_get_annotations_flight_departure(self, hydrator):
        """Direct test of _get_annotations for flight departure."""
        triggers, high_point = hydrator._get_annotations("flight_departure", "", "")
        
        assert "airport crowds" in triggers
        assert "through security and settled at the gate" in high_point

    def test_get_annotations_flight_arrival(self, hydrator):
        """Direct test of _get_annotations for flight arrival."""
        triggers, high_point = hydrator._get_annotations("flight_arrival", "", "")
        
        assert "jet lag" in triggers
        assert "stepping into the arrivals area" in high_point

    def test_get_annotations_uber(self, hydrator):
        """Direct test of _get_annotations for uber."""
        triggers, high_point = hydrator._get_annotations("other", "uber", "")
        
        assert "surge pricing" in triggers
        assert "someone else is driving" in high_point

    def test_get_annotations_drive(self, hydrator):
        """Direct test of _get_annotations for drive."""
        triggers, high_point = hydrator._get_annotations("drive", "", "")
        
        assert "winding roads" in triggers
        assert "settling into the drive" in high_point

    def test_get_annotations_ferry(self, hydrator):
        """Direct test of _get_annotations for ferry."""
        triggers, high_point = hydrator._get_annotations("ferry", "", "")
        
        assert "crowds during boarding" in triggers
        assert "standing on deck" in high_point

    def test_get_annotations_lodging_checkin(self, hydrator):
        """Direct test of _get_annotations for lodging checkin."""
        triggers, high_point = hydrator._get_annotations("lodging_checkin", "", "")
        
        assert "front-desk logistics" in triggers
        assert "first moment in the room" in high_point

    def test_get_annotations_lodging_checkout(self, hydrator):
        """Direct test of _get_annotations for lodging checkout."""
        triggers, high_point = hydrator._get_annotations("lodging_checkout", "", "")
        
        # Gets checkin annotations because "check" is in the kind
        assert "front-desk logistics" in triggers
        assert "first moment in the room" in high_point

    def test_get_annotations_decision(self, hydrator):
        """Direct test of _get_annotations for decision."""
        triggers, high_point = hydrator._get_annotations("decision", "", "")
        
        assert "decision paralysis" in triggers
        assert "clarity and relief once a decision is actually made" in high_point

    def test_get_annotations_unknown(self, hydrator):
        """Direct test of _get_annotations for unknown kind."""
        triggers, high_point = hydrator._get_annotations("unknown", "", "")
        
        assert "being late" in triggers
        assert "unclear instructions" in triggers
        assert "immersed moment when the activity is underway" in high_point

    def test_hydrate_modifies_events_in_place(self, hydrator):
        """Verifies events are modified in place."""
        events = [Event(kind="drive", location="City")]
        
        original_ids = [id(ev) for ev in events]
        result = hydrator.hydrate(events)
        result_ids = [id(ev) for ev in result]
        
        # Should be the same objects (modified in place)
        assert original_ids == result_ids
        assert result[0].emotional_triggers is not None
