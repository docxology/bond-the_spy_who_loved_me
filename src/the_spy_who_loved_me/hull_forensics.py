"""LIPARUS — pressure-hull and ballast forensics for submersible conversion.

The Lotus-Esprit-grade submersible in *The Spy Who Loved Me* must survive
the hydrostatic pressure of the operating depth and be able to control its
buoyancy. This module puts hard numbers on both, with standard
pressure-vessel and naval-architecture formulas, all deterministic:

* :func:`hoop_stress_pa` — the circumferential stress in a thin cylindrical
  hull, ``sigma = p r / t``.
* :func:`elastic_buckling_pressure_pa` — the long-cylinder elastic buckling
  pressure ``p_cr = E (t/r)^3 / (4(1-nu^2))`` (the mode-2 lobe collapse
  that dominates unstiffened hulls).
* :func:`yield_pressure_pa` — the pressure at which hoop stress reaches the
  material yield strength, ``p_y = sigma_y t / r``.
* :func:`collapse_pressure_pa` / :func:`collapse_depth_m` — the governing
  (minimum of the two) collapse pressure and its equivalent depth in
  seawater.
* :func:`ballast_volume_m3` — the flood-water volume required to reach
  neutral buoyancy (Archimedes), the figure of merit for "can this car
  actually dive?".

These are the same first-order checks a conversion surveyor would run. The
long-cylinder buckling expression is Timoshenko & Gere, *Theory of Elastic
Stability* (2nd ed., 1961); the thin-wall hoop-stress and Archimedean
relations are standard (Young & Budynas, *Roark's Formulas for Stress and
Strain*; Tupper, *Introduction to Naval Architecture*).
"""

from __future__ import annotations

__all__ = [
    "SEAWATER_DENSITY_KG_M3",
    "ballast_volume_m3",
    "collapse_depth_m",
    "collapse_pressure_pa",
    "design_safety_factor",
    "elastic_buckling_pressure_pa",
    "hoop_stress_pa",
    "pressure_at_depth_pa",
    "yield_pressure_pa",
]

#: Density of seawater, kg/m^3.
SEAWATER_DENSITY_KG_M3 = 1025.0

#: Standard gravity, m/s^2.
GRAVITY_MPS2 = 9.81


def pressure_at_depth_pa(
    depth_m: float, water_density_kg_m3: float = SEAWATER_DENSITY_KG_M3
) -> float:
    """Hydrostatic pressure ``p = rho g h`` (Pa) at ``depth_m``."""
    if depth_m < 0.0:
        raise ValueError("depth_m must be >= 0")
    return float(water_density_kg_m3 * GRAVITY_MPS2 * depth_m)


def hoop_stress_pa(pressure_pa: float, radius_m: float, thickness_m: float) -> float:
    """Circumferential (hoop) stress in a thin cylinder, ``p r / t`` (Pa)."""
    if pressure_pa < 0.0:
        raise ValueError("pressure_pa must be >= 0")
    if radius_m <= 0.0 or thickness_m <= 0.0:
        raise ValueError("radius_m and thickness_m must be > 0")
    return float(pressure_pa * radius_m / thickness_m)


def elastic_buckling_pressure_pa(
    radius_m: float,
    thickness_m: float,
    young_modulus_pa: float,
    poisson_ratio: float = 0.3,
) -> float:
    """Elastic buckling pressure of a long unstiffened cylinder (Pa).

    The classic mode-2 collapse pressure
    ``p_cr = E (t/r)^3 / (4 (1 - nu^2))``. Unstiffened cylindrical hulls are
    buckling-limited, not strength-limited, at deep operating depths — this
    is why real submersibles are ring-stiffened.
    """
    if radius_m <= 0.0 or thickness_m <= 0.0:
        raise ValueError("radius_m and thickness_m must be > 0")
    if young_modulus_pa <= 0.0:
        raise ValueError("young_modulus_pa must be > 0")
    ratio = thickness_m / radius_m
    return float(young_modulus_pa * ratio**3 / (4.0 * (1.0 - poisson_ratio * poisson_ratio)))


def yield_pressure_pa(radius_m: float, thickness_m: float, yield_stress_pa: float) -> float:
    """Pressure at which the hoop stress reaches yield (Pa), ``sigma_y t / r``."""
    if yield_stress_pa <= 0.0:
        raise ValueError("yield_stress_pa must be > 0")
    return float(yield_stress_pa * thickness_m / radius_m)


def collapse_pressure_pa(
    radius_m: float,
    thickness_m: float,
    yield_stress_pa: float,
    young_modulus_pa: float,
    poisson_ratio: float = 0.3,
) -> float:
    """Governing collapse pressure (Pa): the minimum of buckling and yield.

    A conservative first-order model treats the hull as failing at whichever
    limit is reached first — elastic buckling for thin hulls, material yield
    for thick ones.
    """
    buckling = elastic_buckling_pressure_pa(radius_m, thickness_m, young_modulus_pa, poisson_ratio)
    yield_p = yield_pressure_pa(radius_m, thickness_m, yield_stress_pa)
    return min(buckling, yield_p)


def collapse_depth_m(
    radius_m: float,
    thickness_m: float,
    yield_stress_pa: float,
    young_modulus_pa: float,
    poisson_ratio: float = 0.3,
    water_density_kg_m3: float = SEAWATER_DENSITY_KG_M3,
) -> float:
    """Depth (m) at which the hull collapses, ``p_collapse / (rho g)``."""
    p = collapse_pressure_pa(
        radius_m, thickness_m, yield_stress_pa, young_modulus_pa, poisson_ratio
    )
    return float(p / (water_density_kg_m3 * GRAVITY_MPS2))


def ballast_volume_m3(
    vehicle_mass_kg: float,
    displacement_m3: float,
    water_density_kg_m3: float = SEAWATER_DENSITY_KG_M3,
) -> float:
    """Flood-water volume (m^3) needed to reach neutral buoyancy.

    Flooding a ballast tank adds *mass* at constant displaced volume — the
    hull envelope does not grow when water enters it. Neutral buoyancy is
    therefore

    .. math::
        D \\rho g = (m + V \\rho) g
        \\quad\\Longrightarrow\\quad
        V = D - \\frac{m}{\\rho}

    with ``D`` the displaced volume, ``m`` the dry mass and ``rho`` the water
    density — which is what this function returns.

    A **positive** result is the volume of water that must be taken aboard:
    the vehicle displaces more than it weighs, so it floats and must be made
    heavier to dive. A **negative** result means the vehicle is already
    denser than the water it displaces — it sinks as it stands, needs no
    ballast at all, and the magnitude is the water volume's worth of mass it
    would have to shed (or displacement it would have to gain) to become
    neutral.
    """
    if vehicle_mass_kg <= 0.0:
        raise ValueError("vehicle_mass_kg must be > 0")
    if displacement_m3 <= 0.0:
        raise ValueError("displacement_m3 must be > 0")
    return float((displacement_m3 * water_density_kg_m3 - vehicle_mass_kg) / water_density_kg_m3)


def design_safety_factor(collapse_depth_m: float, operating_depth_m: float) -> float:
    """Ratio of collapse depth to operating depth (dimensionless).

    A factor below 1.0 means the hull collapses shallower than its intended
    operating depth — a conversion that is not fit for purpose.
    """
    if operating_depth_m <= 0.0:
        raise ValueError("operating_depth_m must be > 0")
    return float(collapse_depth_m / operating_depth_m)
