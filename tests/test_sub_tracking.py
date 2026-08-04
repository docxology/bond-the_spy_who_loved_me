"""Real-data, deterministic tests for passive acoustic detection and tracking."""

from __future__ import annotations

import numpy as np
import pytest

from the_spy_who_loved_me.sub_tracking import (
    DetectionConfig,
    PassiveBearingTracker,
    TrackSimulation,
    chi2_quantile,
    detect_contract,
    estimate_tma,
    inverse_normal_cdf,
    simulate_signal,
    simulate_target_track,
    tracking_rms_error,
)


class TestQuantiles:
    def test_inverse_normal_cdf_mid_and_tails(self) -> None:
        assert inverse_normal_cdf(0.5) == pytest.approx(0.0, abs=1e-3)
        assert inverse_normal_cdf(0.975) == pytest.approx(1.96, abs=1e-2)
        assert inverse_normal_cdf(0.025) == pytest.approx(-1.96, abs=1e-2)
        assert inverse_normal_cdf(0.001) < inverse_normal_cdf(0.5)
        assert inverse_normal_cdf(0.999) > inverse_normal_cdf(0.5)

    def test_inverse_normal_cdf_rejects_out_of_range(self) -> None:
        for bad in (0.0, 1.0, -0.5, 1.5):
            with pytest.raises(ValueError):
                inverse_normal_cdf(bad)

    def test_chi2_quantile_monotonic_in_p_and_nu(self) -> None:
        assert chi2_quantile(64, 0.99) > chi2_quantile(64, 0.5)
        assert chi2_quantile(128, 0.5) > chi2_quantile(64, 0.5)

    def test_chi2_quantile_validates(self) -> None:
        with pytest.raises(ValueError):
            chi2_quantile(0, 0.5)
        with pytest.raises(ValueError):
            chi2_quantile(4, 1.0)


class TestDetection:
    def test_detect_high_snr_signal(self) -> None:
        # A strong tonal in seeded noise must cross a low-P_FA threshold.
        signal = simulate_signal(duration_s=2.0, fs=8000, target_snr_db=12.0, seed=11)
        detection = detect_contract(signal)
        assert detection.detected is True
        assert detection.margin_db > 0.0

    def test_detect_pure_noise_not_crossing(self) -> None:
        # Pure noise at very low P_FA should not trip the detector.
        noise = simulate_signal(duration_s=2.0, fs=8000, target_snr_db=0.0, seed=11)
        detection = detect_contract(noise, DetectionConfig(p_fa=1e-6))
        assert detection.detected is False

    def test_detect_short_input(self) -> None:
        detection = detect_contract(np.zeros(4), DetectionConfig(window=64))
        assert detection.detected is False

    def test_detection_config_validates(self) -> None:
        with pytest.raises(ValueError):
            DetectionConfig(noise_variance=0.0)
        with pytest.raises(ValueError):
            DetectionConfig(window=0)
        with pytest.raises(ValueError):
            DetectionConfig(p_fa=1.0)

    def test_detection_margin_db(self) -> None:
        d = detect_contract(simulate_signal(2.0, 8000, 12.0, 5))
        assert d.margin_db > 0.0

    def test_threshold_decreases_as_p_fa_rises(self) -> None:
        lo = chi2_quantile(64, 1.0 - 1e-6)
        hi = chi2_quantile(64, 1.0 - 0.1)
        assert lo > hi


class TestTrackSimulation:
    def test_scenario_shape_and_fields(self) -> None:
        sim = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        assert sim.num_measurements == 60
        assert sim.truth.shape == (60, 2)
        assert sim.ownship.shape == (60, 2)
        assert sim.speed_m_s == 25.0
        assert sim.course_deg == 90.0

    def test_ownship_maneuvers(self) -> None:
        sim = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        # Dogleg: east first leg, then north — ownship total displacement and
        # the final position must reflect a course change.
        final = sim.ownship[-1]
        assert final[0] > 0.0 and final[1] > 0.0

    def test_same_seed_reproducible(self) -> None:
        a = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=42)
        b = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=42)
        np.testing.assert_array_equal(a.bearings_rad, b.bearings_rad)

    def test_maneuver_fraction_edge(self) -> None:
        # A fraction outside (0,1) should not crash: entire run on leg one.
        sim = simulate_target_track(100.0, 10.0, 20.0, 0.0, 0.5, seed=1, maneuver_fraction=1.0)
        assert sim.ownship[-1][1] == pytest.approx(0.0)


