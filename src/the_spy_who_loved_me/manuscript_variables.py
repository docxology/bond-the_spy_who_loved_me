"""LIPARUS manuscript variable hydration.

Every ``{{TOKEN}}`` in ``manuscript/[0-9]*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus
metrics computed live from the deterministic domain core. No result number is
hand-authored in prose — it flows through this module from an actual
algorithm run, so the manuscript cannot drift from the code.

The consuming orchestrator is ``scripts/z_generate_manuscript_variables.py``
(a thin wrapper); the live cross-reference gate lives in
``tests/test_manuscript_variables.py``.
"""

from __future__ import annotations

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .sub_tracking import estimate_tma, simulate_target_track
from .tanker_capture import (
    BayConfig,
    SubmarineSpec,
    classify_clearance,
    simulate_capture,
    stowage_capacity,
)
from .vehicle_forensics import VehicleSpec, assess_conversion

__all__ = ["generate_variables", "load_manuscript_config", "resolve_manuscript_tree"]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

#: Number of discrete domain-concept modules in this package (a stable,
#: code-derived count surfaced as a manuscript token).
NUM_CONCEPT_MODULES = 3

#: The canonical passive-tracking scenario used for manuscript metrics.
_TRACK_DURATION_S = 600.0
_TRACK_DT_S = 10.0
_TRACK_SPEED_M_S = 25.0
_TRACK_COURSE_DEG = 90.0
_TRACK_SEED = 11
_EKF_RMSE_CONVERGED_THRESHOLD_M = 250.0

#: The canonical Liparus bay and a representative quarry used for metrics.
_CANONICAL_BAY = BayConfig(
    mouth_width_m=16.0, mouth_height_m=14.0, hold_length_m=140.0, clearance_m=1.5
)
_CANONICAL_SUB = SubmarineSpec(length_m=72.0, beam_m=8.0, depth_m=7.0)

#: The canonical Lotus-Esprit-grade submersible conversion spec.
_CANONICAL_VEHICLE = VehicleSpec(
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


def _track_metrics() -> dict[str, object]:
    """Run the canonical TMA scenario and report solution error vs truth."""
    track = simulate_target_track(
        duration_s=_TRACK_DURATION_S,
        dt=_TRACK_DT_S,
        target_speed_m_s=_TRACK_SPEED_M_S,
        target_course_deg=_TRACK_COURSE_DEG,
        bearing_noise_deg=0.5,
        seed=_TRACK_SEED,
    )
    sol = estimate_tma(track.time_s, track.bearings_rad, track.ownship)
    pos_err = float(np.linalg.norm(sol.position0 - track.truth[0]))
    return {
        "num_bearings": track.num_measurements,
        "pos_err_m": pos_err,
        "residual_rms_rad": sol.residual_rms_rad,
        "converged": pos_err < _EKF_RMSE_CONVERGED_THRESHOLD_M,
    }


def _capture_metrics() -> dict[str, object]:
    """Run the canonical Liparus capture and report its outcome metrics."""
    run = simulate_capture(_CANONICAL_SUB, _CANONICAL_BAY)
    capacity = stowage_capacity(_CANONICAL_SUB, _CANONICAL_BAY)
    return {
        "clearance": classify_clearance(_CANONICAL_SUB, _CANONICAL_BAY),
        "success": run.success,
        "total_time_s": run.total_time_s,
        "num_phases": len(run.phases),
        "stowage": capacity,
        "hold_length_m": _CANONICAL_BAY.hold_length_m,
        "mouth_width_m": _CANONICAL_BAY.mouth_width_m,
        "clearance_m": _CANONICAL_BAY.clearance_m,
    }


def _forensics_metrics() -> dict[str, object]:
    """Assess the canonical conversion spec and report its traceability."""
    assessment = assess_conversion(_CANONICAL_VEHICLE)
    return {
        "score": assessment.score,
        "classification": assessment.classification.value,
        "missing_critical": len(assessment.missing_critical),
        "satisfied": len(assessment.satisfied),
    }


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(
            f"manuscript config must be a top-level mapping, got {type(data).__name__}"
        )
    return data


def generate_variables(
    *, config_path: str | Path | None = None, require_outputs: bool = True
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), the deterministic domain metrics
            must be computable — a strict gate so the manuscript never renders
            with placeholder numbers.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")

    track = _track_metrics()
    capture = _capture_metrics()
    forensics = _forensics_metrics()

    if require_outputs:
        # Real algorithm outputs must be present; the canonical scenario is
        # guaranteed to converge, so a failed track indicates a regression.
        if not track["converged"]:
            raise ValueError("canonical EKF scenario did not converge — domain core regression")

    return {
        "LIPARUS_IDENTITY": "THE_SPY_WHO_LOVED_ME",
        "LIPARUS_CODENAME": "LIPARUS",
        "LIPARUS_TITLE": str(paper.get("title", "")),
        "LIPARUS_SUBTITLE": str(paper.get("subtitle", "")),
        "LIPARUS_VERSION": str(paper.get("version", "")),
        "LIPARUS_DATE": str(paper.get("date", "")),
        "NUM_CONCEPT_MODULES": str(NUM_CONCEPT_MODULES),
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "SUB_NUM_BEARINGS": str(track["num_bearings"]),
        "SUB_TRACK_POS_ERR_M": f"{track['pos_err_m']:.1f}",
        "TANKER_HOLD_LENGTH_M": str(capture["hold_length_m"]),
        "TANKER_MOUTH_WIDTH_M": str(capture["mouth_width_m"]),
        "TANKER_CLEARANCE_M": str(capture["clearance_m"]),
        "TANKER_CAPTURE_TIME_S": f"{capture['total_time_s']:.0f}",
        "TANKER_STOWAGE": str(capture["stowage"]),
        "FORENSICS_SCORE": f"{forensics['score']:.2f}",
        "FORENSICS_CLASS": str(forensics["classification"]),
        "FORENSICS_MISSING_CRITICAL": str(forensics["missing_critical"]),
    }


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each manuscript section to ``output/manuscript/``, substituting tokens.

    Only ``NN_*.md`` section files are copied. In strict mode any leftover
    ``{{TOKEN}}`` fails so the manuscript can never render with raw braces.
    """
    manuscript_dir = (
        Path(manuscript_dir) if manuscript_dir is not None else PACKAGE_ROOT / "manuscript"
    )
    output_dir = (
        Path(output_dir) if output_dir is not None else PACKAGE_ROOT / "output" / "manuscript"
    )
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(f"unresolved manuscript tokens in {source.name}: {unresolved}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved
