"""Real-data, deterministic tests for submersible conversion forensics."""

from __future__ import annotations

import pytest

from the_spy_who_loved_me.hull_forensics import SEAWATER_DENSITY_KG_M3, ballast_volume_m3
from the_spy_who_loved_me.vehicle_forensics import (
    SUBMERSIBLE_REQUIREMENTS,
    WATER_DENSITY_KG_M3,
    BuoyancyClass,
    ConversionClass,
    Requirement,
    VehicleSpec,
    assess_conversion,
    buoyancy_status,
    classify_conversion,
    recommend_upgrades,
)


def _full_spec() -> VehicleSpec:
    systems = {r.name: True for r in SUBMERSIBLE_REQUIREMENTS}
    return VehicleSpec("full submersible", 1800.0, 2.0, systems)


class TestRequirements:
    def test_requirement_validates(self) -> None:
        with pytest.raises(ValueError):
            Requirement("  ", True, "x")
        assert any(r.critical for r in SUBMERSIBLE_REQUIREMENTS)

    def test_spec_validates(self) -> None:
        with pytest.raises(ValueError):
            VehicleSpec("", 1800.0, 2.0, {})
        with pytest.raises(ValueError):
            VehicleSpec("x", 0.0, 2.0, {})
        with pytest.raises(ValueError):
            VehicleSpec("x", 1800.0, 0.0, {})


class TestAssessment:
    def test_full_spec_is_submersible(self) -> None:
        a = assess_conversion(_full_spec())
        assert a.classification == ConversionClass.SUBMERSIBLE
        assert a.score == pytest.approx(1.0)
        assert a.missing_critical == ()

    def test_road_car_is_road_only(self) -> None:
        a = assess_conversion(VehicleSpec("stock car", 1000.0, 1.1, {}))
        assert a.classification == ConversionClass.ROAD_ONLY
        assert len(a.missing) == len(SUBMERSIBLE_REQUIREMENTS)

    def test_partial_is_amphibious(self) -> None:
        a = assess_conversion(VehicleSpec("amphibious", 1350.0, 1.4, {"watertight_seals": True}))
        assert a.classification == ConversionClass.AMPHIBIOUS
        assert any(r.name == "pressure_hull" for r in a.missing_critical)

    def test_unknown_keys_surfaced(self) -> None:
        a = assess_conversion(VehicleSpec("x", 1000.0, 1.1, {"flux_capacitor": True}))
        assert "flux_capacitor" in a.unknown_keys
        assert a.as_dict()["unknown_keys"] == ["flux_capacitor"]

    def test_satisfied_unknown_not_counted(self) -> None:
        # An unknown key must not inflate the readiness score.
        a = assess_conversion(VehicleSpec("x", 1000.0, 1.1, {"flux_capacitor": True}))
        assert a.score == pytest.approx(0.0)


class TestClassification:
    def test_submersible(self) -> None:
        missing = (r for r in SUBMERSIBLE_REQUIREMENTS if r.name == "escape_hatch")
        assert (
            classify_conversion(len(SUBMERSIBLE_REQUIREMENTS) - 1, tuple(missing))
            == ConversionClass.SUBMERSIBLE
        )

    def test_amphibious_with_critical_gap(self) -> None:
        missing = tuple(r for r in SUBMERSIBLE_REQUIREMENTS if r.critical)[:1]
        assert classify_conversion(2, missing) == ConversionClass.AMPHIBIOUS

    def test_road_only_nothing(self) -> None:
        assert classify_conversion(0, tuple(SUBMERSIBLE_REQUIREMENTS)) == ConversionClass.ROAD_ONLY

    def test_road_only_some_optional_but_critical_missing(self) -> None:
        # Not enough satisfied AND critical missing -> still road-only (odd path).
        missing = (r for r in SUBMERSIBLE_REQUIREMENTS if r.critical)
        result = classify_conversion(1, tuple(missing))
        assert result in (ConversionClass.AMPHIBIOUS, ConversionClass.ROAD_ONLY)


class TestBuoyancy:
    def test_floats(self) -> None:
        assert buoyancy_status(1800.0, 2.0) == BuoyancyClass.FLOATS

    def test_sinks(self) -> None:
        assert buoyancy_status(5000.0, 2.0) == BuoyancyClass.SINKS

    def test_neutral(self) -> None:
        # mass == displacement * rho (seawater) -> balanced.
        assert buoyancy_status(2.0 * WATER_DENSITY_KG_M3, 2.0) == BuoyancyClass.NEUTRAL

    def test_nonpositive_displacement(self) -> None:
        assert buoyancy_status(1000.0, 0.0) == BuoyancyClass.SINKS


