import pytest
import json
from pathlib import Path
from unittest.mock import patch
from itingen.cli import main

def test_cli_generate_example_trip(tmp_path):
    """E2E test for generating an itinerary from the example trip."""
    output_dir = tmp_path / "output"
    
    # Run CLI generate command
    result = main([
        "generate",
        "--trip", "example",
        "--format", "markdown",
        "--output-dir", str(output_dir)
    ])
    
    assert result == 0
    
    # Check if output files exist
    # Based on cli.py: output_dir = args.output_dir / args.trip
    expected_path = output_dir / "example"
    assert expected_path.exists()
    # PipelineOrchestrator uses output_0.md for the first emitter
    assert (expected_path / "output_0.md").exists()

def test_cli_venues_list_example_trip(capsys):
    """E2E test for listing venues of the example trip."""
    result = main([
        "venues",
        "list",
        "--trip", "example"
    ])
    
    assert result == 0
    captured = capsys.readouterr()
    assert "Listing venues for trip: example..." in captured.out
    assert "central-hotel" in captured.out
    assert "local-cafe" in captured.out

def test_cli_generate_with_person_filter(tmp_path):
    """E2E test for generating an itinerary with person filtering."""
    output_dir = tmp_path / "output"
    
    # Run CLI generate command for a specific person
    result = main([
        "generate",
        "--trip", "example",
        "--person", "alice",
        "--format", "markdown",
        "--output-dir", str(output_dir)
    ])
    
    assert result == 0
    
    # Based on cli.py: output_dir = args.output_dir / args.trip / args.person
    expected_path = output_dir / "example" / "alice"
    assert expected_path.exists()
    assert (expected_path / "output_0.md").exists()

def test_cli_venues_create_success(tmp_path):
    """E2E test for creating a new venue via CLI."""
    # Setup temporary trip directory
    trip_dir = tmp_path / "new_trip"
    trip_dir.mkdir()
    (trip_dir / "venues").mkdir()
    
    # Mock input for the interactive prompt
    inputs = ["new-venue", "New Venue Name", "123 New St", "restaurant"]
    
    with patch("builtins.input", side_effect=inputs):
        result = main([
            "venues",
            "create",
            "--trip", str(trip_dir)
        ])
    
    assert result == 0
    
    venue_file = trip_dir / "venues" / "new-venue.json"
    assert venue_file.exists()
    
    with open(venue_file, "r") as f:
        data = json.load(f)
        assert data["venue_id"] == "new-venue"
        assert data["canonical_name"] == "New Venue Name"
        assert data["address"] == "123 New St"
        assert data["kind"] == "restaurant"
