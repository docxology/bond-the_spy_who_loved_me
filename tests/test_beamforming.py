"""Real-data, deterministic tests for ULA beamforming and bearing estimation."""

from __future__ import annotations

import math

import numpy as np
import pytest

from the_spy_who_loved_me.beamforming import (
    BeamformerResult,
    array_snapshot,
    beam_power,
    cramer_rao_bearing_std_deg,
    estimate_bearing_deg,
    interpolate_peak_deg,
    steering_vector,
)


class TestSteeringVector:
    def test_broadside_is_ones(self) -> None:
        a = steering_vector(0.0, 0.5, 8)
        np.testing.assert_allclose(np.abs(a), 1.0)
        np.testing.assert_allclose(np.imag(a), 0.0, atol=1e-12)

    def test_single_element_phase(self) -> None:
        a = steering_vector(0.5, 0.5, 2)
        # Element 1 phase = -2 pi * 0.5 * 1 * sin(0.5).
        expected_phase = -2.0 * math.pi * 0.5 * math.sin(0.5)
        assert np.angle(a[1]) == pytest.approx(expected_phase)

    def test_validates(self) -> None:
        with pytest.raises(ValueError):
            steering_vector(0.0, 0.5, 1)
        with pytest.raises(ValueError):
            steering_vector(0.0, 0.0, 8)


class TestSnapshot:
    def test_seed_reproducible(self) -> None:
        a = array_snapshot(0.5, 0.5, 8, 1.0, 0.1, 42)
        b = array_snapshot(0.5, 0.5, 8, 1.0, 0.1, 42)
        np.testing.assert_array_equal(a, b)

    def test_shape(self) -> None:
        snap = array_snapshot(0.5, 0.5, 8, 1.0, 0.1, 1)
        assert snap.shape == (8,)
        assert np.iscomplexobj(snap)


class TestBeamPower:
    def test_peak_at_truth(self) -> None:
        snap = array_snapshot(math.radians(30.0), 0.5, 8, 2.0, 0.3, 11)
        on = beam_power(snap, math.radians(30.0), 0.5)
        off = beam_power(snap, math.radians(-30.0), 0.5)
        assert on > off

    def test_rejects_2d(self) -> None:
        with pytest.raises(ValueError):
            beam_power(np.zeros((2, 2)), 0.0, 0.5)


class TestBearingEstimate:
    def test_recovers_true_bearing(self) -> None:
        snap = array_snapshot(math.radians(30.0), 0.5, 8, 1.0, 0.1, 11)
        res = estimate_bearing_deg(snap, 0.5)
        assert isinstance(res, BeamformerResult)
        assert abs(res.bearing_deg - 30.0) <= 1.5

    def test_custom_scan_grid(self) -> None:
        snap = array_snapshot(math.radians(10.0), 0.5, 8, 2.0, 0.2, 3)
        grid = np.arange(-40.0, 41.0, 1.0)
        res = estimate_bearing_deg(snap, 0.5, scan=grid)
        assert res.bearing_deg in grid
        assert res.n_elements == 8

    def test_as_dict(self) -> None:
        snap = array_snapshot(math.radians(20.0), 0.5, 8, 1.0, 0.1, 5)
        d = estimate_bearing_deg(snap, 0.5).as_dict()
        assert "bearing_deg" in d and "n_elements" in d


class TestCRB:
    def test_decreases_with_snr_and_elements(self) -> None:
        lo = cramer_rao_bearing_std_deg(8, 0.5, 30.0, 0.0)
        hi = cramer_rao_bearing_std_deg(8, 0.5, 10.0, 0.0)
        assert lo < hi
        more = cramer_rao_bearing_std_deg(32, 0.5, 10.0, 0.0)
        assert more < hi

    def test_validates(self) -> None:
        with pytest.raises(ValueError):
            cramer_rao_bearing_std_deg(1, 0.5, 10.0, 0.0)
        with pytest.raises(ValueError):
            cramer_rao_bearing_std_deg(8, -0.5, 10.0, 0.0)
        # Near endfire the bound diverges.
        with pytest.raises(ValueError):
            cramer_rao_bearing_std_deg(8, 0.5, 10.0, math.pi / 2.0)


