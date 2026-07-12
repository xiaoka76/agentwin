"""Smoke tests - just import and --help."""
from typer.testing import CliRunner
from agentwin.cli import app


def test_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "agentwin" in result.output.lower() or "Usage" in result.output


def test_health_help():
    runner = CliRunner()
    result = runner.invoke(app, ["health", "--help"])
    assert result.exit_code == 0


def test_auth_help():
    runner = CliRunner()
    result = runner.invoke(app, ["auth", "--help"])
    assert result.exit_code == 0
