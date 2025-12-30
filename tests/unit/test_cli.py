"""Tests for the itingen CLI."""

import pytest
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

def test_cli_invalid_command():
    """Test that an invalid command returns non-zero."""
    with pytest.raises(SystemExit):
        main(["invalid-command"])
