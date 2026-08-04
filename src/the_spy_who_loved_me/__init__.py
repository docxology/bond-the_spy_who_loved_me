"""LIPARUS — The Spy Who Loved Me (1977) special-agent mission software.

PROJECT BOND film package. Presents three deterministic, infrastructure-free
domain cores plus the manuscript-variable hydration and the BOND-API mission
adapter:

* :mod:`.sub_tracking` — passive acoustic detection and bearing-only tracking
* :mod:`.tanker_capture` — Liparus-class tanker swallowing-submarine simulation
* :mod:`.vehicle_forensics` — Lotus-Esprit-grade submersible conversion forensics
* :mod:`.manuscript_variables` — ``{{TOKEN}}`` hydration from manuscript config
* :mod:`.mission` — the frozen ``bond_api.MissionProvider`` adapter
"""

from __future__ import annotations

from .sub_tracking import (
    Detection,
    DetectionConfig,
    PassiveBearingTracker,
    TrackSimulation,
    TrackSolution,
    chi2_quantile,
    detect_contract,
    estimate_tma,
    simulate_signal,
    simulate_target_track,
    tracking_rms_error,
)
from .tanker_capture import (
    BayConfig,
    CapturePhase,
    CaptureRun,
    Clearance,
    PhaseRecord,
    SubmarineSpec,
    classify_clearance,
    clearance_metrics,
    simulate_capture,
    stowage_capacity,
)
from .vehicle_forensics import (
    SUBMERSIBLE_REQUIREMENTS,
    BuoyancyClass,
    ConversionAssessment,
    ConversionClass,
    Requirement,
    VehicleSpec,
    assess_conversion,
    buoyancy_status,
    classify_conversion,
    recommend_upgrades,
)

__all__ = [
    "BayConfig",
    "BuoyancyClass",
    "CapturePhase",
    "CaptureRun",
    "Clearance",
    "ConversionAssessment",
    "ConversionClass",
    "Detection",
    "DetectionConfig",
    "PassiveBearingTracker",
    "PhaseRecord",
    "Requirement",
    "SUBMERSIBLE_REQUIREMENTS",
    "SubmarineSpec",
    "TrackSimulation",
    "TrackSolution",
    "VehicleSpec",
    "assess_conversion",
    "buoyancy_status",
    "chi2_quantile",
    "classify_clearance",
    "classify_conversion",
    "clearance_metrics",
    "detect_contract",
    "estimate_tma",
    "recommend_upgrades",
    "simulate_capture",
    "simulate_signal",
    "simulate_target_track",
    "stowage_capacity",
    "tracking_rms_error",
]
