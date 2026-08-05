"""LIPARUS — underwater acoustic propagation and the passive sonar equation.

The *Liparus* and its quarry live in a medium that is far from transparent:
seawater absorbs and spreads acoustic energy, and a passive array hears a
contact only when the received signal exceeds the ambient noise. This module
models those physics with real, textbook formulas, all deterministic:

* :func:`thorp_absorption` — Thorp's (1967) low-frequency seawater
  absorption coefficient in dB/km as a function of frequency.
* :func:`transmission_loss` — geometric spreading (spherical or
  cylindrical) plus absorption, ``TL(r) = n*10*log10(r) + alpha*r``.
* :func:`passive_sonar_equation` — the passive sonar equation in its
  *signal-excess* form ``SE = SL - TL - (NL - DI) - DT``, the standard
  detection budget. Note the ``- DT``: signal excess is the margin over the
  detection threshold, and is **not** the signal-to-noise ratio (which is
  ``SL - TL - (NL - DI)``, i.e. ``SE + DT``). Urick, *Principles of
  Underwater Sound*, keeps the two distinct and so does this module.
* :func:`detection_range_m` — the range at which the propagation loss
  exhausts the figure of merit, solved by monotone bisection.
* :func:`sound_speed_m_s` — the Mackenzie (1981) sound-speed equation
  as a function of temperature, salinity and depth.

All functions are pure; no randomness, no wall-clock.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "PropagationResult",
    "SonarBudget",
    "detection_range_m",
    "figure_of_merit_db",
    "passive_sonar_equation",
    "signal_to_noise_ratio_db",
    "sound_speed_m_s",
    "thorp_absorption",
    "transmission_loss",
]


def thorp_absorption(freq_hz: float) -> float:
    """Thorp (1967) seawater absorption in dB/km at ``freq_hz``.

    The classic low-frequency expression (with frequency ``f`` in kHz):

    .. math::
        \\alpha = \\frac{0.1 f^2}{1+f^2} + \\frac{40 f^2}{4100+f^2}
                  + 2.75\\times10^{-4} f^2 + 0.003

    Valid and smooth over the sonar band (tens of Hz to tens of kHz).
    """
    if freq_hz < 0.0:
        raise ValueError("freq_hz must be >= 0")
    f = freq_hz / 1000.0
    return float(
        0.1 * f * f / (1.0 + f * f) + 40.0 * f * f / (4100.0 + f * f) + 2.75e-4 * f * f + 0.003
    )


def sound_speed_m_s(temperature_c: float, salinity_psu: float, depth_m: float) -> float:
    """Mackenzie (1981) sound speed (m/s) in seawater.

    Nine-term equation valid for temperature 0-30 C, salinity 30-40 PSU,
    depth 0-8000 m:

    .. math::
        c = 1448.96 + 4.591T - 5.304\\times10^{-2} T^2 + 2.374\\times10^{-4} T^3
            + 1.340(S-35) + 1.630\\times10^{-2}D + 1.675\\times10^{-7}D^2
            - 1.025\\times10^{-2}T(S-35) - 7.139\\times10^{-13}TD^3
    """
    t = float(temperature_c)
    s = float(salinity_psu)
    d = float(depth_m)
    return float(
        1448.96
        + 4.591 * t
        - 5.304e-2 * t * t
        + 2.374e-4 * t**3
        + 1.340 * (s - 35.0)
        + 1.630e-2 * d
        + 1.675e-7 * d * d
        - 1.025e-2 * t * (s - 35.0)
        - 7.139e-13 * t * d**3
    )


def _spreading_loss_db(range_m: float, spreading: str) -> float:
    if range_m <= 0.0:
        raise ValueError("range_m must be > 0")
    if spreading == "spherical":
        return 20.0 * math.log10(range_m)
    if spreading == "cylindrical":
        return 10.0 * math.log10(range_m)
    raise ValueError("spreading must be 'spherical' or 'cylindrical'")


def transmission_loss(range_m: float, freq_hz: float, spreading: str = "spherical") -> float:
    """Propagation loss ``TL(r) = n*10*log10(r) + alpha*r`` (dB).

    ``n`` is 2 for spherical spreading, 1 for cylindrical. Absorption is
    applied per kilometre via :func:`thorp_absorption`.
    """
    spread = _spreading_loss_db(range_m, spreading)
    absorption = thorp_absorption(freq_hz) * (range_m / 1000.0)
    return spread + absorption


@dataclass(frozen=True)
class SonarBudget:
    """A passive sonar detection budget (all levels in dB re 1 uPa).

    ``sl`` is the source level of the contact, ``nl`` the ambient noise
    level, ``di`` the directivity index of the receiving array, and ``dt``
    the detection threshold (the SNR required for a reliable decision).
    """

    sl_db: float
    nl_db: float
    di_db: float
    dt_db: float = 10.0

    def __post_init__(self) -> None:
        for label, value in (
            ("sl_db", self.sl_db),
            ("nl_db", self.nl_db),
            ("di_db", self.di_db),
            ("dt_db", self.dt_db),
        ):
            if value < 0.0:
                raise ValueError(f"{label} must be >= 0")


def figure_of_merit_db(budget: SonarBudget) -> float:
    """Figure of merit ``FOM = SL - (NL - DI) - DT`` (dB).

    The propagation loss a contact may suffer before its SNR falls below
    the detection threshold.
    """
    return float(budget.sl_db - (budget.nl_db - budget.di_db) - budget.dt_db)


def passive_sonar_equation(
    budget: SonarBudget, range_m: float, freq_hz: float, spreading: str = "spherical"
) -> float:
    """Passive sonar equation: **signal excess** at ``range_m`` (dB).

    ``SE = SL - TL(range) - (NL - DI) - DT``. The contact is detectable when
    the signal excess is non-negative — that is what the ``- DT`` term buys.

    This quantity is deliberately *not* called an SNR: the signal-to-noise
    ratio at the array output is ``SL - TL - (NL - DI)``, which is larger by
    exactly the detection threshold ``DT``. Use
    :func:`signal_to_noise_ratio_db` when the SNR is what is wanted.
    """
    tl = transmission_loss(range_m, freq_hz, spreading)
    return float(figure_of_merit_db(budget) - tl)


def signal_to_noise_ratio_db(
    budget: SonarBudget, range_m: float, freq_hz: float, spreading: str = "spherical"
) -> float:
    """Signal-to-noise ratio at the array output (dB).

    ``SNR = SL - TL(range) - (NL - DI)``, i.e. the signal excess of
    :func:`passive_sonar_equation` plus the detection threshold ``DT``.
    """
    return passive_sonar_equation(budget, range_m, freq_hz, spreading) + float(budget.dt_db)


@dataclass(frozen=True)
class PropagationResult:
    """Outcome of a detection-range solve.

    ``signal_excess_db`` is ``SL - TL - (NL - DI) - DT`` at ``range_m`` — the
    margin over the detection threshold, not the SNR (this field was named
    ``snr_db`` until the two quantities were separated).
    """

    range_m: float
    signal_excess_db: float
    tl_db: float
    fom_db: float
    converged: bool


def detection_range_m(
    budget: SonarBudget,
    freq_hz: float,
    spreading: str = "spherical",
    *,
    max_range_m: float = 200_000.0,
    tolerance_m: float = 1.0,
) -> PropagationResult:
    """Solve the maximum detectable range by monotone bisection.

    ``TL(r)`` is strictly increasing in ``r``, so the equation
    ``TL(r) = FOM`` has at most one root; bisection on ``[1, max_range_m]``
    is deterministic and exact to ``tolerance_m``. When the contact is not
    detectable even at 1 m (negative signal excess at the closest range), the
    solve returns ``range_m=0`` with ``converged=False``.
    """
    fom = figure_of_merit_db(budget)
    excess_at_one = passive_sonar_equation(budget, 1.0, freq_hz, spreading)
    if excess_at_one < 0.0:
        return PropagationResult(
            0.0, excess_at_one, transmission_loss(1.0, freq_hz, spreading), fom, False
        )
    lo, hi = 1.0, float(max_range_m)
    if passive_sonar_equation(budget, hi, freq_hz, spreading) > 0.0:
        # Even the maximum range is detectable: report the capped range.
        return PropagationResult(
            hi,
            passive_sonar_equation(budget, hi, freq_hz, spreading),
            transmission_loss(hi, freq_hz, spreading),
            fom,
            True,
        )
    while hi - lo > tolerance_m:
        mid = 0.5 * (lo + hi)
        if passive_sonar_equation(budget, mid, freq_hz, spreading) > 0.0:
            lo = mid
        else:
            hi = mid
    range_m = 0.5 * (lo + hi)
    return PropagationResult(
        range_m,
        passive_sonar_equation(budget, range_m, freq_hz, spreading),
        transmission_loss(range_m, freq_hz, spreading),
        fom,
        True,
    )
