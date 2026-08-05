"""Real-data, deterministic tests for the Liparus capture simulation."""

from __future__ import annotations

import pytest

from the_spy_who_loved_me.tanker_capture import (
    _PHASE_DURATIONS,
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
        # Derived from the declared schedule rather than restating its total.
        assert run.total_time_s == pytest.approx(sum(_PHASE_DURATIONS.values()))

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


class TestReportedTimeIsASchedule:
    """``total_time_s`` is a declared schedule, and the tests say so.

    The reported duration is the sum of the fixed ``_PHASE_DURATIONS`` for
    the phases a run reached. Nothing in the module makes it depend on the
    submarine or the bay, so a test that only checked ``630.0`` on the
    canonical case would read as a result while pinning a constant. These
    assertions pin what is actually true: the total tracks *how far the run
    got*, and is invariant to geometry at equal progress.
    """

    def test_total_is_the_sum_of_the_phases_that_ran(self, bay: BayConfig) -> None:
        run = simulate_capture(SubmarineSpec(72.0, 8.0, 7.0), bay)
        assert run.total_time_s == pytest.approx(sum(p.duration_s for p in run.phases))
        assert run.total_time_s == pytest.approx(sum(_PHASE_DURATIONS[p.phase] for p in run.phases))

    def test_aborted_run_reports_less_time(self, bay: BayConfig) -> None:
        full = simulate_capture(SubmarineSpec(72.0, 8.0, 7.0), bay)
        aborted = simulate_capture(SubmarineSpec(72.0, 15.0, 7.0), bay)  # ingress fails
        assert len(aborted.phases) < len(full.phases)
        assert aborted.total_time_s < full.total_time_s
        assert aborted.total_time_s == pytest.approx(
            _PHASE_DURATIONS[CapturePhase.APPROACH] + _PHASE_DURATIONS[CapturePhase.INGRESS]
        )

    def test_time_is_invariant_to_submarine_size(self, bay: BayConfig) -> None:
        """Two very different submarines, both reaching all four phases."""
        small = simulate_capture(SubmarineSpec(10.0, 3.0, 3.0), bay)
        large = simulate_capture(SubmarineSpec(72.0, 8.0, 7.0), bay)
        assert small.success and large.success
        assert small.total_time_s == large.total_time_s

    def test_a_failed_capture_still_reports_the_full_schedule(self, bay: BayConfig) -> None:
        """Failure at *secure* does not shorten the timeline — read it that way."""
        failed = simulate_capture(SubmarineSpec(139.0, 8.0, 7.0), bay)
        succeeded = simulate_capture(SubmarineSpec(72.0, 8.0, 7.0), bay)
        assert failed.success is False
        assert failed.total_time_s == succeeded.total_time_s


class TestSecurePredicateIsGeometryOnly:
    """The *secure* stage turns on hold-length clearance and nothing else.

    A ``seal_requirement`` field used to add ``and bay.seal_requirement <=
    1.0`` here, which ``BayConfig.__post_init__`` had already made
    unfalsifiable. The field is gone; these assertions pin the boundary that
    remains, on both sides.
    """

    def test_secure_fails_just_inside_the_margin(self, bay: BayConfig) -> None:
        # hold 140 m, clearance 1.5 m -> the boundary sits at 138.5 m.
        assert simulate_capture(SubmarineSpec(138.6, 8.0, 7.0), bay).success is False
        assert simulate_capture(SubmarineSpec(138.4, 8.0, 7.0), bay).success is True

    def test_secure_note_names_only_the_length(self, bay: BayConfig) -> None:
        run = simulate_capture(SubmarineSpec(139.0, 8.0, 7.0), bay)
        assert run.phases[-1].phase == CapturePhase.SECURE
        assert "seal" not in run.phases[-1].note

    def test_hatch_seal_phase_declares_it_models_no_seal(self, bay: BayConfig) -> None:
        run = simulate_capture(SubmarineSpec(72.0, 8.0, 7.0), bay)
        seal = next(p for p in run.phases if p.phase == CapturePhase.HATCH_SEAL)
        assert seal.ok is True
        assert "not modelled" in seal.note
