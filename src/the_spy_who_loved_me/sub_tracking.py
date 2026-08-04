"""LIPARUS — passive acoustic submarine detection and bearing-only tracking.

This module models the core signal-processing problem a passive-array sensor
faces when hunting a submarine that emits nothing deliberately (as in *The
Spy Who Loved Me*, where the quarry is detected only by the machinery noise
it cannot avoid radiating). Three deterministic capabilities are provided:

1. :func:`detect_contract` — a Neyman–Pearson energy detector. The received
   waveform (ambient noise, optionally plus a narrow-band tonal) is windowed
   and the statistic ``T = sum(x**2)/noise_var`` is compared against a
   threshold quantile of the central chi-square distribution computed in
   closed form via the Wilson–Hilferty approximation, giving a detection
   decision at a *controlled* false-alarm probability ``P_FA``.

2. :func:`simulate_target_track` — a deterministic scenario: a
   constant-velocity submarine observed by a *maneuvering* ownship (a
   dogleg course change), producing a sequence of noisy relative bearings.
   The observer maneuver is essential: bearing-only geometry cannot recover
   absolute range or speed from a stationary observer (the trajectory is
   scale-ambiguous); a change of ownship course makes the state observable.

3. :func:`estimate_tma` — batch least-squares target motion analysis. Given
   the bearing history and the known ownship path, it solves for the target
   position and velocity that best reproduce the bearings (coarse grid
   initialisation, then Gauss–Newton refinement). :class:`PassiveBearingTracker`
   is the matching recursive Extended Kalman Filter for online use.

All algorithms are deterministic for fixed seeds/parameters, so tests can
assert exact convergence without mocking anything.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

__all__ = [
    "Detection",
    "DetectionConfig",
    "PassiveBearingTracker",
    "TrackSimulation",
    "TrackSolution",
    "chi2_quantile",
    "detect_contract",
    "estimate_tma",
    "inverse_normal_cdf",
    "simulate_target_track",
    "tracking_rms_error",
]

#: Density of seawater, kg/m^3 — the acoustic and buoyancy reference medium.
SEAWATER_DENSITY_KG_M3 = 1025.0


@dataclass(frozen=True)
class DetectionConfig:
    """Tunables for the Neyman–Pearson energy detector.

    ``noise_variance`` is the expected per-sample variance of the ambient
    noise (sigma^2) used to normalise the test statistic. ``window`` is the
    number of samples integrated per detection cell. ``p_fa`` is the target
    false-alarm probability — the threshold is chosen so that, under the
    noise-only hypothesis, the statistic exceeds it with probability ``p_fa``.
    """

    noise_variance: float = 1.0
    window: int = 64
    p_fa: float = 1e-3

    def __post_init__(self) -> None:
        if self.noise_variance <= 0.0:
            raise ValueError("noise_variance must be > 0")
        if self.window < 1:
            raise ValueError("window must be >= 1")
        if not 0.0 < self.p_fa < 1.0:
            raise ValueError("p_fa must lie in (0, 1)")


@dataclass(frozen=True)
class Detection:
    """Result of running the energy detector on one window of samples."""

    detected: bool
    statistic: float
    threshold: float
    p_fa: float

    @property
    def margin_db(self) -> float:
        """Detection margin (statistic / threshold) in decibels."""
        return 10.0 * math.log10(max(self.statistic, 1e-12) / max(self.threshold, 1e-12))


def inverse_normal_cdf(p: float) -> float:
    """Acklam's closed-form approximation of the standard normal quantile.

    Deterministic and dependency-free; ``erfinv``-equivalent accuracy to
    roughly nine significant figures for ``0 < p < 1``. Splits the domain
    into a central rational polynomial and two rational (Ogita-style) tail
    approximations.
    """
    if not 0.0 < p < 1.0:
        raise ValueError("p must lie in (0, 1)")
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00)

    def _tail(q: float) -> float:
        num = c[0] * q + c[1]
        num = num * q + c[2]
        num = num * q + c[3]
        num = num * q + c[4]
        num = num * q + c[5]
        den = d[0] * q + d[1]
        den = den * q + d[2]
        den = den * q + d[3]
        den = den * q + 1.0
        return num / den

    p_low = 0.02425
    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        return _tail(q)
    if p > 1.0 - p_low:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -_tail(q)
    q = p - 0.5
    r = q * q
    num = ((a[0] * r + a[1]) * r + a[2]) * r + a[3]
    num = (num * r + a[4]) * r + a[5]
    den = ((b[0] * r + b[1]) * r + b[2]) * r + b[3]
    den = (den * r + b[4]) * r + 1.0
    return num * q / den


def chi2_quantile(nu: int, p: float) -> float:
    """Approximate the ``p``-quantile of a central chi-square with ``nu`` dof.

    Uses the Wilson–Hilferty transform ``nu * (1 - 2/(9nu) + z*sqrt(2/(9nu)))**3``.
    """
    if nu < 1:
        raise ValueError("nu must be >= 1")
    if not 0.0 < p < 1.0:
        raise ValueError("p must lie in (0, 1)")
    z = inverse_normal_cdf(p)
    scale = 1.0 - 2.0 / (9.0 * nu)
    return nu * (scale + z * math.sqrt(2.0 / (9.0 * nu))) ** 3


def _window_statistic(samples: np.ndarray, window: int) -> np.ndarray:
    """Energy statistic of non-overlapping windows of ``samples`` (sum of squares)."""
    n_full = (samples.size // window) * window
    reshaped = samples[:n_full].reshape(-1, window)
    return np.einsum("ij,ij->i", reshaped, reshaped)  # type: ignore[no-any-return]


def detect_contract(samples: np.ndarray, config: DetectionConfig | None = None) -> Detection:
    """Run a Neyman–Pearson energy detector over a received waveform.

    The samples are split into non-overlapping windows of ``config.window``;
    each window statistic ``T = sum(x**2)/noise_variance`` is compared against
    the ``(1 - p_fa)``-quantile of a chi-square with ``window`` dof. A
    contact is detected when any window crosses the threshold.
    """
    cfg = config or DetectionConfig()
    arr = np.asarray(samples, dtype=float)
    if arr.size < cfg.window:
        return Detection(False, 0.0, 0.0, cfg.p_fa)
    stats = _window_statistic(arr, cfg.window) / cfg.noise_variance
    threshold = chi2_quantile(cfg.window, 1.0 - cfg.p_fa)
    peak = float(stats.max()) if stats.size else 0.0
    return Detection(bool(peak > threshold), peak, threshold, cfg.p_fa)


def simulate_signal(
    duration_s: float,
    fs: int,
    target_snr_db: float,
    seed: int,
    *,
    tone_hz: float = 400.0,
    noise_variance: float = 1.0,
) -> np.ndarray:
    """Synthesise a deterministic received waveform for detector tests.

    ``duration_s`` seconds of ambient Gaussian noise (variance
    ``noise_variance``, seeded) plus, optionally, a narrow-band tonal at
    ``tone_hz`` whose power raises the per-window SNR toward ``target_snr_db``.
    """
    n = int(round(duration_s * fs))
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, math.sqrt(noise_variance), n)
    if target_snr_db <= 0.0:
        return noise
    t = np.arange(n) / fs
    amplitude = math.sqrt(noise_variance * 10.0 ** (target_snr_db / 10.0)) * math.sqrt(2.0)
    return noise + amplitude * np.sin(2.0 * math.pi * tone_hz * t)


@dataclass(frozen=True)
class TrackSimulation:
    """A deterministic bearing-only target scenario.

    ``truth`` (Nx2) is the target's earth-frame trajectory; ``ownship`` (Nx2)
    is the maneuvering observer's trajectory; ``bearings_rad`` are the noisy
    relative bearings from the ownship to the target at ``time_s``.
    """

    time_s: np.ndarray
    truth: np.ndarray
    ownship: np.ndarray
    bearings_rad: np.ndarray
    bearing_noise_deg: float
    speed_m_s: float
    course_deg: float

    @property
    def num_measurements(self) -> int:
        """Number of bearing samples in the scenario."""
        return int(self.bearings_rad.size)


def simulate_target_track(
    duration_s: float,
    dt: float,
    target_speed_m_s: float,
    target_course_deg: float,
    bearing_noise_deg: float,
    seed: int,
    *,
    ownship_speed_m_s: float = 20.0,
    maneuver_fraction: float = 0.5,
    range0_m: float = 4000.0,
    bearing0_deg: float = 26.565,
) -> TrackSimulation:
    """Simulate a constant-velocity target observed by a maneuvering ownship.

    The ownship starts at the origin and runs a deterministic dogleg: a first
    leg heading due east, then a 90-degree turn to due north for the rest of
    the run. The target moves at constant velocity from ``range0_m`` metres
    away on bearing ``bearing0_deg``, with course ``target_course_deg``.

    Relative bearings (``atan2(target - ownship)``) are corrupted by
    zero-mean Gaussian noise with standard deviation ``bearing_noise_deg``,
    seeded deterministically. The observer *must* maneuver for the target's
    range and speed to be observable; without it ``estimate_tma`` cannot
    separate scale from shape.
    """
    steps = max(2, int(round(duration_s / dt)))
    time = np.arange(steps, dtype=float) * dt
    turn = max(1, int(steps * maneuver_fraction)) if 0.0 < maneuver_fraction < 1.0 else steps

    ownship = np.empty((steps, 2), dtype=float)
    for i in range(steps):
        if i < turn:
            ownship[i] = (ownship_speed_m_s * time[i], 0.0)
        else:
            ownship[i] = (
                ownship_speed_m_s * time[turn - 1],
                ownship_speed_m_s * (time[i] - time[turn - 1]),
            )

    rad = math.radians(target_course_deg)
    vx = target_speed_m_s * math.cos(rad)
    vy = target_speed_m_s * math.sin(rad)
    b0 = math.radians(bearing0_deg)
    p0x = range0_m * math.cos(b0)
    p0y = range0_m * math.sin(b0)
    truth = np.empty((steps, 2), dtype=float)
    truth[:, 0] = p0x + vx * time
    truth[:, 1] = p0y + vy * time

    true_bearing = np.arctan2(truth[:, 1] - ownship[:, 1], truth[:, 0] - ownship[:, 0])
    rng = np.random.default_rng(seed)
    noise_rad = math.radians(bearing_noise_deg)
    return TrackSimulation(
        time_s=time,
        truth=truth,
        ownship=ownship,
        bearings_rad=true_bearing + rng.normal(0.0, noise_rad, steps),
        bearing_noise_deg=bearing_noise_deg,
        speed_m_s=target_speed_m_s,
        course_deg=target_course_deg,
    )


@dataclass(frozen=True)
class TrackSolution:
    """A target-motion-analysis solution: position and velocity in the frame."""

    position0: np.ndarray
    velocity: np.ndarray
    residual_rms_rad: float
    num_measurements: int

    def position_at(self, t: float) -> np.ndarray:
        """Cartesian position of the target at time ``t`` (seconds)."""
        return self.position0 + self.velocity * t

    @property
    def as_dict(self) -> dict[str, object]:
        """Plain-dict summary for provenance records."""
        return {
            "position0_m": [float(self.position0[0]), float(self.position0[1])],
            "velocity_m_s": [float(self.velocity[0]), float(self.velocity[1])],
            "residual_rms_rad": self.residual_rms_rad,
            "num_measurements": self.num_measurements,
        }


_COARSE_RANGE_MIN = 3000.0
_COARSE_RANGE_MAX = 7000.0
_COARSE_RANGE_STEP = 500.0
_COARSE_COURSES = range(0, 360, 15)
_COARSE_SPEEDS = range(5, 40, 5)
_GAUSS_NEWTON_ITERS = 200


def _bearings_along(
    p0: np.ndarray, vel: np.ndarray, time: np.ndarray, ownship: np.ndarray
) -> np.ndarray:
    """Relative bearings (rad) of a candidate CV target at ``time`` grid."""
    rx = p0[0] + vel[0] * time - ownship[:, 0]
    ry = p0[1] + vel[1] * time - ownship[:, 1]
    return np.arctan2(ry, rx)  # type: ignore[no-any-return]


def _wrap_radians(angles: np.ndarray) -> np.ndarray:
    return angles - 2.0 * np.pi * np.round(angles / (2.0 * np.pi))


def estimate_tma(
    time: np.ndarray,
    bearings: np.ndarray,
    ownship: np.ndarray,
) -> TrackSolution:
    """Batch least-squares target motion analysis from a maneuvering ownship.

    Solves for the constant-velocity target ``[px, py, vx, vy]`` that
    minimises the sum of squared bearing residuals
    ``sum_i (bearing_i - atan2(target(t_i) - ownship_i))**2``. A coarse grid
    search over range/course/speed provides a robust initialisation, then
    Gauss–Newton refines it. Fully deterministic.

    Args:
        time: ``(N,)`` sample times (seconds).
        bearings: ``(N,)`` measured relative bearings (rad).
        ownship: ``(N, 2)`` observer positions (metres).

    Returns:
        A :class:`TrackSolution` with the recovered initial position and
        constant velocity.
    """
    time = np.asarray(time, dtype=float)
    bearings = np.asarray(bearings, dtype=float)
    ownship = np.asarray(ownship, dtype=float)
    if time.ndim != 1 or bearings.ndim != 1 or ownship.shape != (time.size, 2):
        raise ValueError("time, bearings and ownship must be aligned (N,), (N,), (N, 2)")
    if time.size < 4:
        raise ValueError("at least 4 bearing measurements are required")

    best_f = float("inf")
    best: np.ndarray | None = None
    for rng0 in np.arange(_COARSE_RANGE_MIN, _COARSE_RANGE_MAX, _COARSE_RANGE_STEP):
        for course in _COARSE_COURSES:
            vx = math.cos(math.radians(course))
            vy = math.sin(math.radians(course))
            for speed in _COARSE_SPEEDS:
                p0 = np.array(
                    [rng0 * math.cos(bearings[0]), rng0 * math.sin(bearings[0])], dtype=float
                )
                vel = np.array([speed * vx, speed * vy], dtype=float)
                res = _bearings_along(p0, vel, time, ownship) - bearings
                f = float(np.sum(res * res))
                if f < best_f:
                    best_f = f
                    best = np.concatenate([p0, vel])

    assert best is not None  # the coarse grid is guaranteed non-empty
    p = best.copy()
    for _ in range(_GAUSS_NEWTON_ITERS):
        rx = p[0] + p[2] * time - ownship[:, 0]
        ry = p[1] + p[3] * time - ownship[:, 1]
        r2 = rx * rx + ry * ry + 1e-9
        ang = np.arctan2(ry, rx)
        dpx = -ry / r2
        dpy = rx / r2
        jac = np.stack([dpx, dpy, dpx * time, dpy * time], axis=1)
        resid = _wrap_radians(ang - bearings)
        hessian = jac.T @ jac + 1e-8 * np.eye(4)
        step = np.linalg.solve(hessian, jac.T @ resid)
        p = p - step

    final_res = _wrap_radians(_bearings_along(p[:2], p[2:], time, ownship) - bearings)
    rms = float(np.sqrt(np.mean(final_res * final_res)))
    return TrackSolution(
        position0=p[:2].copy(),
        velocity=p[2:].copy(),
        residual_rms_rad=rms,
        num_measurements=int(time.size),
    )


class PassiveBearingTracker:
    """Extended Kalman Filter for online bearing-only target tracking.

    State ``x = [pos_x, pos_y, vel_x, vel_y]`` with a constant-velocity
    transition model. The measurement is the relative bearing to the target
    from a (possibly moving) ownship, ``h(x) = atan2(y - oy, x - ox)``; the
    ownship position is supplied per measurement. As with any bearing-only
    estimator, the ownship must maneuver for range and speed to be
    observable; initialise from :func:`estimate_tma` for reliable convergence.
    """

    def __init__(
        self,
        initial_state: Sequence[float],
        initial_cov: Sequence[Sequence[float]],
        *,
        process_noise: float = 1.0,
        measurement_noise_rad: float = 0.01,
    ) -> None:
        self.x = _validate_initial_state(initial_state)
        self.P = _validate_initial_cov(initial_cov)
        if process_noise < 0.0:
            raise ValueError("process_noise must be >= 0")
        if measurement_noise_rad <= 0.0:
            raise ValueError("measurement_noise_rad must be > 0")
        self._q = float(process_noise)
        self._r = float(measurement_noise_rad)

    def predict(self, dt: float) -> None:
        """Advance the estimate one Euler step of size ``dt`` (seconds)."""
        f = np.eye(4)
        f[0, 2] = dt
        f[1, 3] = dt
        self.x = f @ self.x
        q = np.zeros((4, 4))
        dt2 = dt * dt
        q[0, 0] = q[1, 1] = dt * self._q
        q[0, 2] = q[1, 3] = 0.5 * dt2 * self._q
        q[2, 0] = q[3, 1] = 0.5 * dt2 * self._q
        q[2, 2] = q[3, 3] = dt * self._q
        self.P = f @ self.P @ f.T + q

    def update(self, bearing_rad: float, ownship: Sequence[float] = (0.0, 0.0)) -> None:
        """Fuse a noisy relative bearing (ownship at ``ownship``) into the estimate."""
        ox, oy = float(ownship[0]), float(ownship[1])
        dx = float(self.x[0, 0]) - ox
        dy = float(self.x[1, 0]) - oy
        r2 = dx * dx + dy * dy
        if r2 == 0.0:
            raise ValueError("tracker state coincides with ownship; bearing undefined")
        predicted = math.atan2(dy, dx)
        h = np.array([-dy / r2, dx / r2, 0.0, 0.0]).reshape(1, 4)
        s = float((h @ self.P @ h.T + self._r).item())
        k = self.P @ h.T / s
        innovation = bearing_rad - predicted
        innovation -= 2.0 * math.pi * round(innovation / (2.0 * math.pi))
        self.x = self.x + k * innovation
        self.P = self.P - k @ h @ self.P

    @property
    def position(self) -> np.ndarray:
        """Current (x, y) position estimate."""
        return self.x[:2, 0].copy()

    @property
    def velocity(self) -> np.ndarray:
        """Current (vx, vy) velocity estimate."""
        return self.x[2:, 0].copy()

    def run(self, simulation: TrackSimulation) -> np.ndarray:
        """Run the filter over a scenario, returning the position history.

        The filter is initialised at ``time[0]``; each later sample predicts
        over the elapsed ``dt`` then fuses that sample's bearing from the
        corresponding ownship position. Returns an ``(N, 2)`` array aligned
        with ``simulation.truth``.
        """
        n = simulation.num_measurements
        if n < 1:
            return np.empty((0, 2))
        estimates = np.empty((n, 2))
        times = simulation.time_s
        for i in range(n):
            if i > 0:
                self.predict(float(times[i] - times[i - 1]))
            self.update(float(simulation.bearings_rad[i]), simulation.ownship[i])
            estimates[i] = self.position
        return estimates


def _validate_initial_state(initial_state: Sequence[float]) -> np.ndarray:
    if len(initial_state) != 4:
        raise ValueError("initial_state must have 4 components [x, y, vx, vy]")
    return np.asarray(initial_state, dtype=float).reshape(4, 1)


def _validate_initial_cov(initial_cov: Sequence[Sequence[float]]) -> np.ndarray:
    cov = np.asarray(initial_cov, dtype=float).reshape(4, 4)
    if not np.all(np.linalg.eigvalsh(cov) >= 0.0):
        raise ValueError("initial_cov must be positive semi-definite")
    return cov


def tracking_rms_error(estimates: np.ndarray, truth: np.ndarray, warmup: int = 0) -> float:
    """Root-mean-square position error between estimates and truth.

    ``warmup`` samples at the start are excluded so the tail reflects
    steady-state accuracy.
    """
    if estimates.shape != truth.shape or estimates.ndim != 2 or estimates.shape[1] != 2:
        raise ValueError("estimates and truth must be aligned Nx2 arrays")
    if estimates.shape[0] <= warmup:
        raise ValueError("warmup must be fewer than the number of samples")
    diff = estimates[warmup:] - truth[warmup:]
    return float(np.sqrt(np.mean(np.einsum("ij,ij->i", diff, diff))))
