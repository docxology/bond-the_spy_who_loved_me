"""LIPARUS — Liparus-class tanker capture scenario simulation.

The *Liparus* is the supervillain tanker in *The Spy Who Loved Me* whose
gigantic hull opens like a mouth to swallow whole submarines. This module
models that capture operation as a deterministic geometric-feasibility check
plus a discrete-event sequence simulation: an approaching submarine must fit
the dock opening with clearance, then pass through a sequence of phases
(approach, ingress, hatch-seal, secure) each of which succeeds or fails on a
fixed predicate.

Everything here is deterministic — no RNG, no wall clock — so a capture run
is reproducible byte-for-byte and the geometry is exact rather than
approximate. Three reusable capabilities are provided:

* :func:`clearance_metrics` / :func:`classify_clearance` — closed-form
  per-axis clearance between a submarine and the bay mouth, and an overall
  fit verdict.
* :func:`stowage_capacity` — how many submarines of a given size the bay
  can hold in a single swallow.
* :func:`simulate_capture` — the discrete-event sequence producing a
  :class:`CaptureRun` with a per-phase timeline and final status.

What is *not* modelled, stated so no reader over-reads the output:

* **Seal integrity has no physics here.** Nothing in this module computes a
  seal quality, so the hatch-seal phase carries no independent predicate: it
  succeeds whenever the ingress succeeded. A ``seal_requirement`` field was
  removed from :class:`BayConfig` in favour of saying so, because it was
  validated into the range ``[0, 1]`` at construction and then compared
  against ``1.0`` at run time — a conjunct that could never be False.
* **Phase durations are declared, not derived.** ``_PHASE_DURATIONS`` is an
  assumed nominal schedule (see its comment); the reported ``total_time_s``
  is the sum of the scheduled phases that actually ran, so it varies with
  *how far the operation got* but never with submarine size or bay geometry.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

__all__ = [
    "BayConfig",
    "CapturePhase",
    "CaptureRun",
    "PhaseRecord",
    "SubmarineSpec",
    "clearance_metrics",
    "classify_clearance",
    "simulate_capture",
    "stowage_capacity",
]


class CapturePhase(str, enum.Enum):
    """The discrete stages of a Liparus capture operation."""

    APPROACH = "approach"
    INGRESS = "ingress"
    HATCH_SEAL = "hatch_seal"
    SECURE = "secure"
    COMPLETE = "complete"


@dataclass(frozen=True)
class SubmarineSpec:
    """Dimensions of a submarine to be swallowed (metres)."""

    length_m: float
    beam_m: float
    depth_m: float

    def __post_init__(self) -> None:
        if self.length_m <= 0.0 or self.beam_m <= 0.0 or self.depth_m <= 0.0:
            raise ValueError("all dimensions must be > 0")


@dataclass(frozen=True)
class BayConfig:
    """Geometry of the Liparus dock mouth and hold."""

    mouth_width_m: float
    mouth_height_m: float
    hold_length_m: float
    #: Minimum per-axis clearance the operation demands, metres.
    clearance_m: float = 1.5

    def __post_init__(self) -> None:
        if self.mouth_width_m <= 0.0 or self.mouth_height_m <= 0.0 or self.hold_length_m <= 0.0:
            raise ValueError("bay dimensions must all be > 0")
        if self.clearance_m < 0.0:
            raise ValueError("clearance_m must be >= 0")


@dataclass(frozen=True)
class Clearance:
    """Per-axis and overall geometric clearance of a submarine in a bay."""

    beam_clearance_m: float
    depth_clearance_m: float
    length_clearance_m: float
    fits: bool

    def as_dict(self) -> dict[str, float | bool]:
        """Dict form for provenance records and reporting."""
        return {
            "beam_clearance_m": self.beam_clearance_m,
            "depth_clearance_m": self.depth_clearance_m,
            "length_clearance_m": self.length_clearance_m,
            "fits": self.fits,
        }


def clearance_metrics(submarine: SubmarineSpec, bay: BayConfig) -> Clearance:
    """Compute the per-axis clearance margins.

    The mouth must clear the submarine's beam and depth; the hold must clear
    its length. A negative margin means the submarine does not fit on that
    axis; ``fits`` is true only when every margin is non-negative.
    """
    beam_c = bay.mouth_width_m - submarine.beam_m
    depth_c = bay.mouth_height_m - submarine.depth_m
    length_c = bay.hold_length_m - submarine.length_m
    fits = beam_c >= 0.0 and depth_c >= 0.0 and length_c >= 0.0
    return Clearance(
        beam_clearance_m=beam_c, depth_clearance_m=depth_c, length_clearance_m=length_c, fits=fits
    )


def classify_clearance(submarine: SubmarineSpec, bay: BayConfig) -> str:
    """Classify the submarine's fit as ``"fits"``, ``"tight"`` or ``"denied"``.

    ``"tight"`` means it fits but at least one margin is below the bay's
    ``clearance_m`` safety requirement (the operation is feasible but
    risky); ``"denied"`` means at least one margin is negative.
    """
    c = clearance_metrics(submarine, bay)
    if not c.fits:
        return "denied"
    margins = (c.beam_clearance_m, c.depth_clearance_m, c.length_clearance_m)
    if any(m < bay.clearance_m for m in margins):
        return "tight"
    return "fits"


def stowage_capacity(submarine: SubmarineSpec, bay: BayConfig) -> int:
    """How many of this submarine the hold can swallow in one pass.

    A floor of (hold length) / (sub length + required clearance), at least 1
    when the first submarine fits at all, else 0.
    """
    c = clearance_metrics(submarine, bay)
    if not c.fits:
        return 0
    pitch = submarine.length_m + bay.clearance_m
    capacity = int(bay.hold_length_m // pitch)
    return max(1, capacity)


@dataclass(frozen=True)
class PhaseRecord:
    """One completed phase of a capture run."""

    phase: CapturePhase
    start_s: float
    end_s: float
    ok: bool
    note: str = ""

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


@dataclass(frozen=True)
class CaptureRun:
    """Full outcome of a Liparus capture simulation."""

    submarine: SubmarineSpec
    bay: BayConfig
    phases: tuple[PhaseRecord, ...] = field(default_factory=tuple)
    success: bool = False

    @property
    def total_time_s(self) -> float:
        """Elapsed schedule time of the phases that ran (last phase end).

        This is **not** a measured or derived duration: it is the sum of the
        declared nominal durations in :data:`_PHASE_DURATIONS` for the phases
        the run reached. It therefore changes when the run aborts early, and
        does not change with submarine size or bay geometry.
        """
        if not self.phases:
            return 0.0
        return self.phases[-1].end_s

    def as_dict(self) -> dict[str, object]:
        """Plain-dict summary suitable for JSON provenance records."""
        return {
            "clearance": classify_clearance(self.submarine, self.bay),
            "success": self.success,
            "total_time_s": self.total_time_s,
            "phases": [
                {
                    "phase": p.phase.value,
                    "start_s": p.start_s,
                    "end_s": p.end_s,
                    "ok": p.ok,
                    "note": p.note,
                }
                for p in self.phases
            ],
        }


def _phase(
    phase: CapturePhase,
    start: float,
    duration: float,
    ok: bool,
    note: str = "",
) -> PhaseRecord:
    return PhaseRecord(phase=phase, start_s=start, end_s=start + duration, ok=ok, note=note)


#: Declared nominal per-phase durations (seconds).
#:
#: These four values are **assumptions, not measurements or derivations** —
#: no timing model, tow speed, or hydrodynamic transit calculation stands
#: behind them, and no source is cited for them. Nothing in this module makes
#: a phase duration depend on the submarine or the bay, so any total assembled
#: from them is a schedule, not a result. Treat a reported ``total_time_s`` as
#: "the nominal timeline elapsed to this point", and never as evidence about
#: how long a particular capture would take.
_PHASE_DURATIONS: dict[CapturePhase, float] = {
    CapturePhase.APPROACH: 240.0,
    CapturePhase.INGRESS: 180.0,
    CapturePhase.HATCH_SEAL: 90.0,
    CapturePhase.SECURE: 120.0,
}


def simulate_capture(submarine: SubmarineSpec, bay: BayConfig) -> CaptureRun:
    """Simulate a full Liparus capture operation deterministically.

    The operation runs through the four stages in order. Each stage's ``ok``
    is decided by a fixed, documented predicate:

    * *approach* always succeeds (the bay is under tow control) — it is a
      timeline entry, not a test;
    * *ingress* succeeds iff the mouth clears the submarine's beam **and**
      depth by at least ``bay.clearance_m``;
    * *hatch-seal* succeeds iff the ingress succeeded (a failed ingress
      aborts before sealing) — no seal-integrity quantity is modelled, so
      this stage likewise tests nothing of its own;
    * *secure* succeeds iff the hold clears the submarine's length by at
      least ``bay.clearance_m``.

    Only two of the four stages therefore carry a discriminating predicate,
    and both are pure geometry. The run's ``success`` is exactly the *secure*
    predicate, reached only when ingress passed.

    A stage that fails terminates the run (no later phases are recorded) and
    marks ``success = False``. Phase timings come from the declared nominal
    schedule in :data:`_PHASE_DURATIONS`; see its comment before reading any
    duration as a result.
    """
    c = clearance_metrics(submarine, bay)
    records: list[PhaseRecord] = []

    def add(phase: CapturePhase, ok: bool, note: str = "") -> bool:
        start = records[-1].end_s if records else 0.0
        records.append(_phase(phase, start, _PHASE_DURATIONS[phase], ok, note))
        return ok

    # Approach: controlled approach under tow.
    add(CapturePhase.APPROACH, True, "bay under tow control; approach nominal")
    # Ingress: the mouth must clear beam and depth with the safety margin.
    mouth_ok = c.beam_clearance_m >= bay.clearance_m and c.depth_clearance_m >= bay.clearance_m
    if not add(
        CapturePhase.INGRESS,
        mouth_ok,
        "mouth clearance satisfied" if mouth_ok else "mouth clearance insufficient",
    ):
        return CaptureRun(submarine, bay, tuple(records), success=False)
    # Hatch seal: requires a geometrically successful ingress. No seal
    # integrity is computed anywhere in this package, so there is nothing
    # else for this phase to test.
    add(CapturePhase.HATCH_SEAL, True, "hatch closes; seal integrity not modelled")
    # Secure: only if the sub fits the hold lengthwise with the safety margin.
    hold_ok = c.length_clearance_m >= bay.clearance_m
    add(
        CapturePhase.SECURE,
        hold_ok,
        "hold length clearance satisfied" if hold_ok else "hold length clearance insufficient",
    )
    return CaptureRun(submarine, bay, tuple(records), success=hold_ok)
