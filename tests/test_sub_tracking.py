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


class TestEkfActuallyEstimates:
    """Accuracy assertions, not shape assertions.

    Every earlier EKF test checked ``.shape`` after predict/update, so the
    filter's arithmetic was invisible under 100% coverage: R was being fed
    the bearing *standard deviation* where the innovation covariance wants a
    *variance*, and nothing went red. These tests pin the estimate against
    truth and pin the R convention directly.
    """

    def _tracker(self, sigma_rad: float = 5e-3) -> PassiveBearingTracker:
        return PassiveBearingTracker(
            [3800.0, 1900.0, 0.0, 25.0],
            [[1e4, 0, 0, 0], [0, 1e4, 0, 0], [0, 0, 1e2, 0], [0, 0, 0, 1e2]],
            process_noise=1e-3,
            measurement_noise_rad=sigma_rad,
        )

    def test_measurement_noise_is_squared_into_a_variance(self) -> None:
        sigma = 0.01
        assert self._tracker(sigma)._r == pytest.approx(sigma**2)

    def test_filter_tracks_the_target(self) -> None:
        """Steady-state accuracy, expressed against the geometry it ran on.

        The bound is 9% of the mean true target range over the window, which
        is where the R convention actually shows up: with ``R = sigma**2``
        (correct) this run measures 8.0% of mean range; with the previous
        ``R = sigma`` it measures 9.9% and this assertion goes red. The
        threshold is deliberately set between the two measured values, so
        reintroducing the units bug fails here.
        """
        sim = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        est = self._tracker().run(sim)
        half = sim.num_measurements // 2
        mean_range_m = float(np.mean(np.linalg.norm(sim.truth[half:] - sim.ownship[half:], axis=1)))
        rms = tracking_rms_error(est, sim.truth, warmup=half)
        assert rms < 0.09 * mean_range_m, f"{rms:.1f} m vs mean range {mean_range_m:.1f} m"

    def test_filter_beats_its_own_initial_error(self) -> None:
        """The estimate must improve on the seed, or it is not filtering."""
        sim = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        fk = self._tracker()
        seed_state = fk.position.copy()
        est = fk.run(sim)
        half = sim.num_measurements // 2
        seeded = np.repeat(seed_state.reshape(1, 2), sim.num_measurements, axis=0)
        assert tracking_rms_error(est, sim.truth, warmup=half) < tracking_rms_error(
            seeded, sim.truth, warmup=half
        )


class TestCoarseSearchEnvelope:
    """The grid initialiser is bounded, and the bound is load-bearing.

    ``estimate_tma``'s default coarse grid spans 3000-6500 m and 5-35 m/s,
    which brackets the canonical scenario (4000 m, 25 m/s).

    The bound is *not* a hard cliff, and this is worth stating precisely
    because it is easy to overclaim in either direction: Gauss-Newton often
    escapes a badly-seeded start, so a 15 km target is still recovered to
    293 m with the defaults. What degrades is the far field — at 60 km the
    default envelope leaves a 25 km position error (42% of range), and
    widening the range bounds cuts it to 4.9 km. These tests pin both halves
    of that, so the caveat in the docstring is falsifiable rather than
    decorative.
    """

    def _far_target(self, range0_m: float) -> TrackSimulation:
        return simulate_target_track(
            600.0, 10.0, 25.0, 90.0, 0.5, seed=11, range0_m=range0_m, bearing0_deg=26.565
        )

    def test_moderately_outside_the_envelope_still_converges(self) -> None:
        """15 km is outside the grid and recovered anyway — do not overclaim."""
        sim = self._far_target(15000.0)
        sol = estimate_tma(sim.time_s, sim.bearings_rad, sim.ownship)
        err = float(np.linalg.norm(sol.position0 - sim.truth[0]))
        assert err < 0.05 * 15000.0, f"expected convergence at 15 km, got {err:.1f} m"

    def test_far_target_is_lost_with_the_default_envelope(self) -> None:
        sim = self._far_target(60000.0)
        sol = estimate_tma(sim.time_s, sim.bearings_rad, sim.ownship)
        err = float(np.linalg.norm(sol.position0 - sim.truth[0]))
        assert err > 0.20 * 60000.0, f"expected the default envelope to miss, got {err:.1f} m"

    def test_widening_the_envelope_recovers_the_far_target(self) -> None:
        sim = self._far_target(60000.0)
        default_err = float(
            np.linalg.norm(
                estimate_tma(sim.time_s, sim.bearings_rad, sim.ownship).position0 - sim.truth[0]
            )
        )
        widened = estimate_tma(
            sim.time_s,
            sim.bearings_rad,
            sim.ownship,
            range_bounds_m=(3000.0, 80000.0),
            range_step_m=2000.0,
        )
        err = float(np.linalg.norm(widened.position0 - sim.truth[0]))
        assert err < 0.5 * default_err, f"widening should help: {err:.1f} vs {default_err:.1f} m"

    def test_empty_or_invalid_envelope_is_rejected(self) -> None:
        sim = simulate_target_track(600.0, 10.0, 25.0, 90.0, 0.5, seed=11)
        with pytest.raises(ValueError, match="must be > 0"):
            estimate_tma(sim.time_s, sim.bearings_rad, sim.ownship, range_step_m=0.0)
        with pytest.raises(ValueError, match="envelope is empty"):
            estimate_tma(sim.time_s, sim.bearings_rad, sim.ownship, range_bounds_m=(5000.0, 4000.0))

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
