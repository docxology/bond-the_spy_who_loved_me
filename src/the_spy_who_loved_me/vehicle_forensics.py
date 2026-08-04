"""LIPARUS — submersible vehicle conversion forensics.

In *The Spy Who Loved Me* Bond's Lotus Esprit converts into a submersible
capable of driving underwater and re-emerging. This module forensically
assesses whether a given road vehicle *can* be converted to submersible duty
and how complete a claimed conversion is, using requirement traceability,
hard physical feasibility (Archimedes buoyancy), and a deterministic scoring
scheme. No mocks, no RNG: every verdict is a pure function of the vehicle
spec.

Three capabilities:

* :func:`assess_conversion` — requirement traceability: which of the
  documented submersible requirements the spec satisfies, a readiness score,
  and any missing *critical* systems.
* :func:`classify_conversion` — map an assessment to a readiness class:
  ``road-only``, ``amphibious``, or ``submersible``.
* :func:`buoyancy_status` — Archimedes feasibility: does the vehicle float,
  sink, or sit balanced given dry mass and displaced volume.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass

__all__ = [
    "BuoyancyClass",
    "ConversionAssessment",
    "ConversionClass",
    "Requirement",
    "VehicleSpec",
    "assess_conversion",
    "buoyancy_status",
    "classify_conversion",
    "recommend_upgrades",
]

#: Density of fresh water (kg/m^3) used for the buoyancy reference.
WATER_DENSITY_KG_M3 = 1000.0
#: Gravity, m/s^2.
G_MPS2 = 9.81


class ConversionClass(str, enum.Enum):
    """Readiness class of a vehicle's submersible conversion."""

    ROAD_ONLY = "road-only"
    AMPHIBIOUS = "amphibious"
    SUBMERSIBLE = "submersible"


class BuoyancyClass(str, enum.Enum):
    """Archimedean state of the as-spec vehicle."""

    FLOATS = "floats"
    SINKS = "sinks"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class Requirement:
    """A single system required for submersible conversion.

    ``critical`` marks requirements whose absence alone disqualifies a
    vehicle from submersible status (a vehicle can neither submerge nor stay
    breathable without them).
    """

    name: str
    critical: bool
    rationale: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Requirement.name must be non-empty")


#: The canonical submersible-conversion requirement set.
SUBMERSIBLE_REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement("pressure_hull", True, "structure must withstand hydrostatic depth"),
    Requirement("watertight_seals", True, "no ingress through hatches or windows"),
    Requirement("ballast_system", True, "controlled buoyancy to dive and surface"),
    Requirement("air_supply", True, "breathable air with scrubber for submerged crew"),
    Requirement("underwater_thrust", False, "propulsion that works submerged"),
    Requirement("depth_rating", False, "rated for the intended operating depth"),
    Requirement("navigation_sonar", False, "sense surroundings when vision is void"),
    Requirement("battery_power", False, "isolated high-capacity power while submerged"),
    Requirement("escape_hatch", False, "egress channel independent of the main hatch"),
)


@dataclass(frozen=True)
class VehicleSpec:
    """A candidate road vehicle and the submersible systems fitted to it.

    ``systems`` maps requirement names (from :data:`SUBMERSIBLE_REQUIREMENTS`)
    to booleans; unknown keys are ignored with a warning carried on the
    assessment. ``plausible_road`` is a string describing the donor vehicle.
    """

    name: str
    dry_mass_kg: float
    displacement_m3: float
    systems: Mapping[str, bool]
    plausible_road: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("VehicleSpec.name must be non-empty")
        if self.dry_mass_kg <= 0.0:
            raise ValueError("dry_mass_kg must be > 0")
        if self.displacement_m3 <= 0.0:
            raise ValueError("displacement_m3 must be > 0")


