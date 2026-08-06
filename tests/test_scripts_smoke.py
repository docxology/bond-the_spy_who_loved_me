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


def test_mission_cli_execute_persists_provenance(tmp_path: Path) -> None:
    """The persisted outcome must keep its provenance block (C4).

    ``mission_outcome.json`` used to carry only the results map, so the input
    hash the manuscript points at for audit ("what lets an outcome be audited
    without re-execution") was printed to stdout and then discarded. The file
    now carries provenance (version, seed, input hash) alongside results, and
    this pins it: a future regression that drops the block turns this red.
    """
    import json

    from the_spy_who_loved_me.scenario import canonical_input_hash

    out = tmp_path / "data" / "mission_outcome.json"
    result = _run("mission_cli.py", "execute", "--out", str(out))
    assert result.returncode == 0
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "provenance" in payload
    prov = payload["provenance"]
    assert prov["input_hash"] == canonical_input_hash()
    assert prov["package_version"] and prov["input_hash"].__len__() == 64
    assert "results" in payload and payload["results"]["detected"] is True
    # The provenance block is no longer discarded into the blob: results only
    # would trip the older (buggy) shape.
    assert "results" not in prov


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
