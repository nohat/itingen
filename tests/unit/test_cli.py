"""Tests for the itingen CLI."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from itingen.cli import main

def test_cli_help(capsys):
    """Test that the CLI shows help information."""
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "itingen" in captured.out
    assert "generate" in captured.out

@patch("itingen.cli.PipelineOrchestrator")
@patch("itingen.cli.FileProvider")
def test_cli_generate_basic(mock_provider_cls, mock_orchestrator_cls, capsys):
    """Test the generate command with basic arguments."""
    # Setup mocks
    mock_orchestrator = mock_orchestrator_cls.return_value
    mock_orchestrator.execute.return_value = []
    mock_orchestrator.validate.return_value = []
    
    # Run CLI
    result = main(["generate", "--trip", "nz_2026"])
    
    assert result == 0
    mock_provider_cls.assert_called_once()
    mock_orchestrator.execute.assert_called_once()

@patch("itingen.cli.FileProvider")
def test_cli_venues_list(mock_provider_cls, capsys):
    """Test the venues list command."""
    # Setup mock provider
    mock_provider = mock_provider_cls.return_value
    mock_venue = MagicMock()
    mock_venue.venue_id = "test-venue"
    mock_venue.canonical_name = "Test Venue"
    mock_venue.address = "123 Test St"
    mock_provider.get_venues.return_value = {"test-venue": mock_venue}
    
    # Run CLI
    result = main(["venues", "list", "--trip", "example"])
    
    assert result == 0
    captured = capsys.readouterr()
    assert "Listing venues for trip: example..." in captured.out
    assert "test-venue" in captured.out
    assert "Test Venue" in captured.out

@patch("itingen.cli.FileProvider")
def test_cli_venues_create(mock_provider_cls, capsys):
    """Test the venues create command."""
    # Setup mock provider
    mock_provider = mock_provider_cls.return_value
    mock_provider.trip_dir = Path("trips/example")
    
    with patch("itingen.cli.input", side_effect=["test-venue", "Test Venue", "123 Test St", "lodging"]):
        result = main(["venues", "create", "--trip", "example"])
    
    assert result == 0
    captured = capsys.readouterr()
    assert "Creating venue for trip: example..." in captured.out
    assert "Venue created successfully" in captured.out

def test_cli_invalid_command():
    """Test that an invalid command returns non-zero."""
    with pytest.raises(SystemExit):
        main(["invalid-command"])
