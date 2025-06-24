"""Unit tests for ClipScribe CLI."""

import pytest
from click.testing import CliRunner
from clipscribe.commands.cli import cli
from clipscribe.version import __version__


class TestCLI:
    """Test CLI commands."""
    
    def test_version(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert __version__ in result.output
    
    def test_help(self):
        """Test help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'ClipScribe - AI-powered video transcription' in result.output
    
    def test_config_command(self):
        """Test config command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['config'])
        assert result.exit_code == 0
        assert 'ClipScribe Configuration' in result.output
    
    def test_platforms_command(self):
        """Test platforms command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['platforms'])
        assert result.exit_code == 0
        assert '1800+ video platforms' in result.output
    
    def test_transcribe_no_url(self):
        """Test transcribe command without URL."""
        runner = CliRunner()
        result = runner.invoke(cli, ['transcribe'])
        assert result.exit_code == 2  # Click returns 2 for missing arguments
        assert 'Missing argument' in result.output 