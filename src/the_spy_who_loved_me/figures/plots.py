"""LIPARUS figure generation — deterministic publication-quality plots.

Each ``plot_*`` function renders one concept (passive tracking, Liparus
capture feasibility, conversion readiness) to a PNG under ``output/figures/``
and returns the absolute path. Rendering is deterministic: fixed data, no
wall-clock stamps, vector-backed raster output at 300 DPI. The figures are
regenerable artifacts, so ``output/`` is git-ignored.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from ..acoustics import SonarBudget, detection_range_m  # noqa: E402
from ..beamforming import array_snapshot, estimate_bearing_deg  # noqa: E402
from ..sub_tracking import TrackSimulation, TrackSolution  # noqa: E402
from ..tanker_capture import BayConfig, SubmarineSpec, clearance_metrics  # noqa: E402
from ..vehicle_forensics import (  # noqa: E402
    VehicleSpec,
    assess_conversion,
)

__all__ = [
    "PROJECT_ROOT",
    "build_all_figures",
    "plot_bearing_track",
    "plot_capture_feasibility",
    "plot_conversion_readiness",
    "plot_beamforming_response",
    "plot_sonar_detection_range",
]

#: The project root (three levels up from ``figures/plots.py``).
PROJECT_ROOT = Path(__file__).resolve().parents[3]

#: Where figures land.
FIGURES_DIR = PROJECT_ROOT / "output" / "figures"


def _ensure_figures_dir() -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIGURES_DIR


def plot_bearing_track(
    track: TrackSimulation, solution: TrackSolution, filename: str = "bearing_track.png"
) -> Path:
    """Plot the true target track vs the TMA solution, with the ownship path.

    ``solution`` is a :class:`~..sub_tracking.TrackSolution` recovered by
    :func:`~..sub_tracking.estimate_tma`; its history is extrapolated over the
    scenario time. The maneuvering ownship path is drawn, and a faint fan of
    the measured bearing rays to the contact is overlaid.
    """
    out = _ensure_figures_dir() / filename
    fig, ax = plt.subplots(figsize=(7, 6))
    for idx in range(0, track.num_measurements, max(1, track.num_measurements // 10)):
        bearing = float(track.bearings_rad[idx])
        direction = np.array([np.cos(bearing), np.sin(bearing)])
        length = 0.45 * float(np.linalg.norm(track.truth[0] - track.ownship[0]))
        origin = track.ownship[idx]
        ax.plot(
            [origin[0], origin[0] + length * direction[0]],
            [origin[1], origin[1] + length * direction[1]],
            color="grey",
            alpha=0.22,
            lw=0.6,
        )
    times = track.time_s
    est_hist = np.stack([solution.position_at(float(t)) for t in times], axis=0)
    ax.plot(track.truth[:, 0], track.truth[:, 1], color="tab:blue", lw=2, label="true track")
    ax.plot(est_hist[:, 0], est_hist[:, 1], color="tab:red", lw=2, ls="--", label="TMA estimate")
    ax.plot(
        track.ownship[:, 0],
        track.ownship[:, 1],
        color="tab:green",
        lw=2,
        label="ownship (maneuvering)",
    )
    ax.plot(track.ownship[0, 0], track.ownship[0, 1], marker="*", color="black", ms=14)
    ax.set_xlabel("East (m)")
    ax.set_ylabel("North (m)")
    ax.set_title("Passive bearing-only tracking — TMA")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


def plot_capture_feasibility(
    sizes: Sequence[tuple[float, float, float]],
    bay: BayConfig,
    filename: str = "capture_feasibility.png",
) -> Path:
    """Bar chart of per-axis clearance margins for several submarine sizes.

    ``sizes`` is a sequence of ``(length_m, beam_m, depth_m)`` triples; each
    is measured against ``bay`` and its minimum margin (colour-coded by
    fit/tight/denied) is plotted.
    """
    out = _ensure_figures_dir() / filename
    margins = []
    colours = []
    labels = []
    for length, beam, depth in sizes:
        sub = SubmarineSpec(length, beam, depth)
        c = clearance_metrics(sub, bay)
        margins.append(min(c.beam_clearance_m, c.depth_clearance_m, c.length_clearance_m))
        labels.append(f"{length:.0f}m\n({beam:.1f}x{depth:.1f})")
        if not c.fits:
            colours.append("tab:red")
        elif margins[-1] < bay.clearance_m:
            colours.append("tab:orange")
        else:
            colours.append("tab:green")
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(margins))
    ax.bar(x, margins, color=colours)
    ax.axhline(
        bay.clearance_m, color="k", ls="--", lw=1, label=f"required margin {bay.clearance_m:.1f} m"
    )
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("submarine length / beam x depth (m)")
    ax.set_ylabel("minimum clearance margin (m)")
    ax.set_title("Liparus dock-mouth feasibility by submarine size")
    ax.legend(loc="best")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


def plot_conversion_readiness(
    vehicles: Sequence[VehicleSpec], filename: str = "conversion_readiness.png"
) -> Path:
    """Horizontal stacked bar of materialised vs missing requirements per vehicle.

    Each vehicle's systems are traced against
    :data:`~..vehicle_forensics.SUBMERSIBLE_REQUIREMENTS`; satisfied systems
    are rendered green, missing non-critical amber, missing critical red.
    """
    out = _ensure_figures_dir() / filename
    names = [v.name for v in vehicles]
    satisfied = []
    missing_opt = []
    missing_crit = []
    for v in vehicles:
        a = assess_conversion(v)
        satisfied.append(len(a.satisfied))
        missing_opt.append(sum(1 for r in a.missing if not r.critical))
        missing_crit.append(len(a.missing_critical))
    y = np.arange(len(vehicles))
    fig, ax = plt.subplots(figsize=(8, max(3.0, 0.6 * len(vehicles))))
    ax.barh(y, satisfied, color="tab:green", label="satisfied")
    ax.barh(y, missing_opt, left=satisfied, color="tab:olive", label="missing (optional)")
    lefts = [s + o for s, o in zip(satisfied, missing_opt, strict=True)]
    ax.barh(y, missing_crit, left=lefts, color="tab:red", label="missing (critical)")
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel("requirements")
    ax.set_title("Submersible conversion readiness by requirement")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


def plot_beamforming_response(
    snapshot: np.ndarray,
    d_over_lambda: float,
    true_bearing_deg: float,
    filename: str = "beamforming_response.png",
) -> Path:
    """Plot the ULA beamformer power response vs bearing.

    ``snapshot`` is a complex array snapshot; the conventional beamformer is
    scanned across ``[-90, 90]`` degrees and the normalised power is plotted,
    together with the true bearing and the scan-peak estimate.
    """
    out = _ensure_figures_dir() / filename
    result = estimate_bearing_deg(snapshot, d_over_lambda)
    powers = result.powers
    norm = powers / float(powers.max()) if float(powers.max()) > 0.0 else powers
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(result.scan, norm, color="tab:blue", lw=2)
    ax.axvline(
        true_bearing_deg,
        color="tab:green",
        ls="--",
        lw=1.5,
        label=f"true {true_bearing_deg:.0f} deg",
    )
    ax.axvline(
        result.bearing_deg,
        color="tab:red",
        ls=":",
        lw=2,
        label=f"estimate {result.bearing_deg:.1f} deg",
    )
    ax.set_xlabel("bearing from broadside (deg)")
    ax.set_ylabel("normalised beam power")
    ax.set_title(f"ULA beamformer response — {result.n_elements} elements")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


def plot_sonar_detection_range(
    budget: SonarBudget,
    freq_hz: float,
    sl_range: tuple[float, float] = (120.0, 200.0),
    filename: str = "sonar_detection_range.png",
) -> Path:
    """Plot passive-sonar detection range as a function of source level.

    Sweeps the canonical budget's source level over ``sl_range`` and solves
    the detection-range equation for each, showing how much range a stronger
    contact buys.
    """
    out = _ensure_figures_dir() / filename
    sl_lo, sl_hi = sl_range
    sls = np.linspace(sl_lo, sl_hi, 41)
    ranges = np.array(
        [
            detection_range_m(
                SonarBudget(
                    sl_db=float(sl), nl_db=budget.nl_db, di_db=budget.di_db, dt_db=budget.dt_db
                ),
                freq_hz,
            ).range_m
            for sl in sls
        ],
        dtype=float,
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sls, ranges / 1000.0, color="tab:blue", lw=2)
    ax.set_xlabel("source level (dB re 1 uPa)")
    ax.set_ylabel("detection range (km)")
    ax.set_title(f"Passive sonar detection range vs source level ({freq_hz:.0f} Hz)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


def build_all_figures() -> dict[str, Path]:
    """Render the five concept figures and return a path map.

    The tracking, beamforming and sonar figures use canonical seeded
    scenarios; the capture and readiness figures use representative data.
    All outputs are deterministic.
    """
    from ..sub_tracking import estimate_tma, simulate_target_track

    track = simulate_target_track(
        duration_s=600.0,
        dt=10.0,
        target_speed_m_s=25.0,
        target_course_deg=90.0,
        bearing_noise_deg=0.5,
        seed=11,
    )
    solution = estimate_tma(track.time_s, track.bearings_rad, track.ownship)
    beam_snapshot = array_snapshot(0.5235987755982988, 0.5, 8, 1.0, 0.1, 11)
    return {
        "bearing_track": plot_bearing_track(track, solution),
        "beamforming_response": plot_beamforming_response(beam_snapshot, 0.5, 30.0),
        "sonar_detection_range": plot_sonar_detection_range(
            SonarBudget(sl_db=160.0, nl_db=70.0, di_db=20.0, dt_db=10.0), 400.0
        ),
        "capture_feasibility": plot_capture_feasibility(
            [(64.0, 6.8, 6.0), (80.0, 10.0, 9.0), (95.0, 12.5, 11.0), (120.0, 16.0, 14.0)],
            BayConfig(
                mouth_width_m=16.0, mouth_height_m=14.0, hold_length_m=140.0, clearance_m=1.5
            ),
        ),
        "conversion_readiness": plot_conversion_readiness(
            [
                VehicleSpec(
                    "stock road car", 1000.0, 1.1, {}, plausible_road="mass-production coupe"
                ),
                VehicleSpec(
                    "amphibious rebuild",
                    1350.0,
                    1.4,
                    {"watertight_seals": True, "underwater_thrust": True},
                ),
                VehicleSpec(
                    "Lotus-Esprit-grade submersible",
                    1800.0,
                    2.0,
                    {
                        "pressure_hull": True,
                        "watertight_seals": True,
                        "ballast_system": True,
                        "air_supply": True,
                    },
                ),
            ]
        ),
    }


if __name__ == "__main__":
    built = build_all_figures()
    for name, path in built.items():
        print(f"{name}: {path}")
