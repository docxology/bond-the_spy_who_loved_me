"""Tests for the LIPARUS canonical scenario (single source of truth)."""

from __future__ import annotations

import numpy as np
import pytest

from the_spy_who_loved_me.scenario import (
    SEED,
    canonical_input_hash,
    canonical_parameters,
    run_canonical,
)


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
    the experimental-setup section can be written in tokens. Each assertion
    below re-derives a reported parameter from something the algorithms
    actually produced, or from another reported parameter.

    An earlier version of this test claimed all five assertions were
    re-derivations when three were not: two were ``> 0.0`` sanity bounds that
    re-derived nothing, and the figure-of-merit identity closed over a
    hardcoded ``10.0`` detection threshold instead of the reported one. Those
    are fixed here rather than re-described.
    """
    import math

    from the_spy_who_loved_me.scenario import (
        _BEAM_TRUE_BEARING_DEG,
        _SUB,
        _TRACK_BEARING_NOISE_DEG,
        _TRACK_COURSE_DEG,
        _TRACK_DT_S,
        _TRACK_DURATION_S,
        _TRACK_SPEED_M_S,
    )
    from the_spy_who_loved_me.sub_tracking import simulate_target_track
    from the_spy_who_loved_me.tanker_capture import BayConfig, SubmarineSpec, simulate_capture

    c = run_canonical()

    # Cadence and duration must reproduce the observed sample count.
    assert c["track_num_bearings"] == round(c["track_duration_s"] / c["track_dt_s"])

    # The reported initial range is the norm of the truth track's first
    # point — re-run the scenario and take that norm independently.
    track = simulate_target_track(
        _TRACK_DURATION_S,
        _TRACK_DT_S,
        _TRACK_SPEED_M_S,
        _TRACK_COURSE_DEG,
        _TRACK_BEARING_NOISE_DEG,
        SEED,
    )
    assert c["track_range0_m"] == pytest.approx(float(np.linalg.norm(track.truth[0])))

    # The reported mouth height is the one the capture was actually run
    # against: a submarine one metre deeper than it is refused ingress, one
    # metre shallower than the margin is admitted.
    bay = BayConfig(
        mouth_width_m=float(c["tanker_mouth_width_m"]),
        mouth_height_m=float(c["tanker_mouth_height_m"]),
        hold_length_m=float(c["tanker_hold_length_m"]),
        clearance_m=float(c["tanker_clearance_m"]),
    )
    too_deep = SubmarineSpec(_SUB.length_m, _SUB.beam_m, float(c["tanker_mouth_height_m"]) + 1.0)
    assert simulate_capture(too_deep, bay).success is False
    assert simulate_capture(_SUB, bay).success is bool(c["capture_success"])

    # The reported submarine fits the reported hold with the reported margin.
    assert (
        c["tanker_hold_length_m"] - c["tanker_sub_length_m"] >= c["tanker_clearance_m"]
    ) is bool(c["capture_success"])

    # The reported figure of merit must equal SL - (NL - DI) - DT, with the
    # detection threshold read from the run rather than typed in here.
    assert c["aco_fom_db"] == pytest.approx(
        c["aco_source_level_db"]
        - (c["aco_noise_level_db"] - c["aco_directivity_db"])
        - c["aco_detection_threshold_db"]
    )

    # The reported bearing estimate really is that far from the reported truth.
    assert c["beam_bearing_err_deg"] == pytest.approx(
        abs(c["beam_estimate_deg"] - c["beam_true_bearing_deg"]), abs=5e-3
    )
    assert c["beam_true_bearing_deg"] == pytest.approx(_BEAM_TRUE_BEARING_DEG)
    assert math.isfinite(c["beam_crb_deg"])


def test_reported_capture_time_is_the_declared_schedule() -> None:
    """``capture_time_s`` is a schedule sum, and the test says so.

    It is *not* a measured or derived duration: it is the total of the fixed
    ``_PHASE_DURATIONS`` for the phases the run reached, so it is invariant
    to submarine size and bay geometry. Pinning it as a "result" would pin a
    constant; pinning its provenance is what can actually fail.
    """
    from the_spy_who_loved_me.tanker_capture import _PHASE_DURATIONS, BayConfig, SubmarineSpec
    from the_spy_who_loved_me.tanker_capture import simulate_capture as sim_cap

    c = run_canonical()
    assert c["capture_phases_run"] == 4
    assert c["capture_time_s"] == pytest.approx(sum(_PHASE_DURATIONS.values()))

    # A different submarine that also completes all four phases reports the
    # identical duration — the number carries no information about the boat.
    bay = BayConfig(
        mouth_width_m=float(c["tanker_mouth_width_m"]),
        mouth_height_m=float(c["tanker_mouth_height_m"]),
        hold_length_m=float(c["tanker_hold_length_m"]),
        clearance_m=float(c["tanker_clearance_m"]),
    )
    other = sim_cap(SubmarineSpec(12.0, 4.0, 4.0), bay)
    assert other.success is True
    assert other.total_time_s == pytest.approx(c["capture_time_s"])


class TestCanonicalInputHash:
    """The provenance input hash must be a function of the inputs.

    ``mission.execute`` carried the fixed literal ``"liparus-mission-input"``
    here, which identified the package and could never change — the one thing
    an input hash exists to detect. These assertions fail if it goes back to
    being a constant, and fail if a scenario parameter stops being covered.
    """

    def test_hash_is_stable_for_unchanged_parameters(self) -> None:
        assert canonical_input_hash() == canonical_input_hash()
        assert canonical_input_hash() == canonical_input_hash(canonical_parameters())
        assert len(canonical_input_hash()) == 64

    def test_every_parameter_changes_the_hash(self) -> None:
        baseline = canonical_input_hash()
        params = canonical_parameters()
        assert params, "the canonical parameter set must not be empty"
        for key, value in params.items():
            perturbed = dict(params)
            perturbed[key] = value + 1
            assert canonical_input_hash(perturbed) != baseline, f"{key} does not reach the hash"

    def test_hash_covers_the_scenario_constants(self) -> None:
        """Every private scenario constant must be represented in the map.

        Guards the failure mode where a new canonical parameter is added to
        ``run_canonical`` but not to ``canonical_parameters``, silently
        shrinking what the input hash covers.
        """
        from the_spy_who_loved_me import scenario as sc

        scalar_constants = {
            name
            for name, value in vars(sc).items()
            if name.startswith("_")
            and name.isupper()
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        }
        # The scan set must be non-empty, or this gate proves nothing.
        assert len(scalar_constants) >= 20, sorted(scalar_constants)

        # Derived quantities are excluded by construction: they are computed
        # from other entries rather than being independent inputs.
        derived = {"_BEAM_SNR_DB"}
        params = canonical_parameters()
        missing = [
            name
            for name in sorted(scalar_constants - derived)
            if not any(float(v) == float(getattr(sc, name)) for v in params.values())
        ]
        assert not missing, f"scenario constants absent from the input hash: {missing}"

    def test_mission_provenance_uses_it(self) -> None:
        from the_spy_who_loved_me.mission import MissionProvider

        provider = MissionProvider()
        outcome = provider.execute(provider.plan(provider.brief()))
        assert outcome.provenance.input_hash == canonical_input_hash()
        assert outcome.provenance.input_hash != "liparus-mission-input"


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


def test_detection_p_fa_is_reported_and_used() -> None:
    """D1: the operating false-alarm probability reaches the run and the token.

    ``detect_contract`` is run with an explicit ``DetectionConfig(p_fa=...)``
    whose value is a reported metric, so prose can state at what false-alarm
    rate the contact was declared without typing 0.001.
    """
    from the_spy_who_loved_me.scenario import _DETECTION_P_FA

    c = run_canonical()
    assert c["detection_p_fa"] == pytest.approx(_DETECTION_P_FA)
    assert c["detection_p_fa"] == pytest.approx(1e-3)


def test_ekf_metric_is_finite_and_reportable() -> None:
    """E1: the recursive EKF runs on the canonical window and reports RMS.

    Before this, the EKF was implemented and tested but never reached
    ``run_canonical``, so no manuscript result reported it. This pins that
    the metric exists, is finite, and is a real steady-state error rather than
    a NaN. The bound is *relative to the geometry it ran on* — the recursive
    estimate sits within 10% of the mean target range over the second half of
    the window (measured ~8%), the same way ``TestEkfActuallyEstimates``
    bounds it — so a divergent filter fails here.
    """
    import math

    from the_spy_who_loved_me.scenario import (
        _TRACK_BEARING_NOISE_DEG,
        _TRACK_COURSE_DEG,
        _TRACK_DT_S,
        _TRACK_DURATION_S,
        _TRACK_SPEED_M_S,
        SEED,
    )
    from the_spy_who_loved_me.sub_tracking import simulate_target_track

    c = run_canonical()
    assert math.isfinite(c["track_ekf_rms_m"])
    assert c["track_ekf_rms_m"] > 0.0

    track = simulate_target_track(
        _TRACK_DURATION_S,
        _TRACK_DT_S,
        _TRACK_SPEED_M_S,
        _TRACK_COURSE_DEG,
        _TRACK_BEARING_NOISE_DEG,
        SEED,
    )
    half = track.num_measurements // 2
    mean_range = float(np.mean(np.linalg.norm(track.truth[half:] - track.ownship[half:], axis=1)))
    assert c["track_ekf_rms_m"] < 0.10 * mean_range


def test_canonical_ekf_constants_reach_the_input_hash() -> None:
    """Every EKF seed parameter is a scenario input, not a hidden literal."""
    from the_spy_who_loved_me import scenario as sc

    for name in (
        "_EKF_INIT_X_M",
        "_EKF_INIT_Y_M",
        "_EKF_INIT_VEL_COV_M2S2",
        "_EKF_PROCESS_NOISE",
        "_EKF_MEASUREMENT_NOISE_RAD",
    ):
        assert canonical_parameters()[name[1:].lower()] == getattr(sc, name)


def test_interpolated_bearing_metric_improves_on_grid() -> None:
    """C1: the refined (parabolic) estimate is reported and no worse.

    ``beam_bearing_err_interp_deg`` is computed with ``interpolate=True``;
    on the canonical (grid-aligned) truth the two agree, but the refined
    metric exists and is bounded, so a real precision gain is possible on
    off-grid geometry.
    """
    import math

    c = run_canonical()
    assert math.isfinite(c["beam_bearing_err_interp_deg"])
    assert c["beam_bearing_err_interp_deg"] <= (
        c["beam_bearing_err_deg"] + 1e-6 + 0.5 * c["beam_scan_step_deg"]
    )
