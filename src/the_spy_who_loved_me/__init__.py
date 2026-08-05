"""LIPARUS — The Spy Who Loved Me (1977) special-agent mission software.

PROJECT BOND film package. Presents six deterministic, infrastructure-free
domain cores plus the manuscript-variable hydration and the BOND-API mission
adapter:

* :mod:`.sub_tracking` — passive acoustic detection and bearing-only tracking
* :mod:`.tanker_capture` — Liparus-class tanker swallowing-submarine simulation
* :mod:`.vehicle_forensics` — Lotus-Esprit-grade submersible conversion forensics
* :mod:`.acoustics` — underwater propagation and the passive sonar equation
* :mod:`.beamforming` — uniform-linear-array beamforming and bearing estimation
* :mod:`.hull_forensics` — pressure-hull collapse depth and ballast analysis
* :mod:`.manuscript_variables` — ``{{TOKEN}}`` hydration from manuscript config
* :mod:`.mission` — the frozen ``bond_api.MissionProvider`` adapter
"""

from __future__ import annotations

from .acoustics import (
    PropagationResult,
    SonarBudget,
    detection_range_m,
    figure_of_merit_db,
    passive_sonar_equation,
    sound_speed_m_s,
    thorp_absorption,
    transmission_loss,
)
from .beamforming import (
    BeamformerResult,
    array_snapshot,
    beam_power,
    cramer_rao_bearing_std_deg,
    estimate_bearing_deg,
    steering_vector,
)
from .hull_forensics import (
    ballast_volume_m3,
    collapse_depth_m,
    collapse_pressure_pa,
    design_safety_factor,
    elastic_buckling_pressure_pa,
    hoop_stress_pa,
    pressure_at_depth_pa,
    yield_pressure_pa,
)
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
    "BeamformerResult",
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
    "PropagationResult",
    "Requirement",
    "SUBMERSIBLE_REQUIREMENTS",
    "SonarBudget",
    "SubmarineSpec",
    "TrackSimulation",
    "TrackSolution",
    "VehicleSpec",
    "array_snapshot",
    "assess_conversion",
    "ballast_volume_m3",
    "beam_power",
    "buoyancy_status",
    "chi2_quantile",
    "classify_clearance",
    "classify_conversion",
    "clearance_metrics",
    "collapse_depth_m",
    "collapse_pressure_pa",
    "cramer_rao_bearing_std_deg",
    "design_safety_factor",
    "detect_contract",
    "detection_range_m",
    "elastic_buckling_pressure_pa",
    "estimate_bearing_deg",
    "estimate_tma",
    "figure_of_merit_db",
    "hoop_stress_pa",
    "passive_sonar_equation",
    "pressure_at_depth_pa",
    "recommend_upgrades",
    "simulate_capture",
    "simulate_signal",
    "simulate_target_track",
    "sound_speed_m_s",
    "steering_vector",
    "stowage_capacity",
    "thorp_absorption",
    "tracking_rms_error",
    "transmission_loss",
    "yield_pressure_pa",
]
