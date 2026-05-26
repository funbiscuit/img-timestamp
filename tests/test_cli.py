import subprocess
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestCLIExitCodes:
    """CLI exit code behavior."""

    def test_empty_dir_exit_0(self):
        """Empty directory exits with code 0."""
        with tempfile.TemporaryDirectory() as td:
            result = subprocess.run(
                ['.venv/bin/imgts', '--directory', td],
                capture_output=True, text=True,
                cwd=str(PROJECT_ROOT),
            )
            assert result.returncode == 0, f'Expected 0, got {result.returncode}'

    def test_nonexistent_dir_exit_2(self):
        """Nonexistent directory exits with code 2."""
        result = subprocess.run(
            ['.venv/bin/imgts', '--directory', '/nonexistent/path/that/does/not/exist'],
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 2, f'Expected 2, got {result.returncode}'

    def test_help_exit_0(self):
        """--help exits with code 0."""
        result = subprocess.run(
            ['.venv/bin/imgts', '--help'],
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
