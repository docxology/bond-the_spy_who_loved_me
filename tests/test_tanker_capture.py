"""Real-data, deterministic tests for the Liparus capture simulation."""

from __future__ import annotations

import pytest

from the_spy_who_loved_me.tanker_capture import (
    BayConfig,
    CapturePhase,
    CaptureRun,
    PhaseRecord,
    SubmarineSpec,
    classify_clearance,
    clearance_metrics,
    simulate_capture,
    stowage_capacity,
)


@pytest.fixture
def bay() -> BayConfig:
    return BayConfig(mouth_width_m=16.0, mouth_height_m=14.0, hold_length_m=140.0, clearance_m=1.5)


class TestSpecs:
    def test_submarine_validates(self) -> None:
        with pytest.raises(ValueError):
            SubmarineSpec(0.0, 8.0, 7.0)
        with pytest.raises(ValueError):
            SubmarineSpec(72.0, -8.0, 7.0)

    def test_bay_validates(self) -> None:
        with pytest.raises(ValueError):
            BayConfig(0.0, 14.0, 140.0)
        with pytest.raises(ValueError):
            BayConfig(16.0, 14.0, 140.0, clearance_m=-1.0)
        with pytest.raises(ValueError):
            BayConfig(16.0, 14.0, 140.0, seal_requirement=1.5)


class TestClearance:
    def test_fits_with_margin(self, bay: BayConfig) -> None:
        sub = SubmarineSpec(80.0, 10.0, 9.0)
        c = clearance_metrics(sub, bay)
        assert c.fits is True
        assert c.beam_clearance_m == pytest.approx(6.0)
        assert c.depth_clearance_m == pytest.approx(5.0)
        assert c.as_dict()["fits"] is True

    def test_denied_oversized(self, bay: BayConfig) -> None:
        sub = SubmarineSpec(200.0, 20.0, 20.0)
        c = clearance_metrics(sub, bay)
        assert c.fits is False

    def test_classify_denied(self, bay: BayConfig) -> None:
        assert classify_clearance(SubmarineSpec(200.0, 20.0, 20.0), bay) == "denied"

    def test_classify_tight(self, bay: BayConfig) -> None:
        # Fits but one margin < required 1.5m clearance.
        sub = SubmarineSpec(92.0, 15.0, 13.0)
        assert classify_clearance(sub, bay) == "tight"

    def test_classify_fits(self, bay: BayConfig) -> None:
        assert classify_clearance(SubmarineSpec(72.0, 8.0, 7.0), bay) == "fits"


class TestStowage:
    def test_capacity_when_fits(self, bay: BayConfig) -> None:
        assert stowage_capacity(SubmarineSpec(72.0, 8.0, 7.0), bay) >= 1

    def test_capacity_zero_when_not_fits(self, bay: BayConfig) -> None:
        assert stowage_capacity(SubmarineSpec(200.0, 20.0, 20.0), bay) == 0


class TestCaptureRun:
    def test_successful_capture_phases(self, bay: BayConfig) -> None:
        run = simulate_capture(SubmarineSpec(72.0, 8.0, 7.0), bay)
        assert run.success is True
        assert len(run.phases) == 4  # approach, ingress, hatch_seal, secure
        names = [p.phase for p in run.phases]
        assert names == [
            CapturePhase.APPROACH,
            CapturePhase.INGRESS,
            CapturePhase.HATCH_SEAL,
            CapturePhase.SECURE,
        ]
        assert all(p.ok for p in run.phases)
        assert run.total_time_s == pytest.approx(630.0)  # 240+180+90+120

    def test_ingress_failure_aborts(self, bay: BayConfig) -> None:
        # Mouth clearance insufficient (beam too wide for the 1.5m margin).
        run = simulate_capture(SubmarineSpec(72.0, 15.0, 7.0), bay)
        assert run.success is False
        assert len(run.phases) == 2  # approach + failed ingress
        assert run.phases[-1].phase == CapturePhase.INGRESS
        assert run.phases[-1].ok is False

    def test_secure_failure(self, bay: BayConfig) -> None:
        # Hold too short for the length margin.
        run = simulate_capture(SubmarineSpec(140.0, 8.0, 7.0), bay)
        assert run.success is False

    def test_phase_record_duration(self) -> None:
        p = PhaseRecord(CapturePhase.APPROACH, 0.0, 240.0, True)
        assert p.duration_s == 240.0

    def test_empty_run_total_time(self, bay: BayConfig) -> None:
        run = CaptureRun(SubmarineSpec(72.0, 8.0, 7.0), bay)
        assert run.total_time_s == 0.0
        assert run.as_dict()["total_time_s"] == 0.0
