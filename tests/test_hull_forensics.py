"""Real-data, deterministic tests for pressure-hull and ballast forensics."""

from __future__ import annotations

import pytest

from the_spy_who_loved_me.hull_forensics import (
    ballast_volume_m3,
    collapse_depth_m,
    collapse_pressure_pa,
    design_safety_factor,
    elastic_buckling_pressure_pa,
    hoop_stress_pa,
    pressure_at_depth_pa,
    yield_pressure_pa,
)


class TestPressure:
    def test_pressure_increases_with_depth(self) -> None:
        assert pressure_at_depth_pa(10.0) > pressure_at_depth_pa(5.0)
        # 10 m of seawater ~= 1 bar (1e5 Pa).
        assert pressure_at_depth_pa(10.0) == pytest.approx(1.0e5, rel=0.05)

    def test_zero_and_negative(self) -> None:
        assert pressure_at_depth_pa(0.0) == pytest.approx(0.0)
        with pytest.raises(ValueError):
            pressure_at_depth_pa(-1.0)


class TestHoop:
    def test_hoop_stress_formula(self) -> None:
        # p * r / t at p=1e6 Pa, r=0.8, t=0.02 -> 4e7 Pa.
        assert hoop_stress_pa(1e6, 0.8, 0.02) == pytest.approx(4.0e7)

    def test_validates(self) -> None:
        with pytest.raises(ValueError):
            hoop_stress_pa(-1.0, 0.8, 0.02)
        with pytest.raises(ValueError):
            hoop_stress_pa(1e6, 0.0, 0.02)
        with pytest.raises(ValueError):
            hoop_stress_pa(1e6, 0.8, 0.0)


class TestBucklingAndYield:
    def test_buckling_formula(self) -> None:
        # E (t/r)^3 / (4(1-nu^2)); thicker hull buckles at higher pressure.
        p_thin = elastic_buckling_pressure_pa(0.8, 0.02, 200e9)
        p_thick = elastic_buckling_pressure_pa(0.8, 0.04, 200e9)
        assert p_thick > p_thin

    def test_yield_formula(self) -> None:
        assert yield_pressure_pa(0.8, 0.02, 350e6) == pytest.approx(8.75e6)

    def test_validates(self) -> None:
        with pytest.raises(ValueError):
            elastic_buckling_pressure_pa(0.0, 0.02, 200e9)
        with pytest.raises(ValueError):
            elastic_buckling_pressure_pa(0.8, 0.0, 200e9)
        with pytest.raises(ValueError):
            elastic_buckling_pressure_pa(0.8, 0.02, 0.0)
        with pytest.raises(ValueError):
            yield_pressure_pa(0.8, 0.02, 0.0)


class TestCollapse:
    def test_thin_hull_buckling_dominated(self) -> None:
        # Thin hull: elastic buckling pressure governs (much lower than yield).
        p = collapse_pressure_pa(0.8, 0.02, 350e6, 200e9)
        assert p == pytest.approx(elastic_buckling_pressure_pa(0.8, 0.02, 200e9))
        assert p < yield_pressure_pa(0.8, 0.02, 350e6)

    def test_thick_hull_yield_dominated(self) -> None:
        # Thick hull: yield governs (elastic buckling pressure is huge).
        p = collapse_pressure_pa(0.8, 0.4, 350e6, 200e9)
        assert p == pytest.approx(yield_pressure_pa(0.8, 0.4, 350e6))

    def test_collapse_depth(self) -> None:
        depth = collapse_depth_m(0.8, 0.02, 350e6, 200e9)
        assert depth > 0.0
        # Thicker hull -> deeper.
        assert collapse_depth_m(0.8, 0.04, 350e6, 200e9) > depth


class TestSafetyFactor:
    def test_ratio(self) -> None:
        assert design_safety_factor(85.0, 40.0) == pytest.approx(2.125)

    def test_operating_zero(self) -> None:
        with pytest.raises(ValueError):
            design_safety_factor(85.0, 0.0)


class TestBallast:
    def test_floating_vehicle_needs_ballast(self) -> None:
        # Esprit displaces 2.0 m^3 (~2050 kg) but weighs 1800 kg -> floats;
        # must flood ~0.244 m^3 to reach neutral buoyancy.
        assert ballast_volume_m3(1800.0, 2.0) == pytest.approx(0.2439, abs=1e-3)

    def test_overweight_vehicle_sinks(self) -> None:
        # Mass > displaced water -> negative ballast (must off-load weight).
        assert ballast_volume_m3(5000.0, 2.0) < 0.0

    def test_validates(self) -> None:
        with pytest.raises(ValueError):
            ballast_volume_m3(0.0, 2.0)
        with pytest.raises(ValueError):
            ballast_volume_m3(1800.0, 0.0)
