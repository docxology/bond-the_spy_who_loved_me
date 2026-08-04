"""Tests for the LIPARUS MissionProvider against the frozen bond_api protocol."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from bond_api.protocol import (
    Debrief,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    ReconReport,
    ReconRequest,
    run_mission,
)
from bond_api.protocol import (
    MissionProvider as ProtocolProvider,
)
from bond_api.serialization import from_json, to_json

from the_spy_who_loved_me.mission import FILM, GADGETS, MissionProvider


def test_provider_conforms_to_protocol() -> None:
    provider = MissionProvider()
    assert provider.film == FILM
    assert isinstance(provider, ProtocolProvider)  # runtime-checkable


def test_brief() -> None:
    brief = MissionProvider().brief()
    assert isinstance(brief, MissionBrief)
    assert brief.film == FILM
    assert brief.codename == "LIPARUS"
    assert brief.objectives
    assert brief.assets
    assert brief.constraints


def test_recon() -> None:
    report = MissionProvider().recon(ReconRequest(goal="find the quarry"))
    assert isinstance(report, ReconReport)
    labels = {f.label for f in report.findings}
    assert "goal" in labels and "tracking_model" in labels


def test_plan() -> None:
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    assert isinstance(plan, MissionPlan)
    actions = [s.action for s in plan.steps]
    assert actions == [
        "run_detector",
        "run_ekf",
        "simulate_liparus",
        "assess_conversion",
        "check_outcome",
    ]


def test_execute_deterministic_results() -> None:
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    assert isinstance(outcome, MissionOutcome)
    assert outcome.success is True
    assert outcome.results["detected"] is True
    assert outcome.results["capture_success"] is True
    assert outcome.results["forensics_class"] == "submersible"
    assert outcome.provenance.seed == 11
    assert outcome.provenance.input_hash
    assert outcome.provenance.wall_time_s == 0.0


def test_execute_reproducible_across_instances() -> None:
    a = MissionProvider().execute(MissionProvider().plan(MissionProvider().brief()))
    b = MissionProvider().execute(MissionProvider().plan(MissionProvider().brief()))
    assert a.results == b.results


def test_debrief() -> None:
    provider = MissionProvider()
    debrief = provider.debrief(provider.execute(provider.plan(provider.brief())))
    assert isinstance(debrief, Debrief)
    assert debrief.lessons


def test_run_mission_full_lifecycle() -> None:
    debrief = run_mission(MissionProvider(), ReconRequest(goal="full run"))
    assert debrief.outcome.success is True


def test_outcome_serializes_round_trip() -> None:
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    text = to_json(outcome)
    restored = from_json(text)
    assert restored.results == outcome.results
    assert restored.provenance == outcome.provenance


@pytest.fixture
def gadgets() -> Iterator[None]:
    # Ensure the registry has the film registered.
    GADGETS.register(FILM, {"extra": lambda: None})
    yield
    if GADGETS.contains(FILM, "extra"):
        GADGETS.drop(FILM, "extra")


def test_gadget_registry(gadgets: None) -> None:
    assert FILM in GADGETS.films()
    names = GADGETS.gadgets_for(FILM)
    assert "detect_contract" in names
    assert "simulate_capture" in names
    assert GADGETS.contains(FILM, "detect_contract")
    assert callable(GADGETS.lookup(FILM, "assess_conversion"))


def test_gadget_lookup_unknown_raises() -> None:
    with pytest.raises(KeyError):
        GADGETS.lookup(FILM, "no_such_gadget")


def test_brief_serializes() -> None:
    text = to_json(MissionProvider().brief())
    assert '"__bond_type__": "MissionBrief"' in text
