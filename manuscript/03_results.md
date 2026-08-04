# Results {#sec:results}

All numbers in this section are computed live by the deterministic domain
core; the simulator is seeded so the outputs are reproducible exactly.

## Passive tracking

The canonical scenario observes a constant-velocity submarine over
{{SUB_NUM_BEARINGS}} bearing samples. Batch target motion analysis recovers
the quarry's initial position to within {{SUB_TRACK_POS_ERR_M}} metres of
truth — well inside the operating envelope of the tracking geometry.
@fig:bearing_track overlays the true trajectory, the TMA estimate, and the
maneuvering ownship path.

![Passive bearing-only tracking: true track vs TMA estimate and ownship path.](../output/figures/bearing_track.png){#fig:bearing_track}

## Liparus capture

For a bay whose hold is {{TANKER_HOLD_LENGTH_M}} metres long with a
{{TANKER_MOUTH_WIDTH_M}}-metre mouth and a required clearance of
{{TANKER_CLEARANCE_M}} metres, the canonical swallow completes in
{{TANKER_CAPTURE_TIME_S}} seconds and stows {{TANKER_STOWAGE}} submarine(s)
per pass. @fig:capture_feasibility shows the per-axis clearance margins
across a sweep of submarine sizes.

![Liparus dock-mouth feasibility by submarine size.](../output/figures/capture_feasibility.png){#fig:capture_feasibility}

## Vehicle conversion forensics

The Lotus-Esprit-grade conversion spec achieves a readiness score of
{{FORENSICS_SCORE}} and is classified **{{FORENSICS_CLASS}}** with
{{FORENSICS_MISSING_CRITICAL}} missing critical systems.
@fig:conversion_readiness renders the requirement traceability across the
canonical road-car, amphibious, and submersible grades.

![Submersible conversion readiness by requirement.](../output/figures/conversion_readiness.png){#fig:conversion_readiness}

## Mission outcome

The `MissionProvider` execute stage runs all four algorithms and returns a
deterministic `MissionOutcome` whose `success` flag is true only when the
contact is detected and the capture succeeds, together with full
`Provenance` (package version, seed, input hash).