class TestTMALeastSquares:
    def test_recovers_target_on_maneuver(self) -> None:
        sim = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        sol = estimate_tma(sim.time_s, sim.bearings_rad, sim.ownship)
        # Batch TMA with a maneuvering ownship recovers initial position well.
        err = float(np.linalg.norm(sol.position0 - sim.truth[0]))
        assert err < 250.0
        assert sol.num_measurements == sim.num_measurements
        assert sol.residual_rms_rad < 0.05

    def test_position_at_and_as_dict(self) -> None:
        sim = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        sol = estimate_tma(sim.time_s, sim.bearings_rad, sim.ownship)
        at = sol.position_at(100.0)
        assert at.shape == (2,)
        d = sol.as_dict
        assert "position0_m" in d and "velocity_m_s" in d

    def test_too_few_measurements(self) -> None:
        sim = simulate_target_track(40.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        with pytest.raises(ValueError):
            estimate_tma(sim.time_s[:3], sim.bearings_rad[:3], sim.ownship[:3])

    def test_alignment_validation(self) -> None:
        sim = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        with pytest.raises(ValueError):
            estimate_tma(sim.time_s[:-1], sim.bearings_rad, sim.ownship)


class TestPassiveBearingTracker:
    def test_predict_update_mechanics(self) -> None:
        fk = PassiveBearingTracker(
            [1000.0, 1000.0, 10.0, 5.0],
            [[10.0, 0, 0, 0], [0, 10.0, 0, 0], [0, 0, 10.0, 0], [0, 0, 0, 10.0]],
            process_noise=0.1,
            measurement_noise_rad=0.01,
        )
        before = fk.position.copy()
        fk.predict(10.0)
        assert fk.position[0] > before[0]  # moved east by vx*dt
        fk.update(0.0)  # bearing east
        assert fk.position.shape == (2,)
        assert fk.velocity.shape == (2,)

    def test_update_at_origin_raises(self) -> None:
        fk = PassiveBearingTracker(
            [0.0, 0.0, 0.0, 0.0],
            [[10.0, 0, 0, 0], [0, 10.0, 0, 0], [0, 0, 10.0, 0], [0, 0, 0, 10.0]],
        )
        with pytest.raises(ValueError):
            fk.update(0.0)

    def test_run_returns_aligned_history(self) -> None:
        sim = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        fk = PassiveBearingTracker(
            [4000.0, 0.0, 0.0, 25.0],
            [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]],
            process_noise=1e-6,
            measurement_noise_rad=1e-3,
        )
        est = fk.run(sim)
        assert est.shape == sim.truth.shape

    def test_run_empty(self) -> None:
        sim = simulate_target_track(20.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        tr = TrackSimulation(
            sim.time_s[:1], sim.truth[:1], sim.ownship[:1], np.array([]), 0.5, 25.0, 90.0
        )
        fk = PassiveBearingTracker(
            [1.0, 1.0, 0.0, 0.0], [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]]
        )
        assert fk.run(tr).shape == (0, 2)

    def test_init_validations(self) -> None:
        with pytest.raises(ValueError):
            PassiveBearingTracker([1.0, 2.0], [[1.0]])
        with pytest.raises(ValueError):
            PassiveBearingTracker(
                [1.0, 1.0, 0.0, 0.0],
                [[-1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]],
            )
        with pytest.raises(ValueError):
            PassiveBearingTracker(
                [1.0, 1.0, 0.0, 0.0],
                [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]],
                process_noise=-1.0,
            )
        with pytest.raises(ValueError):
            PassiveBearingTracker(
                [1.0, 1.0, 0.0, 0.0],
                [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]],
                measurement_noise_rad=0.0,
            )


class TestTrackingRms:
    def test_rms_error_zero_for_identical(self) -> None:
        truth = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
        assert tracking_rms_error(truth, truth) == pytest.approx(0.0)

    def test_rms_error_known_value(self) -> None:
        truth = np.array([[0.0, 0.0], [0.0, 0.0]])
        est = np.array([[1.0, 0.0], [0.0, 1.0]])  # errors 1 and 1 -> rmse 1
        assert tracking_rms_error(est, truth) == pytest.approx(1.0)

    def test_rms_error_validates(self) -> None:
        with pytest.raises(ValueError):
            tracking_rms_error(np.zeros((2, 2)), np.zeros((2, 3)))
        with pytest.raises(ValueError):
            tracking_rms_error(np.zeros((2, 2)), np.zeros((2, 2)), warmup=2)


class TestSimulateSignal:
    def test_zero_snr_returns_noise_only(self) -> None:
        sig = simulate_signal(1.0, 8000, 0.0, seed=3)
        n = np.random.default_rng(3).normal(0.0, 1.0, 8000)
        np.testing.assert_array_equal(sig, n)

    def test_positive_snr_adds_tonal(self) -> None:
        sig = simulate_signal(1.0, 8000, 12.0, seed=3)
        assert float(np.mean(sig**2)) > 1.0
