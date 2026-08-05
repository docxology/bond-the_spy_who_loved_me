"""LIPARUS manuscript variable hydration.

Every ``{{TOKEN}}`` in ``manuscript/[0-9]*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
live canonical metrics from :func:`the_spy_who_loved_me.scenario.run_canonical`.
No result number is hand-authored in prose — it flows through this module from
an actual deterministic algorithm run, so the manuscript cannot drift from
the code. Because both the mission adapter and this module consume the same
``run_canonical`` factory, outcome ``results`` and manuscript ``{{TOKEN}}``s
can never disagree.

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

import yaml

from .scenario import run_canonical

__all__ = ["generate_variables", "load_manuscript_config", "resolve_manuscript_tree"]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

#: Number of discrete domain-concept modules in this package.
NUM_CONCEPT_MODULES = 6


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


def _canonical_metrics(require_outputs: bool) -> dict[str, Any]:
    """Run the canonical scenario and gate it when ``require_outputs``."""
    metrics = run_canonical()
    if require_outputs:
        # The canonical scenario must be non-degenerate: a contact is
        # detected, a finite detection range is solved, and the hull
        # survives its operating depth.
        if not bool(metrics["detected"]):
            raise ValueError("canonical contact was not detected — domain core regression")
        if float(metrics["aco_detection_range_m"]) <= 0.0:
            raise ValueError("canonical detection range is non-positive — domain core regression")
        if not bool(metrics["hull_feasible"]):
            raise ValueError(
                "canonical hull is not feasible at operating depth — domain core regression"
            )
    return metrics


def generate_variables(
    *, config_path: str | Path | None = None, require_outputs: bool = True
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), the deterministic canonical
            metrics must be non-degenerate — a strict gate so the manuscript
            never renders with placeholder numbers.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")

    c = _canonical_metrics(require_outputs)

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
        # sub_tracking
        "SUB_NUM_BEARINGS": str(c["track_num_bearings"]),
        "SUB_TRACK_POS_ERR_M": f"{c['track_pos_err_m']:.1f}",
        "SUB_TRACK_VEL_ERR_M_S": f"{c['track_vel_err_m_s']:.1f}",
        # tanker_capture
        "TANKER_HOLD_LENGTH_M": str(c["tanker_hold_length_m"]),
        "TANKER_MOUTH_WIDTH_M": str(c["tanker_mouth_width_m"]),
        "TANKER_CLEARANCE_M": str(c["tanker_clearance_m"]),
        "TANKER_CAPTURE_TIME_S": f"{c['capture_time_s']:.0f}",
        "TANKER_STOWAGE": str(c["capture_stowage"]),
        # vehicle_forensics
        "FORENSICS_SCORE": f"{c['forensics_score']:.2f}",
        "FORENSICS_CLASS": str(c["forensics_class"]),
        "FORENSICS_MISSING_CRITICAL": str(c["forensics_missing_critical"]),
        # acoustics
        "ACO_ABSORPTION_DB_KM": f"{c['aco_absorption_db_km']:.4f}",
        "ACO_SOUND_SPEED_M_S": f"{c['aco_sound_speed_m_s']:.0f}",
        "ACO_DETECTION_RANGE_M": f"{c['aco_detection_range_m']:.0f}",
        "ACO_FOM_DB": f"{c['aco_fom_db']:.0f}",
        # beamforming
        "BEAM_NUM_ELEMENTS": str(c["beam_num_elements"]),
        "BEAM_ESTIMATE_DEG": f"{c['beam_estimate_deg']:.1f}",
        "BEAM_BEARING_ERR_DEG": f"{c['beam_bearing_err_deg']:.1f}",
        "BEAM_CRB_DEG": f"{c['beam_crb_deg']:.2f}",
        # hull_forensics
        "HULL_COLLAPSE_DEPTH_M": f"{c['hull_collapse_depth_m']:.0f}",
        "HULL_OPERATING_DEPTH_M": f"{c['hull_operating_depth_m']:.0f}",
        "HULL_SAFETY_FACTOR": f"{c['hull_safety_factor']:.2f}",
        "HULL_FEASIBLE": "yes" if c["hull_feasible"] else "no",
        "BALLAST_VOLUME_L": f"{c['ballast_volume_l']:.0f}",
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
