"""Subprocess smoke tests for the thin LIPARUS CLI scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / script), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_mission_cli_brief() -> None:
    result = _run("mission_cli.py", "brief")
    assert result.returncode == 0
    assert '"MissionBrief"' in result.stdout


def test_mission_cli_execute_writes_outcome(tmp_path: Path) -> None:
    out = tmp_path / "data" / "mission_outcome.json"
    result = _run("mission_cli.py", "execute", "--out", str(out))
    assert result.returncode == 0
    assert out.is_file()
    assert '"detected"' in out.read_text(encoding="utf-8")


def test_mission_cli_unknown_phase_exits_2() -> None:
    result = _run("mission_cli.py", "bogus")
    assert result.returncode == 2


def test_generate_figures() -> None:
    result = _run("generate_figures.py")
    assert result.returncode == 0
    assert (PROJECT_ROOT / "output" / "figures" / "bearing_track.png").is_file()


def test_z_generate_manuscript_variables() -> None:
    result = _run("z_generate_manuscript_variables.py")
    assert result.returncode == 0
    data = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    assert data.is_file()
    assert "LIPARUS_CODENAME" in data.read_text(encoding="utf-8")
