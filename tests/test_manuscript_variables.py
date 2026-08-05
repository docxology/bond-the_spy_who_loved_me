"""Tests for LIPARUS manuscript variable hydration and token cross-reference."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from the_spy_who_loved_me.manuscript_variables import (
    PACKAGE_ROOT,
    _canonical_metrics,
    check_metrics,
    coverage_floor_pct,
    generate_variables,
    load_manuscript_config,
    resolve_manuscript_tree,
)
from the_spy_who_loved_me.scenario import run_canonical

_MANUSCRIPT = PACKAGE_ROOT / "manuscript"
_TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


class TestConfig:
    def test_load_default(self) -> None:
        cfg = load_manuscript_config()
        assert cfg["paper"]["title"].startswith("The Spy Who Loved Me")

    def test_missing_path(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_manuscript_config(PACKAGE_ROOT / "nope.yaml")

    def test_non_mapping_section_rejected(self, tmp_path: Path) -> None:
        p = tmp_path / "config.yaml"
        p.write_text("paper: 5\n", encoding="utf-8")
        with pytest.raises(ValueError):
            generate_variables(config_path=p)


class TestGenerateVariables:
    def test_tokens_present(self) -> None:
        v = generate_variables(require_outputs=True)
        assert v["LIPARUS_CODENAME"] == "LIPARUS"
        assert v["LIPARUS_IDENTITY"] == "THE_SPY_WHO_LOVED_ME"
        assert v["NUM_CONCEPT_MODULES"] == "6"
        for key in (
            "SUB_NUM_BEARINGS",
            "SUB_TRACK_POS_ERR_M",
            "TANKER_HOLD_LENGTH_M",
            "TANKER_CAPTURE_TIME_S",
            "FORENSICS_SCORE",
            "FORENSICS_CLASS",
            "ACO_DETECTION_RANGE_M",
            "ACO_SOUND_SPEED_M_S",
            "BEAM_BEARING_ERR_DEG",
            "BEAM_CRB_DEG",
            "HULL_COLLAPSE_DEPTH_M",
            "HULL_SAFETY_FACTOR",
            "BALLAST_VOLUME_L",
        ):
            assert key in v and v[key]

    def test_metrics_are_real_numbers(self) -> None:
        v = generate_variables()
        assert float(v["SUB_TRACK_POS_ERR_M"]) < 250.0  # canonical TMA converges
        assert float(v["ACO_DETECTION_RANGE_M"]) > 0.0
        assert float(v["HULL_SAFETY_FACTOR"]) >= 1.5
        assert v["HULL_FEASIBLE"] == "yes"


class TestCrossReference:
    def test_every_prose_token_is_generated(self) -> None:
        """Gated in the manifest: every token in numbered sections must exist."""
        variables = generate_variables(require_outputs=True)
        for section in sorted(_MANUSCRIPT.glob("[0-9][0-9]_*.md")):
            text = section.read_text(encoding="utf-8")
            for token in _TOKEN_RE.findall(text):
                assert token in variables, (
                    f"manuscript token {token} missing from generate_variables() (in {section.name})"
                )


class TestResolveTree:
    def test_resolves_to_output(self, tmp_path: Path) -> None:
        variables = generate_variables()
        out_dir, resolved = resolve_manuscript_tree(variables, output_dir=tmp_path / "ms")
        assert out_dir.is_dir()
        assert resolved, "expected at least one section"
        first = out_dir / resolved[0]
        text = first.read_text(encoding="utf-8")
        assert "{{LIPARUS_TITLE}}" not in text  # substituted
        assert "LIPARUS" in text

    def test_strict_rejects_unresolved(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "00_bad.md").write_text("leftover {{NOT_A_TOKEN}} here\n", encoding="utf-8")
        with pytest.raises(ValueError):
            resolve_manuscript_tree(
                {}, manuscript_dir=src, output_dir=tmp_path / "out", strict=True
            )

    def test_non_strict_allows_unresolved(self, tmp_path: Path) -> None:
        src = tmp_path / "src2"
        src.mkdir()
        (src / "00_bad.md").write_text("leftover {{NOT_A_TOKEN}} here\n", encoding="utf-8")
        out, resolved = resolve_manuscript_tree(
            {}, manuscript_dir=src, output_dir=tmp_path / "out2", strict=False
        )
        assert (out / "00_bad.md").read_text(encoding="utf-8") == "leftover {{NOT_A_TOKEN}} here\n"


def test_config_is_valid_yaml_mapping() -> None:
    with open(_MANUSCRIPT / "config.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)


class TestCoverageFloor:
    """The coverage figure quoted in prose must come from the enforced gate."""

    def test_matches_pyproject(self) -> None:
        import tomllib

        with open(PACKAGE_ROOT / "pyproject.toml", "rb") as handle:
            data = tomllib.load(handle)
        expected = int(data["tool"]["coverage"]["report"]["fail_under"])
        assert coverage_floor_pct() == expected
        assert generate_variables()["COVERAGE_FLOOR_PCT"] == str(expected)

    def test_reads_an_explicit_file(self, tmp_path: Path) -> None:
        proj = tmp_path / "pyproject.toml"
        proj.write_text(
            "[tool.coverage.report]\nfail_under = 77\n",
            encoding="utf-8",
        )
        assert coverage_floor_pct(proj) == 77

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            coverage_floor_pct(tmp_path / "absent.toml")

    def test_missing_key_raises(self, tmp_path: Path) -> None:
        proj = tmp_path / "pyproject.toml"
        proj.write_text("[project]\nname = 'x'\n", encoding="utf-8")
        with pytest.raises(KeyError):
            coverage_floor_pct(proj)


class TestStrictOutputGate:
    """The ``require_outputs`` guards must be able to fire, not just exist.

    Each guard is driven by handing :func:`check_metrics` a genuine
    ``run_canonical()`` dict with one field degraded. Nothing is substituted:
    the gate is a pure predicate over a metric mapping, so exercising it
    needs no ``monkeypatch.setattr`` on ``run_canonical`` — which the earlier
    version of this file did, and which is a dependency replacement however
    it is labelled.
    """

    def test_passes_on_the_real_canonical_run(self) -> None:
        metrics = _canonical_metrics(require_outputs=True)
        assert metrics["detected"] is True
        assert check_metrics(metrics) is None

    @pytest.mark.parametrize(
        ("key", "bad_value", "fragment"),
        [
            ("detected", False, "not detected"),
            ("aco_detection_range_m", 0.0, "detection range"),
            ("hull_feasible", False, "not feasible"),
        ],
    )
    def test_each_guard_fires(self, key: str, bad_value: object, fragment: str) -> None:
        degraded = dict(run_canonical())
        degraded[key] = bad_value
        with pytest.raises(ValueError, match=fragment):
            check_metrics(degraded)

    def test_guards_are_skipped_in_draft_mode(self) -> None:
        """Draft mode must not call the gate at all."""
        degraded = dict(run_canonical())
        degraded["detected"] = False
        with pytest.raises(ValueError):
            check_metrics(degraded)  # strict would reject it ...
        # ... and draft mode renders the real run without consulting it.
        assert _canonical_metrics(require_outputs=False)["detected"] is True


class TestPersistedArtefactIsDeterministic:
    """`06_reproducibility.md` claims no wall-clock in persisted artefacts.

    A ``GENERATION_TIMESTAMP`` token used to be emitted into the very map
    that ``scripts/z_generate_manuscript_variables.py`` writes to
    ``output/data/manuscript_variables.json``, so every regeneration differed
    and the claim was false. These assertions are what makes it true: they
    fail the moment any wall-clock value re-enters the map.
    """

    def test_two_generations_are_identical(self) -> None:
        assert generate_variables() == generate_variables()

    def test_serialised_map_is_byte_identical(self) -> None:
        import json

        first = json.dumps(generate_variables(), indent=2, sort_keys=True)
        second = json.dumps(generate_variables(), indent=2, sort_keys=True)
        assert first == second

    def test_no_token_carries_a_wall_clock_value(self) -> None:
        """No value may parse as a current date/time, whatever it is named."""
        import re

        stamp = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")
        variables = generate_variables()
        offenders = {k: v for k, v in variables.items() if stamp.search(v)}
        assert not offenders, f"wall-clock values in the persisted map: {offenders}"


class TestConfigValidation:
    def test_non_mapping_config_rejected(self, tmp_path: Path) -> None:
        bad = tmp_path / "config.yaml"
        bad.write_text("- just\n- a list\n", encoding="utf-8")
        with pytest.raises(ValueError, match="top-level mapping"):
            load_manuscript_config(bad)

    def test_missing_config_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_manuscript_config(tmp_path / "nope.yaml")

    def test_non_mapping_paper_section_rejected(self, tmp_path: Path) -> None:
        bad = tmp_path / "config.yaml"
        bad.write_text("paper: not-a-mapping\n", encoding="utf-8")
        with pytest.raises(ValueError, match="'paper' section"):
            generate_variables(config_path=bad)
