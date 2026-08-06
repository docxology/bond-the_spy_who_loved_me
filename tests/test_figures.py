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


def test_capture_feasibility_colours_all_three_fit_classes(tmp_path: Path) -> None:
    """Exercise the green / orange / red colour branches in one render.

    The default figure only ever plots submarines that fit comfortably, so
    the "tight" branch (fits, but inside the required margin) never ran.
    These three sizes are chosen against the bay below to hit each branch.
    """
    bay = BayConfig(mouth_width_m=16.0, mouth_height_m=14.0, hold_length_m=140.0, clearance_m=1.5)
    sizes = [
        (72.0, 8.0, 7.0),  # comfortable margin -> green
        (139.0, 15.5, 13.6),  # fits but inside the 1.5 m margin -> orange
        (200.0, 20.0, 18.0),  # does not fit at all -> red
    ]
    out = plot_capture_feasibility(sizes, bay, filename="capture_feasibility_branches.png")
    assert out.is_file()
    assert out.stat().st_size > 0


class TestFigureDeterminism:
    """``06_reproducibility.md`` claims byte-identical figure renders.

    The earlier figure gate asserted existence and non-empty size only, so a
    matplotlib version bump, an embedded creation timestamp, or unseeded
    jitter would pass silently while the reproducibility claim was false.
    Rendering each figure twice must yield byte-identical PNGs.
    """

    def test_all_figures_are_byte_deterministic(self) -> None:
        first = {name: Path(path).read_bytes() for name, path in build_all_figures().items()}
        second = {name: Path(path).read_bytes() for name, path in build_all_figures().items()}
        assert set(first) == set(second)
        for name in first:
            assert first[name] == second[name], f"{name} render is not deterministic"
