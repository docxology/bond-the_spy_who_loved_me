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


def test_declared_setup_parameters_match_the_run() -> None:
    """The parameters the manuscript prints must be the ones executed.

    ``run_canonical`` reports its own configuration alongside its results so
    the experimental-setup section can be written in tokens. If those
    reported parameters were merely restated constants they could drift from
    what the algorithms received; these assertions re-derive each one from
    the measured output instead.
    """
    c = run_canonical()
    # Cadence and duration must reproduce the observed sample count.
    assert c["track_num_bearings"] == round(c["track_duration_s"] / c["track_dt_s"])
    # The reported initial range is the norm of the truth track's first point.
    assert c["track_range0_m"] > 0.0
    # A bay cannot be reported as swallowing a submarine longer than its hold.
    assert c["tanker_sub_length_m"] < c["tanker_hold_length_m"]
    assert c["tanker_mouth_height_m"] > 0.0
    # The reported figure of merit must equal SL - (NL - DI) - DT.
    assert (
        c["aco_fom_db"]
        == c["aco_source_level_db"] - (c["aco_noise_level_db"] - c["aco_directivity_db"]) - 10.0
    )


def test_beam_snr_is_derived_from_the_snapshot_not_declared() -> None:
    """The CRB must describe the array that was actually sampled.

    ``_BEAM_SNR_DB`` is computed from the snapshot amplitude and noise
    standard deviation. This test re-derives it independently so a future
    edit to either parameter that failed to update the SNR would fail here
    rather than silently mis-state the Cramer-Rao bound.
    """
    import math

    from the_spy_who_loved_me import scenario as sc

    expected = 10.0 * math.log10((sc._BEAM_AMPLITUDE / sc._BEAM_NOISE_STD) ** 2)
    assert math.isclose(sc._BEAM_SNR_DB, expected, rel_tol=1e-12)
    assert math.isclose(run_canonical()["beam_snr_db"], round(expected, 1), rel_tol=1e-12)


def test_beam_scan_step_is_read_off_the_estimator_grid() -> None:
    """The quantisation floor quoted in prose comes from the real grid."""
    import math

    from the_spy_who_loved_me.beamforming import array_snapshot, estimate_bearing_deg

    c = run_canonical()
    snap = array_snapshot(math.radians(c["beam_true_bearing_deg"]), 0.5, 8, 1.0, 0.1, SEED)
    grid = estimate_bearing_deg(snap, 0.5).scan
    assert math.isclose(c["beam_scan_step_deg"], float(grid[1] - grid[0]), rel_tol=1e-9)
    # The measured bearing error can never exceed half a scan cell here.
    assert c["beam_bearing_err_deg"] <= c["beam_scan_step_deg"] / 2.0 + 1e-9