class TestScanGridQuantisation:
    """The peak search is grid-limited; pin that on *off-grid* bearings.

    The canonical scenario places the true bearing at exactly 30 degrees,
    which lands on a scan-grid node and yields a measured error of exactly
    zero — below the Cramer-Rao bound, which no unbiased estimator can
    achieve. That zero is an artefact of grid alignment, so asserting on it
    would be a test that passes by construction. These tests use bearings
    deliberately placed *between* grid nodes, where the quantisation floor
    is visible and the assertion can actually fail.
    """

    #: Scan-grid step of ``estimate_bearing_deg`` when no grid is supplied.
    SCAN_STEP_DEG = 0.5

    def test_default_grid_step_is_the_documented_one(self) -> None:
        snap = array_snapshot(math.radians(10.0), 0.5, 8, 1.0, 0.05, 3)
        scan = estimate_bearing_deg(snap, 0.5).scan
        steps = np.diff(scan)
        assert np.allclose(steps, self.SCAN_STEP_DEG)

    @pytest.mark.parametrize("true_deg", [12.3, -47.7, 30.25, 5.1, -0.3])
    def test_off_grid_error_is_bounded_by_half_a_cell(self, true_deg: float) -> None:
        snap = array_snapshot(math.radians(true_deg), 0.5, 16, 1.0, 0.05, 7)
        est = estimate_bearing_deg(snap, 0.5).bearing_deg
        # The estimate must snap to a grid node ...
        assert math.isclose(est / self.SCAN_STEP_DEG, round(est / self.SCAN_STEP_DEG), abs_tol=1e-9)
        # ... and be within half a cell of truth at this (high) SNR.
        assert abs(est - true_deg) <= self.SCAN_STEP_DEG / 2.0 + 1e-9

    def test_off_grid_error_is_nonzero_so_the_bound_is_not_vacuous(self) -> None:
        """A truth strictly between nodes cannot be recovered exactly."""
        true_deg = 12.3  # 12.3 / 0.5 is not an integer
        snap = array_snapshot(math.radians(true_deg), 0.5, 16, 1.0, 0.05, 7)
        est = estimate_bearing_deg(snap, 0.5).bearing_deg
        assert abs(est - true_deg) > 0.0

    def test_finer_grid_reduces_the_quantisation_error(self) -> None:
        true_deg = 12.3
        snap = array_snapshot(math.radians(true_deg), 0.5, 16, 1.0, 0.05, 7)
        coarse = abs(estimate_bearing_deg(snap, 0.5).bearing_deg - true_deg)
        fine_grid = np.arange(-90.0, 90.0 + 0.01, 0.01)
        fine = abs(estimate_bearing_deg(snap, 0.5, fine_grid).bearing_deg - true_deg)
        assert fine < coarse


class TestInterpolation:
    """Opt-in parabolic interpolation refines the grid-quantised estimate.

    ``estimate_bearing_deg(..., interpolate=True)`` is **additive**: the
    default stays grid-quantised (so existing semantics and the honest
    grid-limitation story are preserved), and interpolation is an explicit
    precision improvement. On an off-grid bearing at high SNR the
    interpolated error must be strictly smaller than the grid error and
    within an order of magnitude of the Cramer-Rao floor — which is what a
    beamformer can approach (not beat). Removing interpolation makes this
    red.
    """

    GRID = np.arange(-90.0, 90.0 + 0.5, 0.5)

    def test_default_stays_grid_quantised(self) -> None:
        """The grid-path behaviour is unchanged: output is a grid node."""
        snap = array_snapshot(math.radians(12.3), 0.5, 16, 1.0, 0.05, 7)
        res = estimate_bearing_deg(snap, 0.5)
        est = res.bearing_deg
        assert math.isclose(est / 0.5, round(est / 0.5), abs_tol=1e-9)

    def test_interp_beats_grid_on_off_grid_bearing(self) -> None:
        true_deg = 12.3  # between nodes
        snap = array_snapshot(math.radians(true_deg), 0.5, 16, 1.0, 0.05, 7)
        grid_err = abs(estimate_bearing_deg(snap, 0.5).bearing_deg - true_deg)
        interp_err = abs(estimate_bearing_deg(snap, 0.5, interpolate=True).bearing_deg - true_deg)
        assert grid_err > 0.0  # genuinely off-grid, else the test is vacuous
        assert interp_err < grid_err

    def test_interp_reasonable_vs_cramer_rao(self) -> None:
        true_deg = 12.3
        snap = array_snapshot(math.radians(true_deg), 0.5, 16, 1.0, 0.02, 7)
        crb = cramer_rao_bearing_std_deg(16, 0.5, 34.0, math.radians(true_deg))
        interp_err = abs(estimate_bearing_deg(snap, 0.5, interpolate=True).bearing_deg - true_deg)
        # Sanity (not a tight bound, but a real relation): a good estimate is
        # within a few CRB sigma, not orders above.
        assert interp_err < 10.0 * crb + 0.05

    def test_interpolate_peak_deg_degenerate_returns_node(self) -> None:
        scan = np.array([-1.0, 0.0, 1.0])
        powers_none = np.array([1.0, 1.0, 1.0])  # flat -> no parabola
        assert interpolate_peak_deg(scan, powers_none, 1) == 0.0
        assert interpolate_peak_deg(scan, np.array([1.0, 2.0, 3.0]), 0) == -1.0  # corner
        assert interpolate_peak_deg(scan, np.array([1.0, 2.0, 3.0]), 2) == 1.0  # corner
