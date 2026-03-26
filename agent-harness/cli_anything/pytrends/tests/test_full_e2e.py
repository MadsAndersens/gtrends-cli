"""E2E tests for cli-anything-pytrends.

Tests the CLI through Click's test runner and via subprocess for installed command.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest
from click.testing import CliRunner

from cli_anything.pytrends.pytrends_cli import cli


# ── Click CliRunner Tests ───────────────────────────────────────────────

class TestCLIBasic:
    """Test basic CLI functionality via Click's CliRunner."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_cli_version(self):
        result = self.runner.invoke(cli, ["--version"], obj={})
        assert result.exit_code == 0
        assert "cli-anything-pytrends" in result.output
        assert "0.1.0" in result.output

    def test_cli_help(self):
        result = self.runner.invoke(cli, ["--help"], obj={})
        assert result.exit_code == 0
        assert "CLI harness for Google Trends" in result.output
        assert "session" in result.output
        assert "search" in result.output
        assert "trending" in result.output
        assert "explore" in result.output
        assert "related" in result.output
        assert "daily" in result.output
        assert "repl" in result.output

    def test_cli_no_command(self):
        result = self.runner.invoke(cli, [], obj={})
        assert result.exit_code == 0
        assert "CLI harness for Google Trends" in result.output

    def test_search_help(self):
        result = self.runner.invoke(cli, ["search", "--help"], obj={})
        assert result.exit_code == 0
        assert "interest-over-time" in result.output
        assert "interest-by-region" in result.output
        assert "multirange" in result.output

    def test_trending_help(self):
        result = self.runner.invoke(cli, ["trending", "--help"], obj={})
        assert result.exit_code == 0
        assert "now" in result.output
        assert "today" in result.output
        assert "realtime" in result.output

    def test_explore_help(self):
        result = self.runner.invoke(cli, ["explore", "--help"], obj={})
        assert result.exit_code == 0
        assert "suggestions" in result.output
        assert "categories" in result.output
        assert "top-charts" in result.output

    def test_related_help(self):
        result = self.runner.invoke(cli, ["related", "--help"], obj={})
        assert result.exit_code == 0
        assert "topics" in result.output
        assert "queries" in result.output

    def test_session_help(self):
        result = self.runner.invoke(cli, ["session", "--help"], obj={})
        assert result.exit_code == 0
        assert "init" in result.output
        assert "show" in result.output
        assert "set" in result.output


class TestCLISessionCommands:
    """Test session commands (these don't need network)."""

    def setup_method(self):
        self.runner = CliRunner()
        # Reset global session
        import cli_anything.pytrends.pytrends_cli as cli_mod
        cli_mod._session = None

    def test_session_show_default(self):
        result = self.runner.invoke(cli, ["session", "show"], obj={})
        assert result.exit_code == 0
        assert "en-US" in result.output

    def test_session_show_json(self):
        result = self.runner.invoke(cli, ["--json", "session", "show"], obj={})
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["config"]["hl"] == "en-US"
        assert parsed["config"]["tz"] == 360
        assert "initialized" in parsed


class TestCLIValidation:
    """Test input validation via CLI."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_search_iot_missing_keywords(self):
        result = self.runner.invoke(cli, ["search", "interest-over-time"], obj={})
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "KEYWORDS" in result.output

    def test_search_ibr_missing_keywords(self):
        result = self.runner.invoke(cli, ["search", "interest-by-region"], obj={})
        assert result.exit_code != 0

    def test_daily_missing_start(self):
        result = self.runner.invoke(cli, ["daily", "python"], obj={})
        assert result.exit_code != 0

    def test_multirange_missing_timeframes(self):
        result = self.runner.invoke(cli, ["search", "multirange", "python"], obj={})
        assert result.exit_code != 0


class TestCLIJsonOutput:
    """Test JSON output mode on commands that don't need network."""

    def setup_method(self):
        self.runner = CliRunner()
        import cli_anything.pytrends.pytrends_cli as cli_mod
        cli_mod._session = None

    def test_session_show_json_structure(self):
        result = self.runner.invoke(cli, ["--json", "session", "show"], obj={})
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data["config"], dict)
        assert isinstance(data["config"]["timeout"], list)
        assert data["config"]["retries"] == 0

    def test_session_show_csv(self):
        result = self.runner.invoke(cli, ["--csv", "session", "show"], obj={})
        assert result.exit_code == 0
        # CSV mode for dict just uses str()
        assert "en-US" in result.output


# ── Subprocess Tests ────────────────────────────────────────────────────

class TestCLISubprocess:
    """Test the installed CLI command via subprocess.

    Uses _resolve_cli() to find the installed command.
    Set CLI_ANYTHING_FORCE_INSTALLED=1 to require the command be in PATH.
    """

    @staticmethod
    def _resolve_cli(name: str = "cli-anything-pytrends") -> list:
        """Resolve the CLI command, preferring PATH-installed version."""
        force_installed = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "0") == "1"

        # Check if command exists in PATH
        cmd_path = shutil.which(name)
        if cmd_path:
            return [cmd_path]

        if force_installed:
            pytest.skip(f"{name} not found in PATH (CLI_ANYTHING_FORCE_INSTALLED=1)")

        # Fallback to python -m invocation
        return [sys.executable, "-m", "cli_anything.pytrends.pytrends_cli"]

    def _run(self, *args, **kwargs) -> subprocess.CompletedProcess:
        cmd = self._resolve_cli() + list(args)
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            **kwargs,
        )

    def test_subprocess_version(self):
        result = self._run("--version")
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_subprocess_help(self):
        result = self._run("--help")
        assert result.returncode == 0
        assert "CLI harness for Google Trends" in result.stdout

    def test_subprocess_session_show(self):
        result = self._run("session", "show")
        assert result.returncode == 0
        assert "en-US" in result.stdout

    def test_subprocess_session_show_json(self):
        result = self._run("--json", "session", "show")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["config"]["hl"] == "en-US"

    def test_subprocess_search_help(self):
        result = self._run("search", "--help")
        assert result.returncode == 0
        assert "interest-over-time" in result.stdout

    def test_subprocess_explore_help(self):
        result = self._run("explore", "--help")
        assert result.returncode == 0
        assert "suggestions" in result.stdout

    def test_subprocess_trending_help(self):
        result = self._run("trending", "--help")
        assert result.returncode == 0
        assert "now" in result.stdout