@dataclass(frozen=True)
class ConversionAssessment:
    """Forensic result of evaluating a vehicle spec against the requirements."""

    spec: VehicleSpec
    satisfied: tuple[Requirement, ...]
    missing: tuple[Requirement, ...]
    unknown_keys: tuple[str, ...]
    score: float
    classification: ConversionClass

    @property
    def missing_critical(self) -> tuple[Requirement, ...]:
        """The missing requirements that are critical to submersible status."""
        return tuple(r for r in self.missing if r.critical)

    def as_dict(self) -> dict[str, object]:
        """Plain-dict summary for provenance records."""
        return {
            "vehicle": self.spec.name,
            "classification": self.classification.value,
            "score": self.score,
            "satisfied": [r.name for r in self.satisfied],
            "missing": [r.name for r in self.missing],
            "missing_critical": [r.name for r in self.missing_critical],
            "unknown_keys": list(self.unknown_keys),
        }


def assess_conversion(spec: VehicleSpec) -> ConversionAssessment:
    """Evaluate a spec against the submersible requirement set.

    The readiness ``score`` is the fraction of the *fitted, recognised*
    systems relative to the full requirement set (unknown keys do not count
    toward satisfaction but are surfaced). ``classification`` is derived from
    :func:`classify_conversion`.
    """
    by_name = {r.name: r for r in SUBMERSIBLE_REQUIREMENTS}
    satisfied: list[Requirement] = []
    missing: list[Requirement] = []
    unknown: list[str] = []
    for name, present in spec.systems.items():
        req = by_name.get(name)
        if req is None:
            unknown.append(name)
        elif present:
            satisfied.append(req)
        else:
            missing.append(req)
    for req in SUBMERSIBLE_REQUIREMENTS:
        if req.name not in spec.systems:
            missing.append(req)
    score = len(satisfied) / len(SUBMERSIBLE_REQUIREMENTS)
    clazz = classify_conversion(len(satisfied), tuple(missing))
    return ConversionAssessment(
        spec=spec,
        satisfied=tuple(satisfied),
        missing=tuple(missing),
        unknown_keys=tuple(unknown),
        score=score,
        classification=clazz,
    )


def classify_conversion(num_satisfied: int, missing: tuple[Requirement, ...]) -> ConversionClass:
    """Map satisfaction counts and missing requirements to a readiness class.

    * ``submersible`` — no critical requirement missing *and* at least half
      of all requirements satisfied;
    * ``amphibious`` — at least one optional system satisfied (can wet its
      wheels) but still missing a critical requirement;
    * ``road-only`` — otherwise.
    """
    missing_critical = any(r.critical for r in missing)
    any_satisfied = num_satisfied > 0
    if not missing_critical and num_satisfied >= len(SUBMERSIBLE_REQUIREMENTS) / 2:
        return ConversionClass.SUBMERSIBLE
    if any_satisfied and missing_critical:
        return ConversionClass.AMPHIBIOUS
    return ConversionClass.ROAD_ONLY


def buoyancy_status(dry_mass_kg: float, displacement_m3: float) -> BuoyancyClass:
    """Archimedes feasibility from dry mass and displaced volume.

    Buoyant force ``Fb = displacement * water_density * g`` compared against
    weight ``W = mass * g`` (g cancels). ``floats`` when buoyant force
    exceeds weight; ``sinks`` when weight exceeds buoyant force; ``neutral``
    within a 1% band of balance.
    """
    buoyant_force = displacement_m3 * WATER_DENSITY_KG_M3 * G_MPS2
    weight = dry_mass_kg * G_MPS2
    ratio = weight / buoyant_force if buoyant_force > 0.0 else float("inf")
    if abs(ratio - 1.0) <= 0.01:
        return BuoyancyClass.NEUTRAL
    if ratio < 1.0:
        return BuoyancyClass.FLOATS
    return BuoyancyClass.SINKS


def recommend_upgrades(spec: VehicleSpec) -> tuple[Requirement, ...]:
    """Return the missing requirements as an ordered retrofit list.

    Critical requirements sort first so the recommendation surfaces the
    life-safety gaps ahead of the comfort/convenience ones.
    """
    assessment = assess_conversion(spec)
    return tuple(sorted(assessment.missing, key=lambda r: (not r.critical, r.name)))
