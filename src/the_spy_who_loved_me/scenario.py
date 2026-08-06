"""LIPARUS — canonical scenario and single source of truth for mission metrics.

Every numeric claim the mission adapter emits and the manuscript hydrates
flows through :func:`run_canonical`, which runs the six deterministic domain
modules against fixed, documented scenario parameters. Sharing this one
factory between ``mission.execute`` and ``manuscript_variables`` guarantees
the outcome ``results`` and the ``{{TOKEN}}`` values can never disagree.

All parameters are module-level constants so the canonical scenario is fully
reproducible and auditable.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

import numpy as np

from .acoustics import (
    SonarBudget,
    detection_range_m,
    figure_of_merit_db,
    sound_speed_m_s,
    thorp_absorption,
)
from .beamforming import array_snapshot, cramer_rao_bearing_std_deg, estimate_bearing_deg
from .hull_forensics import ballast_volume_m3, collapse_depth_m, design_safety_factor
from .sub_tracking import (
    DetectionConfig,
    PassiveBearingTracker,
    detect_contract,
    estimate_tma,
    simulate_signal,
    simulate_target_track,
    tracking_rms_error,
)
from .tanker_capture import (
    BayConfig,
    SubmarineSpec,
    classify_clearance,
    simulate_capture,
    stowage_capacity,
)
from .vehicle_forensics import VehicleSpec, assess_conversion

__all__ = [
    "SEED",
    "canonical_input_hash",
    "canonical_parameters",
    "run_canonical",
]

#: The deterministic seed used across the canonical scenario.
SEED = 11

# --- Passive detection (sub_tracking) ---
_DETECTION_SNR_DB = 12.0
_DETECTION_FS = 8000
_DETECTION_DURATION_S = 2.0
_DETECTION_P_FA = 1e-3

# --- Extended Kalman Filter (sub_tracking) ---
# Recursive-filter seed and process/measurement noise for the EKF that the
# canonical scenario runs alongside batch TMA (Section 3). The initial state
# is a coarse guess; the filter converges over the scenario window regardless.
_EKF_INIT_X_M = 3800.0
_EKF_INIT_Y_M = 1900.0
_EKF_INIT_VX_M_S = 0.0
_EKF_INIT_VY_M_S = 25.0
_EKF_INIT_POS_COV_M2 = 1e4
_EKF_INIT_VEL_COV_M2S2 = 1e2
_EKF_PROCESS_NOISE = 1e-3
_EKF_MEASUREMENT_NOISE_RAD = 5e-3

# --- Bearing-only tracking (sub_tracking) ---
_TRACK_DURATION_S = 600.0
_TRACK_DT_S = 10.0
_TRACK_SPEED_M_S = 25.0
_TRACK_COURSE_DEG = 90.0
_TRACK_BEARING_NOISE_DEG = 0.5

# --- Liparus capture (tanker_capture) ---
_BAY = BayConfig(mouth_width_m=16.0, mouth_height_m=14.0, hold_length_m=140.0, clearance_m=1.5)
_SUB = SubmarineSpec(length_m=72.0, beam_m=8.0, depth_m=7.0)

# --- Vehicle forensics (vehicle_forensics) ---
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

# --- Passive sonar equation (acoustics) ---
_SONAR_BUDGET = SonarBudget(sl_db=160.0, nl_db=70.0, di_db=20.0, dt_db=10.0)
_SONAR_FREQ_HZ = 400.0
_SOUND_TEMP_C = 10.0
_SOUND_SALINITY_PSU = 35.0
_SOUND_DEPTH_M = 0.0

# --- ULA beamforming (beamforming) ---
_BEAM_N_ELEMENTS = 8
_BEAM_D_OVER_LAMBDA = 0.5
_BEAM_TRUE_BEARING_DEG = 30.0
_BEAM_AMPLITUDE = 1.0
_BEAM_NOISE_STD = 0.1
#: Element-level SNR is *derived* from the snapshot parameters rather than
#: stated independently. Quoting it as its own constant would let the Cramer-Rao
#: bound silently describe a different array than the one actually sampled the
#: moment ``_BEAM_AMPLITUDE`` or ``_BEAM_NOISE_STD`` changed.
_BEAM_SNR_DB = 10.0 * math.log10((_BEAM_AMPLITUDE / _BEAM_NOISE_STD) ** 2)

# --- Pressure hull (hull_forensics) ---
_HULL_RADIUS_M = 0.8
_HULL_THICKNESS_M = 0.02
_HULL_YIELD_PA = 350.0e6
_HULL_YOUNG_PA = 200.0e9
_HULL_OPERATING_DEPTH_M = 40.0
_HULL_SF_MIN = 1.5


def canonical_parameters() -> dict[str, float | int]:
    """Every input the canonical scenario is run with, as one flat mapping.

    This is the *input* side of :func:`run_canonical`: the seed and each
    module-level constant that reaches an algorithm. It exists so the
    provenance record can carry a hash of what was actually fed in
    (:func:`canonical_input_hash`) rather than a fixed package label.

    Any parameter added to the scenario must be added here too, or the input
    hash silently stops covering it; ``tests/test_scenario.py`` pins the key
    set against the constants defined in this module.
    """
    return {
        "seed": SEED,
        "detection_snr_db": _DETECTION_SNR_DB,
        "detection_fs": _DETECTION_FS,
        "detection_duration_s": _DETECTION_DURATION_S,
        "detection_p_fa": _DETECTION_P_FA,
        "ekf_init_x_m": _EKF_INIT_X_M,
        "ekf_init_y_m": _EKF_INIT_Y_M,
        "ekf_init_vx_m_s": _EKF_INIT_VX_M_S,
        "ekf_init_vy_m_s": _EKF_INIT_VY_M_S,
        "ekf_init_pos_cov_m2": _EKF_INIT_POS_COV_M2,
        "ekf_init_vel_cov_m2s2": _EKF_INIT_VEL_COV_M2S2,
        "ekf_process_noise": _EKF_PROCESS_NOISE,
        "ekf_measurement_noise_rad": _EKF_MEASUREMENT_NOISE_RAD,
        "track_duration_s": _TRACK_DURATION_S,
        "track_dt_s": _TRACK_DT_S,
        "track_speed_m_s": _TRACK_SPEED_M_S,
        "track_course_deg": _TRACK_COURSE_DEG,
        "track_bearing_noise_deg": _TRACK_BEARING_NOISE_DEG,
        "bay_mouth_width_m": _BAY.mouth_width_m,
        "bay_mouth_height_m": _BAY.mouth_height_m,
        "bay_hold_length_m": _BAY.hold_length_m,
        "bay_clearance_m": _BAY.clearance_m,
        "sub_length_m": _SUB.length_m,
        "sub_beam_m": _SUB.beam_m,
        "sub_depth_m": _SUB.depth_m,
        "vehicle_dry_mass_kg": _VEHICLE.dry_mass_kg,
        "vehicle_displacement_m3": _VEHICLE.displacement_m3,
        "vehicle_systems_fitted": sum(1 for fitted in _VEHICLE.systems.values() if fitted),
        "sonar_sl_db": _SONAR_BUDGET.sl_db,
        "sonar_nl_db": _SONAR_BUDGET.nl_db,
        "sonar_di_db": _SONAR_BUDGET.di_db,
        "sonar_dt_db": _SONAR_BUDGET.dt_db,
        "sonar_freq_hz": _SONAR_FREQ_HZ,
        "sound_temp_c": _SOUND_TEMP_C,
        "sound_salinity_psu": _SOUND_SALINITY_PSU,
        "sound_depth_m": _SOUND_DEPTH_M,
        "beam_n_elements": _BEAM_N_ELEMENTS,
        "beam_d_over_lambda": _BEAM_D_OVER_LAMBDA,
        "beam_true_bearing_deg": _BEAM_TRUE_BEARING_DEG,
        "beam_amplitude": _BEAM_AMPLITUDE,
        "beam_noise_std": _BEAM_NOISE_STD,
        "hull_radius_m": _HULL_RADIUS_M,
        "hull_thickness_m": _HULL_THICKNESS_M,
        "hull_yield_pa": _HULL_YIELD_PA,
        "hull_young_pa": _HULL_YOUNG_PA,
        "hull_operating_depth_m": _HULL_OPERATING_DEPTH_M,
        "hull_sf_min": _HULL_SF_MIN,
    }


def canonical_input_hash(parameters: Mapping[str, float | int] | None = None) -> str:
    """SHA-256 over a stable serialisation of the scenario inputs.

    Defaults to :func:`canonical_parameters`. The serialisation is
    key-sorted compact JSON, so the digest depends on the parameter *values*
    and names and not on dict ordering or formatting — editing any canonical
    parameter changes it, and re-running with the same parameters does not.
    """
    params = dict(canonical_parameters() if parameters is None else parameters)
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_canonical() -> dict[str, Any]:
    """Run the six domain modules over the canonical scenario.

    Returns a flat ``dict[str, Any]`` of measured metrics: detection and
    tracking accuracy, Liparus capture feasibility, vehicle conversion,
    sonar detection range, beamforming bearing error, and hull collapse
    depth together with the required ballast volume.
    """
    # 1. Passive acoustic detection
    signal = simulate_signal(_DETECTION_DURATION_S, _DETECTION_FS, _DETECTION_SNR_DB, SEED)
    detection = detect_contract(signal, DetectionConfig(p_fa=_DETECTION_P_FA))

    # 2. Bearing-only tracking (maneuvering ownship TMA)
    track = simulate_target_track(
        _TRACK_DURATION_S,
        _TRACK_DT_S,
        _TRACK_SPEED_M_S,
        _TRACK_COURSE_DEG,
        _TRACK_BEARING_NOISE_DEG,
        SEED,
    )
    sol = estimate_tma(track.time_s, track.bearings_rad, track.ownship)
    pos_err = float(np.linalg.norm(sol.position0 - track.truth[0]))
    course_rad = math.radians(_TRACK_COURSE_DEG)
    vel_err = float(
        np.linalg.norm(
            sol.velocity
            - (_TRACK_SPEED_M_S * np.asarray([math.cos(course_rad), math.sin(course_rad)]))
        )
    )

    # 2b. Extended Kalman Filter over the same bearing sequence (recursive
    # partner to the batch TMA; reported so the two are comparable on one run).
    tracker = PassiveBearingTracker(
        [_EKF_INIT_X_M, _EKF_INIT_Y_M, _EKF_INIT_VX_M_S, _EKF_INIT_VY_M_S],
        [
            [_EKF_INIT_POS_COV_M2, 0.0, 0.0, 0.0],
            [0.0, _EKF_INIT_POS_COV_M2, 0.0, 0.0],
            [0.0, 0.0, _EKF_INIT_VEL_COV_M2S2, 0.0],
            [0.0, 0.0, 0.0, _EKF_INIT_VEL_COV_M2S2],
        ],
        process_noise=_EKF_PROCESS_NOISE,
        measurement_noise_rad=_EKF_MEASUREMENT_NOISE_RAD,
    )
    ekf_hist = tracker.run(track)
    ekf_warmup = track.num_measurements // 2
    ekf_rms = tracking_rms_error(ekf_hist, track.truth, warmup=ekf_warmup)

    # 3. Liparus capture
    capture = simulate_capture(_SUB, _BAY)

    # 4. Vehicle conversion forensics
    forensics = assess_conversion(_VEHICLE)

    # 5. Passive sonar equation + propagation
    sonar = detection_range_m(_SONAR_BUDGET, _SONAR_FREQ_HZ)

    # 6. ULA beamforming + bearing CRB
    snapshot = array_snapshot(
        math.radians(_BEAM_TRUE_BEARING_DEG),
        _BEAM_D_OVER_LAMBDA,
        _BEAM_N_ELEMENTS,
        _BEAM_AMPLITUDE,
        _BEAM_NOISE_STD,
        SEED,
    )
    beam = estimate_bearing_deg(snapshot, _BEAM_D_OVER_LAMBDA)
    beam_refined = estimate_bearing_deg(snapshot, _BEAM_D_OVER_LAMBDA, interpolate=True)
    crb_deg = cramer_rao_bearing_std_deg(
        _BEAM_N_ELEMENTS, _BEAM_D_OVER_LAMBDA, _BEAM_SNR_DB, math.radians(_BEAM_TRUE_BEARING_DEG)
    )

    # 7. Pressure hull collapse depth + ballast
    hull_depth = collapse_depth_m(_HULL_RADIUS_M, _HULL_THICKNESS_M, _HULL_YIELD_PA, _HULL_YOUNG_PA)
    safety_factor = design_safety_factor(hull_depth, _HULL_OPERATING_DEPTH_M)
    ballast_l = ballast_volume_m3(_VEHICLE.dry_mass_kg, _VEHICLE.displacement_m3) * 1000.0

    return {
        # sub_tracking
        "detected": detection.detected,
        "detection_margin_db": round(detection.margin_db, 2),
        "detection_p_fa": detection.p_fa,
        "track_pos_err_m": round(pos_err, 1),
        "track_vel_err_m_s": round(vel_err, 1),
        "track_num_bearings": track.num_measurements,
        "track_residual_rms_rad": round(sol.residual_rms_rad, 4),
        "track_ekf_rms_m": round(ekf_rms, 1),
        "track_duration_s": _TRACK_DURATION_S,
        "track_dt_s": _TRACK_DT_S,
        "track_speed_m_s": _TRACK_SPEED_M_S,
        "track_course_deg": _TRACK_COURSE_DEG,
        "track_range0_m": float(track.truth[0][0] ** 2 + track.truth[0][1] ** 2) ** 0.5,
        "track_bearing_noise_deg": _TRACK_BEARING_NOISE_DEG,
        # tanker_capture
        "capture_clearance": classify_clearance(_SUB, _BAY),
        "capture_success": capture.success,
        # Declared nominal schedule, not a measured or derived duration —
        # see ``tanker_capture._PHASE_DURATIONS``. It is the sum of the fixed
        # per-phase durations for the phases this run reached.
        "capture_time_s": round(capture.total_time_s, 1),
        "capture_phases_run": len(capture.phases),
        "capture_stowage": stowage_capacity(_SUB, _BAY),
        "tanker_hold_length_m": _BAY.hold_length_m,
        "tanker_mouth_width_m": _BAY.mouth_width_m,
        "tanker_mouth_height_m": _BAY.mouth_height_m,
        "tanker_clearance_m": _BAY.clearance_m,
        "tanker_sub_length_m": _SUB.length_m,
        # vehicle_forensics
        "forensics_class": forensics.classification.value,
        "forensics_score": round(forensics.score, 2),
        "forensics_missing_critical": len(forensics.missing_critical),
        "vehicle_dry_mass_kg": _VEHICLE.dry_mass_kg,
        "vehicle_displacement_m3": _VEHICLE.displacement_m3,
        # acoustics
        "aco_absorption_db_km": round(thorp_absorption(_SONAR_FREQ_HZ), 4),
        "aco_sound_speed_m_s": round(
            sound_speed_m_s(_SOUND_TEMP_C, _SOUND_SALINITY_PSU, _SOUND_DEPTH_M), 1
        ),
        "aco_detection_range_m": round(sonar.range_m, 0),
        "aco_fom_db": round(figure_of_merit_db(_SONAR_BUDGET), 1),
        "aco_freq_hz": _SONAR_FREQ_HZ,
        "aco_source_level_db": _SONAR_BUDGET.sl_db,
        "aco_noise_level_db": _SONAR_BUDGET.nl_db,
        "aco_directivity_db": _SONAR_BUDGET.di_db,
        "aco_detection_threshold_db": _SONAR_BUDGET.dt_db,
        "aco_temp_c": _SOUND_TEMP_C,
        "aco_salinity_psu": _SOUND_SALINITY_PSU,
        # beamforming
        "beam_num_elements": _BEAM_N_ELEMENTS,
        "beam_true_bearing_deg": _BEAM_TRUE_BEARING_DEG,
        "beam_estimate_deg": round(beam.bearing_deg, 2),
        "beam_bearing_err_deg": round(abs(beam.bearing_deg - _BEAM_TRUE_BEARING_DEG), 2),
        "beam_bearing_err_interp_deg": round(
            abs(beam_refined.bearing_deg - _BEAM_TRUE_BEARING_DEG), 3
        ),
        "beam_estimate_interp_deg": round(beam_refined.bearing_deg, 3),
        "beam_crb_deg": round(crb_deg, 3),
        "beam_snr_db": round(_BEAM_SNR_DB, 1),
        # Read back off the grid the estimator actually scanned, so the
        # quantisation floor reported in the manuscript can never describe a
        # different grid than the one that produced the estimate.
        "beam_scan_step_deg": round(float(beam.scan[1] - beam.scan[0]), 3),
        # hull_forensics
        "hull_collapse_depth_m": round(hull_depth, 1),
        "hull_operating_depth_m": _HULL_OPERATING_DEPTH_M,
        "hull_radius_m": _HULL_RADIUS_M,
        "hull_thickness_mm": _HULL_THICKNESS_M * 1000.0,
        "hull_yield_mpa": _HULL_YIELD_PA / 1.0e6,
        "hull_safety_factor": round(safety_factor, 2),
        "hull_feasible": bool(safety_factor >= _HULL_SF_MIN),
        "ballast_volume_l": round(ballast_l, 1),
    }
