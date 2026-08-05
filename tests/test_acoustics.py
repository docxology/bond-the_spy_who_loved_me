"""Real-data, deterministic tests for underwater acoustics and the passive sonar equation."""

from __future__ import annotations

import math

import pytest

from the_spy_who_loved_me.acoustics import (
    PropagationResult,
    SonarBudget,
    detection_range_m,
    figure_of_merit_db,
    passive_sonar_equation,
    sound_speed_m_s,
    thorp_absorption,
    transmission_loss,
)


class TestThorp:
    def test_known_values(self) -> None:
        # Absorption grows with frequency; near DC it is ~0.003 dB/km.
        assert thorp_absorption(0.0) == pytest.approx(0.003, abs=1e-6)
        assert thorp_absorption(1000.0) > thorp_absorption(100.0)
        assert thorp_absorption(10000.0) > thorp_absorption(1000.0)

    def test_negative_frequency_rejected(self) -> None:
        with pytest.raises(ValueError):
            thorp_absorption(-1.0)


class TestSoundSpeed:
    def test_reasonable_range(self) -> None:
        assert sound_speed_m_s(10.0, 35.0, 0.0) == pytest.approx(1489.8, abs=1.0)
        # Warmer water is faster.
        assert sound_speed_m_s(25.0, 35.0, 0.0) > sound_speed_m_s(5.0, 35.0, 0.0)


class TestTransmissionLoss:
    def test_spherical_vs_cylindrical(self) -> None:
        # Spherical spreading is 10 dB/km stronger at 1 km.
        r = 1000.0
        assert transmission_loss(r, 100.0, "spherical") > transmission_loss(r, 100.0, "cylindrical")
        # At 1 m, loss is ~0 (spreading is 0; only a trace of absorption).
        assert transmission_loss(1.0, 100.0, "spherical") == pytest.approx(0.0, abs=1e-4)

    def test_loss_increases_with_range(self) -> None:
        assert transmission_loss(5000.0, 400.0) > transmission_loss(1000.0, 400.0)

    def test_invalid_spreading_rejected(self) -> None:
        with pytest.raises(ValueError):
            transmission_loss(1000.0, 100.0, "fancy")

    def test_nonpositive_range_rejected(self) -> None:
        with pytest.raises(ValueError):
            transmission_loss(0.0, 100.0)


class TestSonarBudget:
    def test_budget_validates(self) -> None:
        with pytest.raises(ValueError):
            SonarBudget(-1.0, 70.0, 20.0)
        with pytest.raises(ValueError):
            SonarBudget(160.0, -70.0, 20.0)
        with pytest.raises(ValueError):
            SonarBudget(160.0, 70.0, 20.0, -10.0)

    def test_fom(self) -> None:
        assert figure_of_merit_db(SonarBudget(160.0, 70.0, 20.0, 10.0)) == pytest.approx(100.0)


class TestSonarEquation:
    def test_snr_positive_near_zero_range(self) -> None:
        budget = SonarBudget(160.0, 70.0, 20.0, 10.0)
        assert passive_sonar_equation(budget, 1.0, 400.0) == pytest.approx(100.0, abs=1.0)

    def test_snr_drops_with_range(self) -> None:
        budget = SonarBudget(160.0, 70.0, 20.0, 10.0)
        assert passive_sonar_equation(budget, 10000.0, 400.0) < passive_sonar_equation(
            budget, 1000.0, 400.0
        )


class TestDetectionRange:
    def test_converged_solve(self) -> None:
        res = detection_range_m(SonarBudget(160.0, 70.0, 20.0, 10.0), 400.0)
        assert res.converged is True
        assert res.range_m > 1000.0
        # At the solved range the SNR is ~0.
        assert abs(res.snr_db) < 0.1
        assert isinstance(res, PropagationResult)

    def test_contact_unheard_even_at_one_metre(self) -> None:
        # Very weak source: not detectable anywhere.
        res = detection_range_m(SonarBudget(60.0, 80.0, 0.0, 20.0), 400.0)
        assert res.converged is False
        assert res.range_m == 0.0

    def test_max_range_capped(self) -> None:
        # Extremely loud source is detectable even past the search window.
        res = detection_range_m(SonarBudget(220.0, 70.0, 20.0, 10.0), 100.0, max_range_m=50_000.0)
        assert res.converged is True
        assert res.range_m == pytest.approx(50_000.0)

    def test_run_detection_range(self) -> None:
        res = detection_range_m(SonarBudget(160.0, 70.0, 20.0, 10.0), 400.0)
        assert res.range_m > 0.0
        assert math.isfinite(res.fom_db)
