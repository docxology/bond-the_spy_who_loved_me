"""LIPARUS figure package."""

from __future__ import annotations

from .plots import (
    FIGURES_DIR,
    PROJECT_ROOT,
    build_all_figures,
    plot_beamforming_response,
    plot_bearing_track,
    plot_capture_feasibility,
    plot_conversion_readiness,
    plot_sonar_detection_range,
)

__all__ = [
    "FIGURES_DIR",
    "PROJECT_ROOT",
    "build_all_figures",
    "plot_bearing_track",
    "plot_beamforming_response",
    "plot_capture_feasibility",
    "plot_conversion_readiness",
    "plot_sonar_detection_range",
]
