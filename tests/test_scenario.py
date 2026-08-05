"""Tests for the LIPARUS canonical scenario (single source of truth)."""

from __future__ import annotations

from the_spy_who_loved_me.scenario import SEED, run_canonical


def test_run_canonical_is_complete() -> None:
    c = run_canonical()
    assert c["detected"] is True
    assert c["capture_success"] is True
    assert c["hull_feasible"] is True
    assert c["aco_detection_range_m"] > 0.0
    assert c["beam_bearing_err_deg"] >= 0.0
    # The six concepts are all represented.
    assert c["track_num_bearings"] > 0
    assert c["capture_time_s"] > 0.0
    assert c["forensics_class"] == "submersible"


def test_run_canonical_is_deterministic() -> None:
    assert run_canonical() == run_canonical()


def test_seed_is_fixed() -> None:
    assert SEED == 11
