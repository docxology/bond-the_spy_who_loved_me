"""LIPARUS — the BOND-API mission provider for The Spy Who Loved Me (1977).

This is the thin adapter between the pure domain core
(:mod:`src.the_spy_who_loved_me.sub_tracking`, ``tanker_capture``,
``vehicle_forensics``) and the FROZEN ``bond_api`` mission protocol. It
implements the full lifecycle — brief → recon → plan → execute → debrief —
by running the real, deterministic domain algorithms, and registers the
concept gadgets on a :class:`bond_api.registry.GadgetRegistry` at import
time so the fleet coordinator can discover them.

Per the protocol contract, this module exposes ``MissionProvider`` at module
top level under a stable name; discovery imports ``<slug>.mission`` and
instantiates it.
"""

from __future__ import annotations

import numpy as np
from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry

from .sub_tracking import detect_contract, estimate_tma, simulate_signal, simulate_target_track
from .tanker_capture import (
    BayConfig,
    SubmarineSpec,
    classify_clearance,
    simulate_capture,
    stowage_capacity,
)
from .vehicle_forensics import VehicleSpec, assess_conversion

__all__ = ["GADGETS", "MissionProvider"]

#: Package identity mirroring ``manuscript/config.yaml``.
PACKAGE_VERSION = "0.1.0"
SEED = 11
CODENAME = "LIPARUS"
FILM = "the_spy_who_loved_me"

#: Canonical scenario parameters — deterministic, shared with manuscript metrics.
_BAY = BayConfig(mouth_width_m=16.0, mouth_height_m=14.0, hold_length_m=140.0, clearance_m=1.5)
_SUB = SubmarineSpec(length_m=72.0, beam_m=8.0, depth_m=7.0)
_VEHICLE = VehicleSpec(
    "Lotus-Esprit-grade submersible",
    dry_mass_kg=1800.0,
    displacement_m3=2.0,
    systems={
        "pressure_hull": True,
        "watertight_seals": True,
        "ballast_system": True,
        "air_supply": True,
        "underwater_thrust": True,
        "navigation_sonar": True,
    },
)


def _run_domain_workload() -> dict[str, object]:
    """Execute the four concept algorithms and return their real, deterministic results.

    Detection uses a synthesised high-SNR contact; tracking runs the canonical
    EKF scenario; capture simulates the Liparus swallow; forensics assesses
    the Esprit-grade conversion.
    """
    # 1. Passive acoustic detection — high-SNR tonal in seeded noise.
    signal = simulate_signal(duration_s=2.0, fs=8000, target_snr_db=12.0, seed=SEED)
    detection = detect_contract(signal)

    # 2. Bearing-only tracking — canonical scenario, TMA solution error vs truth.
    track = simulate_target_track(
        duration_s=600.0,
        dt=10.0,
        target_speed_m_s=25.0,
        target_course_deg=90.0,
        bearing_noise_deg=0.5,
        seed=SEED,
    )
    sol = estimate_tma(track.time_s, track.bearings_rad, track.ownship)
    # Position error of the recovered initial position against truth at t=0.
    pos_err = float(np.linalg.norm(sol.position0 - track.truth[0]))
    vel_err = float(
        np.linalg.norm(
            sol.velocity
            - (
                track.speed_m_s
                * np.asarray(
                    [np.cos(np.radians(track.course_deg)), np.sin(np.radians(track.course_deg))]
                )
            )
        )
    )

    # 3. Liparus capture.
    capture = simulate_capture(_SUB, _BAY)

    # 4. Vehicle forensics.
    forensics = assess_conversion(_VEHICLE)

    return {
        "detected": detection.detected,
        "detection_margin_db": round(detection.margin_db, 2),
        "track_pos_err_m": round(pos_err, 1),
        "track_vel_err_m_s": round(vel_err, 1),
        "track_num_bearings": track.num_measurements,
        "track_residual_rms_rad": round(sol.residual_rms_rad, 4),
        "capture_clearance": classify_clearance(_SUB, _BAY),
        "capture_success": capture.success,
        "capture_time_s": round(capture.total_time_s, 1),
        "capture_stowage": stowage_capacity(_SUB, _BAY),
        "forensics_class": forensics.classification.value,
        "forensics_score": round(forensics.score, 2),
        "forensics_missing_critical": len(forensics.missing_critical),
    }


class MissionProvider:  # noqa: N801 — class name fixed by the discovery contract
    """Deterministic BOND-API mission provider for LIPARUS.

    ``execute`` runs the real domain workload (detection, tracking, capture,
    forensics) with a fixed seed and no wall-clock dependence, and returns
    the measured results with full provenance.
    """

    film = FILM

    def brief(self) -> MissionBrief:
        """Declare the LIPARUS mission: two objectives over the concept core."""
        return MissionBrief(
            film=self.film,
            codename=CODENAME,
            objectives=(
                "detect and track a passive-acoustic contact",
                "simulate a Liparus-Class tanker capture and verify vehicle conversion",
            ),
            assets=(
                Asset(
                    kind="module",
                    name="sub_tracking",
                    payload={"algorithms": ["energy_detector", "ekf_bearing_tracking"]},
                ),
                Asset(
                    kind="module", name="tanker_capture", payload={"scenario": "Liparus swallow"}
                ),
                Asset(
                    kind="module",
                    name="vehicle_forensics",
                    payload={"subject": "Lotus Esprit conversion"},
                ),
            ),
            constraints=(
                Constraint(
                    kind="determinism", detail="fixed seed, no random draws, no external calls"
                ),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the goals, available assets, and determinism constraint."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(label="asset_count", detail="three concept modules available"),
                Finding(
                    label="detection_model",
                    detail="Neyman-Pearson energy detector with Wilson-Hilferty threshold",
                ),
                Finding(
                    label="tracking_model",
                    detail="extended Kalman filter, constant-velocity target",
                ),
                Finding(label="constraints", detail="deterministic execution required"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the five deterministic steps across the four stages."""
        return MissionPlan(
            steps=(
                Step(
                    name="detect",
                    action="run_detector",
                    params={"snr_db": 12, "objectives": len(brief.objectives)},
                ),
                Step(
                    name="track", action="run_ekf", params={"scenario": "canonical", "seed": SEED}
                ),
                Step(name="capture", action="simulate_liparus", params={"submarine": "canonical"}),
                Step(
                    name="forensics", action="assess_conversion", params={"vehicle": "esprit_grade"}
                ),
                Step(name="verify", action="check_outcome", params={"success": True}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the concept workload and return measured results with provenance."""
        results = _run_domain_workload()
        return MissionOutcome(
            success=bool(results["detected"] and results["capture_success"]),
            results=results,
            provenance=Provenance(
                package_version=PACKAGE_VERSION,
                seed=SEED,
                input_hash="liparus-mission-input",
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarise the mission and record LIPARUS' standing lessons."""
        results = outcome.results
        return Debrief(
            outcome=outcome,
            lessons=(
                f"passive contact detected (margin {results['detection_margin_db']} dB); TMA position error {results['track_pos_err_m']} m over {results['track_num_bearings']} bearings",
                f"Liparus capture {results['capture_clearance']}; vehicle conversion class {results['forensics_class']}",
                "deterministic provenance is mandatory for every outcome",
            ),
        )


#: Gadgets this film contributes to the fleet registry (name → domain callable).
GADGETS = GadgetRegistry()
GADGETS.register(
    FILM,
    {
        "detect_contract": detect_contract,
        "simulate_target_track": simulate_target_track,
        "simulate_capture": simulate_capture,
        "assess_conversion": assess_conversion,
    },
)
