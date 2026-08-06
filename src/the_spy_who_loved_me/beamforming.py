"""LIPARUS — uniform linear array beamforming and bearing estimation.

A passive array does not just *detect* a contact; it must say *where* it is.
This module models the classic uniform linear array (ULA) processing chain
that turns time-delayed sensor snapshots into a bearing estimate — the
geometry behind the film's sonar "firing solution":

* :func:`steering_vector` — the plane-wave phase progression across the
  array for a candidate bearing, ``a(theta) = exp(-j 2 pi (d/lambda) k
  sin(theta))``.
* :func:`array_snapshot` — a deterministic complex snapshot: a plane wave
  from a true bearing plus seeded Gaussian noise, the raw data a beamformer
  sees.
* :func:`beam_power` — the conventional (delay-and-sum) beamformer output
  power over a scan grid, ``P(theta) = |a(theta)^H x|^2``.
* :func:`estimate_bearing_deg` — the peak of the beamformer response.
* :func:`cramer_rao_bearing_std_deg` — the Cramer-Rao lower bound on
  bearing estimation error for a ULA, the theoretical floor against which
  the estimate is judged.

All deterministic: a seeded snapshot reproduces exactly, and the formulas
are standard array-processing results (Van Trees, *Optimum Array
Processing*).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    "BeamformerResult",
    "array_snapshot",
    "beam_power",
    "cramer_rao_bearing_std_deg",
    "estimate_bearing_deg",
    "interpolate_peak_deg",
    "steering_vector",
]

#: Standard scan grid half-width around broadside (degrees).
_SCAN_LIMIT_DEG = 90.0


def steering_vector(theta_rad: float, d_over_lambda: float, n_elements: int) -> np.ndarray:
    """Plane-wave steering vector of a ULA (complex, length ``n_elements``).

    Element ``k`` (0-indexed, first element at the phase reference) has the
    phase delay ``exp(-j 2 pi (d/lambda) k sin(theta))`` for a wave arriving
    from bearing ``theta_rad`` measured from broadside.
    """
    if n_elements < 2:
        raise ValueError("n_elements must be >= 2")
    if d_over_lambda <= 0.0:
        raise ValueError("d_over_lambda must be > 0")
    k = np.arange(n_elements, dtype=float)
    phase = -2.0 * math.pi * d_over_lambda * k * math.sin(theta_rad)
    return np.exp(1j * phase)  # type: ignore[no-any-return]


def array_snapshot(
    theta_true_rad: float,
    d_over_lambda: float,
    n_elements: int,
    amplitude: float,
    noise_std: float,
    seed: int,
) -> np.ndarray:
    """Deterministic complex array snapshot: signal + seeded noise.

    ``x = amplitude * a(theta_true) + noise`` where ``noise`` is circular
    complex Gaussian with standard deviation ``noise_std`` per component,
    drawn from a fixed ``seed`` so the snapshot is reproducible exactly.
    """
    a = steering_vector(theta_true_rad, d_over_lambda, n_elements)
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, noise_std / math.sqrt(2.0), n_elements) + 1j * rng.normal(
        0.0, noise_std / math.sqrt(2.0), n_elements
    )
    return amplitude * a + noise


def beam_power(snapshot: np.ndarray, theta_rad: float, d_over_lambda: float) -> float:
    """Conventional beamformer output power at a single candidate bearing.

    ``P = |a(theta)^H x|^2`` — the coherent sum of the snapshot along the
    steering direction, squared.
    """
    snapshot = np.asarray(snapshot)
    if snapshot.ndim != 1:
        raise ValueError("snapshot must be a 1-D complex array")
    a = steering_vector(theta_rad, d_over_lambda, int(snapshot.size))
    return float(np.abs(np.vdot(a, snapshot)) ** 2)


@dataclass(frozen=True)
class BeamformerResult:
    """Bearing estimate from a beamformer scan."""

    bearing_deg: float
    beam_power_peak: float
    scan: np.ndarray
    powers: np.ndarray
    n_elements: int
    d_over_lambda: float

    def as_dict(self) -> dict[str, object]:
        """Plain-dict summary for provenance records."""
        return {
            "bearing_deg": self.bearing_deg,
            "beam_power_peak": self.beam_power_peak,
            "n_elements": self.n_elements,
            "d_over_lambda": self.d_over_lambda,
        }


def _scan_grid() -> np.ndarray:
    # 0.5-degree resolution across +/-90 degrees.
    return np.arange(-_SCAN_LIMIT_DEG, _SCAN_LIMIT_DEG + 0.5, 0.5)


def interpolate_peak_deg(scan: np.ndarray, powers: np.ndarray, peak_index: int) -> float:
    """Parabolic (three-point) interpolation of the peak bearing, in degrees.

    The grid peak-search of :func:`estimate_bearing_deg` quantises the
    estimate to the scan step, so its error cannot fall below half a cell no
    matter how good the array is. Given the power samples already computed on
    the scan grid, this fits a parabola through the peak node and its two
    neighbours and places the apex at the interpolated bearing. It is the
    standard refinement that lets a beamformer approach (not beat) the
    Cramer-Rao floor.

    A corner peak (index 0 or ``len-1``) or a perfectly flat apex (zero
    denominator) has no useful three-point parabola and returns the raw grid
    node unchanged, so interpolation never makes a degenerate case worse.
    """
    n = int(len(powers))
    if peak_index <= 0 or peak_index >= n - 1 or n < 3:
        return float(scan[peak_index])
    step = float(scan[1] - scan[0]) if n > 1 else 1.0
    y0 = float(powers[peak_index - 1])
    y1 = float(powers[peak_index])
    y2 = float(powers[peak_index + 1])
    denom = y0 - 2.0 * y1 + y2
    if denom == 0.0:
        return float(scan[peak_index])
    delta = 0.5 * (y0 - y2) / denom
    return float(scan[peak_index] + delta * step)


def estimate_bearing_deg(
    snapshot: np.ndarray,
    d_over_lambda: float,
    scan: np.ndarray | None = None,
    *,
    interpolate: bool = False,
) -> BeamformerResult:
    """Scan the beamformer over the grid and return the peak-bearing estimate.

    The snapshot's ``n_elements`` defines the array size; the scan grid is
    ``[-90, 90]`` degrees at 0.5-degree resolution unless overridden.

    ``interpolate=False`` (the default) preserves the grid-quantised
    behaviour: the returned bearing is the peak search node, and its error is
    floored at half a scan cell. ``interpolate=True`` applies a three-point
    parabolic refinement (:func:`interpolate_peak_deg`) around that node, so
    the estimate can land between grid cells. The default is grid behaviour
    so existing callers' semantics (and the honest grid-quantisation story)
    do not change; interpolation is an opt-in precision improvement.
    """
    snapshot = np.asarray(snapshot)
    grid = _scan_grid() if scan is None else np.asarray(scan, dtype=float)
    powers = np.array(
        [beam_power(snapshot, math.radians(float(deg)), d_over_lambda) for deg in grid], dtype=float
    )
    idx = int(np.argmax(powers))
    bearing = float(grid[idx])
    if interpolate:
        bearing = interpolate_peak_deg(grid, powers, idx)
    return BeamformerResult(
        bearing_deg=bearing,
        beam_power_peak=float(powers[idx]),
        scan=grid,
        powers=powers,
        n_elements=int(snapshot.size),
        d_over_lambda=float(d_over_lambda),
    )


def cramer_rao_bearing_std_deg(
    n_elements: int, d_over_lambda: float, snr_db: float, theta_rad: float
) -> float:
    """Cramer-Rao lower bound on ULA bearing-estimation error (degrees).

    For a single plane wave in white noise the CRB on the bearing variance is

    .. math::
        \\sigma_\\theta \\ge \\frac{1}{\\sqrt{SNR}}
        \\sqrt{\\frac{12}{N (N^2 - 1) (2 \\pi (d/\\lambda) \\cos\\theta)^2}}

    where SNR is the element-level power ratio. Returns the standard
    deviation in degrees; the beamformer cannot be statistically more
    precise than this floor.
    """
    if n_elements < 2:
        raise ValueError("n_elements must be >= 2")
    if d_over_lambda <= 0.0:
        raise ValueError("d_over_lambda must be > 0")
    snr = 10.0 ** (float(snr_db) / 10.0)
    cos_theta = math.cos(theta_rad)
    if abs(cos_theta) < 1e-6:
        raise ValueError("bearing near endfire has unbounded CRB; use |theta| < 90 deg")
    variance = 12.0 / (
        n_elements
        * (n_elements * n_elements - 1.0)
        * (2.0 * math.pi * d_over_lambda * cos_theta) ** 2
        * snr
    )
    return float(math.degrees(math.sqrt(variance)))