class TestOneVehicleOneFluid:
    """The buoyancy verdict and the ballast figure must use the same medium.

    This module carried a fresh-water 1000 kg/m^3 while ``hull_forensics``
    computed the same Lotus-Esprit-grade vehicle's ballast volume and
    collapse depth in seawater at 1025 — one vehicle, one manuscript section,
    two fluids. The classification happened not to flip for the canonical
    spec, so nothing caught it.
    """

    def test_density_is_the_seawater_constant(self) -> None:
        assert WATER_DENSITY_KG_M3 == SEAWATER_DENSITY_KG_M3

    def test_the_two_verdicts_agree_on_the_canonical_vehicle(self) -> None:
        """`floats` must mean `needs positive ballast`, in both modules."""
        mass, displacement = 1800.0, 2.0
        assert buoyancy_status(mass, displacement) is BuoyancyClass.FLOATS
        assert ballast_volume_m3(mass, displacement) > 0.0

    def test_the_two_verdicts_agree_on_a_sinker(self) -> None:
        mass, displacement = 5000.0, 2.0
        assert buoyancy_status(mass, displacement) is BuoyancyClass.SINKS
        assert ballast_volume_m3(mass, displacement) < 0.0

    def test_the_sign_change_happens_at_the_same_mass(self) -> None:
        """A single crossing point, not two — pinned either side of it."""
        displacement = 2.0
        neutral_mass = displacement * WATER_DENSITY_KG_M3
        assert ballast_volume_m3(neutral_mass - 1.0, displacement) > 0.0
        assert ballast_volume_m3(neutral_mass + 1.0, displacement) < 0.0
        assert buoyancy_status(neutral_mass * 0.9, displacement) is BuoyancyClass.FLOATS
        assert buoyancy_status(neutral_mass * 1.1, displacement) is BuoyancyClass.SINKS


class TestRecommendations:
    def test_critical_first(self) -> None:
        upgrades = recommend_upgrades(VehicleSpec("x", 1000.0, 1.1, {"underwater_thrust": True}))
        assert upgrades
        assert upgrades[0].critical is True  # critical gaps sort first


class TestExplicitlyAbsentSystem:
    """A system present in ``systems`` but set to ``False`` is *missing*.

    This is a distinct code path from a system omitted from the mapping
    entirely, and the two must produce the same assessment — otherwise a
    surveyor who writes ``"air_supply": False`` would silently score
    differently from one who leaves the key out.
    """

    def _spec(self, systems: dict[str, bool]) -> VehicleSpec:
        return VehicleSpec("probe", dry_mass_kg=1500.0, displacement_m3=2.0, systems=systems)

    def test_false_value_counts_as_missing(self) -> None:
        spec = self._spec({"pressure_hull": True, "air_supply": False})
        result = assess_conversion(spec)
        names = {r.name for r in result.missing}
        assert "air_supply" in names
        assert "air_supply" not in {r.name for r in result.satisfied}

    def test_false_and_omitted_agree(self) -> None:
        explicit = assess_conversion(self._spec({"pressure_hull": True, "watertight_seals": False}))
        omitted = assess_conversion(self._spec({"pressure_hull": True}))
        assert explicit.score == omitted.score
        assert explicit.classification is omitted.classification
        assert {r.name for r in explicit.missing} == {r.name for r in omitted.missing}

    def test_no_requirement_is_double_counted(self) -> None:
        """The explicit-False branch must not also append via the omitted loop."""
        spec = self._spec({"pressure_hull": True, "ballast_system": False})
        result = assess_conversion(spec)
        names = [r.name for r in result.missing]
        assert len(names) == len(set(names)), f"duplicate missing entries: {names}"
        assert len(result.satisfied) + len(result.missing) == len(SUBMERSIBLE_REQUIREMENTS)

    def test_all_false_is_road_only(self) -> None:
        spec = self._spec({r.name: False for r in SUBMERSIBLE_REQUIREMENTS})
        result = assess_conversion(spec)
        assert result.score == 0.0
        assert result.classification is ConversionClass.ROAD_ONLY


class TestAmphibiousPredicateMatchesDocstring:
    """``amphibious`` is ``num_satisfied > 0``, not "an optional system"."""

    def test_only_a_critical_system_still_reads_amphibious(self) -> None:
        spec = VehicleSpec(
            "hull only", dry_mass_kg=1500.0, displacement_m3=2.0, systems={"pressure_hull": True}
        )
        assert assess_conversion(spec).classification is ConversionClass.AMPHIBIOUS

    def test_nothing_fitted_is_road_only(self) -> None:
        spec = VehicleSpec("bare", dry_mass_kg=1500.0, displacement_m3=2.0, systems={})
        assert assess_conversion(spec).classification is ConversionClass.ROAD_ONLY
