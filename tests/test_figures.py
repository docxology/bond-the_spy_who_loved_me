"""Deterministic figure generation tests (real rendering, Agg backend)."""

from __future__ import annotations

from pathlib import Path

from the_spy_who_loved_me import SonarBudget, array_snapshot
from the_spy_who_loved_me.figures import (
    FIGURES_DIR,
    build_all_figures,
    plot_beamforming_response,
    plot_bearing_track,
    plot_capture_feasibility,
    plot_conversion_readiness,
    plot_sonar_detection_range,
)
from the_spy_who_loved_me.sub_tracking import estimate_tma, simulate_target_track
from the_spy_who_loved_me.tanker_capture import BayConfig
from the_spy_who_loved_me.vehicle_forensics import VehicleSpec


def test_build_all_figures() -> None:
    built = build_all_figures()
    assert set(built) == {
        "bearing_track",
        "beamforming_response",
        "capture_feasibility",
        "conversion_readiness",
        "sonar_detection_range",
    }
    for name, path in built.items():
        assert Path(path).is_file()
        assert Path(path).stat().st_size > 0
        assert name in path.name


def test_bearing_track_fig() -> None:
    track = simulate_target_track(300.0, 10.0, 25.0, 90.0, 0.5, seed=3)
    sol = estimate_tma(track.time_s, track.bearings_rad, track.ownship)
    path = plot_bearing_track(track, sol, filename="test_bearing.png")
    assert Path(path).is_file()
    path.unlink()


def test_beamforming_fig() -> None:
    snap = array_snapshot(0.5, 0.5, 8, 1.0, 0.1, 11)
    path = plot_beamforming_response(snap, 0.5, 30.0, filename="test_beam.png")
    assert Path(path).is_file()
    path.unlink()


def test_sonar_range_fig() -> None:
    path = plot_sonar_detection_range(
        SonarBudget(160.0, 70.0, 20.0, 10.0), 400.0, filename="test_sonar.png"
    )
    assert Path(path).is_file()
    path.unlink()


def test_capture_feasibility_fig() -> None:
    bay = BayConfig(mouth_width_m=16.0, mouth_height_m=14.0, hold_length_m=140.0, clearance_m=1.5)
    path = plot_capture_feasibility(
        [(72.0, 8.0, 7.0), (95.0, 12.0, 11.0)], bay, filename="test_capture.png"
    )
    assert Path(path).is_file()
    path.unlink()


def test_conversion_fig() -> None:
    vehicles = [
        VehicleSpec("a", 1000.0, 1.1, {}),
        VehicleSpec(
            "b",
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
    path = plot_conversion_readiness(vehicles, filename="test_conv.png")
    assert Path(path).is_file()
    path.unlink()


def test_figures_dir_defined() -> None:
    assert FIGURES_DIR.name == "figures"
