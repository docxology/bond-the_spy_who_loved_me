"""LIPARUS — the BOND-API mission provider for The Spy Who Loved Me (1977).

This is the thin adapter between the pure domain core
(:mod:`src.the_spy_who_loved_me.{sub_tracking,tanker_capture,
vehicle_forensics,acoustics,beamforming,hull_forensics}`) and the FROZEN
``bond_api`` mission protocol. It implements the full lifecycle — brief →
recon → plan → execute → debrief — by running the real, deterministic
domain algorithms via the single canonical scenario
(:func:`the_spy_who_loved_me.scenario.run_canonical`), and registers the
concept gadgets on a :class:`bond_api.registry.GadgetRegistry` at import
time so the fleet coordinator can discover them.

Per the protocol contract, this module exposes ``MissionProvider`` at module
top level under a stable name; discovery imports ``<slug>.mission`` and
instantiates it. The public shape (class, methods, module-level ``GADGETS``)
is frozen and must not change.
"""

from __future__ import annotations

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

from .acoustics import SonarBudget, detection_range_m
from .beamforming import array_snapshot, estimate_bearing_deg
from .hull_forensics import collapse_depth_m, design_safety_factor
from .scenario import SEED, canonical_input_hash, run_canonical
from .sub_tracking import detect_contract, estimate_tma, simulate_signal, simulate_target_track
from .tanker_capture import simulate_capture
from .vehicle_forensics import assess_conversion

__all__ = ["GADGETS", "MissionProvider"]

#: Package identity mirroring ``manuscript/config.yaml``.
PACKAGE_VERSION = "0.1.0"
CODENAME = "LIPARUS"
FILM = "the_spy_who_loved_me"


class MissionProvider:  # noqa: N801 — class name fixed by the discovery contract
    """Deterministic BOND-API mission provider for LIPARUS.

    ``execute`` runs the six-concept canonical workload with a fixed seed and
    no wall-clock dependence, and returns the measured results with full
    provenance.
    """

    film = FILM

    def brief(self) -> MissionBrief:
        """Declare the LIPARUS mission: two objectives over the concept core."""
        return MissionBrief(
            film=self.film,
            codename=CODENAME,
            objectives=(
                "detect, localise and track a passive-acoustic contact",
                "simulate a Liparus-Class tanker capture, verify submersible conversion and hull viability",
            ),
            assets=(
                Asset(
                    kind="module",
                    name="sub_tracking",
                    payload={"algorithms": ["energy_detector", "tma", "ekf"]},
                ),
                Asset(
                    kind="module", name="tanker_capture", payload={"scenario": "Liparus swallow"}
                ),
                Asset(
                    kind="module",
                    name="vehicle_forensics",
                    payload={"subject": "Lotus Esprit conversion"},
                ),
                Asset(kind="module", name="acoustics", payload={"model": "passive sonar equation"}),
                Asset(kind="module", name="beamforming", payload={"array": "uniform linear"}),
                Asset(kind="module", name="hull_forensics", payload={"subject": "pressure hull"}),
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
                Finding(label="asset_count", detail="six concept modules available"),
                Finding(
                    label="detection_model",
                    detail="Neyman-Pearson energy detector; passive sonar equation; Thorp absorption",
                ),
                Finding(
                    label="tracking_model",
                    detail="bearing-only TMA over a maneuvering ownship; EKF; ULA beamformer",
                ),
                Finding(label="hull_model", detail="hoop stress, elastic buckling, ballast volume"),
                Finding(label="constraints", detail="deterministic execution required"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the deterministic steps across the six concept stages."""
        return MissionPlan(
            steps=(
                Step(
                    name="detect",
                    action="run_detector",
                    params={"snr_db": 12, "objectives": len(brief.objectives)},
                ),
                Step(
                    name="track", action="run_tma", params={"scenario": "canonical", "seed": SEED}
                ),
                Step(name="sonar", action="solve_detection_range", params={"freq_hz": 400}),
                Step(name="beamform", action="estimate_bearing", params={"array": "ula8"}),
                Step(name="capture", action="simulate_liparus", params={"submarine": "canonical"}),
                Step(
                    name="forensics", action="assess_conversion", params={"vehicle": "esprit_grade"}
                ),
                Step(name="hull", action="check_collapse_depth", params={"operating_depth_m": 40}),
                Step(name="verify", action="check_outcome", params={"success": True}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the canonical concept workload and return measured results.

        ``input_hash`` is a SHA-256 over the canonical scenario's actual
        parameter set (:func:`the_spy_who_loved_me.scenario.canonical_input_hash`),
        so editing any canonical input changes it. It was a fixed string
        literal until this was fixed, which meant it identified the package
        and not the inputs.
        """
        results = run_canonical()
        return MissionOutcome(
            success=bool(
                results["detected"] and results["capture_success"] and results["hull_feasible"]
            ),
            results=results,
            provenance=Provenance(
                package_version=PACKAGE_VERSION,
                seed=SEED,
                input_hash=canonical_input_hash(),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarise the mission and record LIPARUS' standing lessons."""
        r = outcome.results
        return Debrief(
            outcome=outcome,
            lessons=(
                f"passive contact detected (margin {r['detection_margin_db']} dB); "
                f"TMA position error {r['track_pos_err_m']} m; beamformer bearing error {r['beam_bearing_err_deg']} deg",
                f"passive sonar detection range {r['aco_detection_range_m']:.0f} m at {r['aco_sound_speed_m_s']:.0f} m/s; "
                f"hull collapse depth {r['hull_collapse_depth_m']} m (safety factor {r['hull_safety_factor']})",
                f"Liparus capture {r['capture_clearance']}; vehicle conversion class {r['forensics_class']}; "
                f"required ballast {r['ballast_volume_l']} L",
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
        "estimate_tma": estimate_tma,
        "simulate_signal": simulate_signal,
        "simulate_capture": simulate_capture,
        "assess_conversion": assess_conversion,
        "detection_range_m": detection_range_m,
        "array_snapshot": array_snapshot,
        "estimate_bearing_deg": estimate_bearing_deg,
        "collapse_depth_m": collapse_depth_m,
        "design_safety_factor": design_safety_factor,
        "SonarBudget": SonarBudget,
    },
)
