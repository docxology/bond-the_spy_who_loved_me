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
