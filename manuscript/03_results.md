# Results {#sec:results}

All numbers in this section are computed live by the deterministic domain
core (the canonical scenario); the simulator is seeded so the outputs are
reproducible exactly.

## Passive tracking

The canonical scenario observes a constant-velocity submarine over
{{SUB_NUM_BEARINGS}} bearing samples. Batch target motion analysis recovers
the quarry's initial position to within {{SUB_TRACK_POS_ERR_M}} metres of
truth (velocity error {{SUB_TRACK_VEL_ERR_M_S}} m/s) — well inside the
operating envelope of the tracking geometry. @fig:bearing_track overlays the
true trajectory, the TMA estimate, and the maneuvering ownship path.

![Passive bearing-only tracking: true track vs TMA estimate and ownship path.](../output/figures/bearing_track.png){#fig:bearing_track}

## Passive sonar equation

Against the canonical budget the passive sonar equation returns a detection
range of {{ACO_DETECTION_RANGE_M}} metres (figure of merit {{ACO_FOM_DB}} dB)
in a channel whose sound speed is {{ACO_SOUND_SPEED_M_S}} m/s and whose
absorption is {{ACO_ABSORPTION_DB_KM}} dB/km at the 400 Hz scan tone.
@fig:sonar_detection_range shows how the solved range grows with the
contact's source level.

![Passive sonar detection range vs source level.](../output/figures/sonar_detection_range.png){#fig:sonar_detection_range}

## Beamforming

The {{BEAM_NUM_ELEMENTS}}-element ULA estimates the contact bearing to
{{BEAM_BEARING_ERR_DEG}} degrees of the true bearing (estimate
{{BEAM_ESTIMATE_DEG}} degrees), against a Cramer-Rao floor of
{{BEAM_CRB_DEG}} degrees — the estimator is at the theoretical limit of
precision for the array geometry and SNR. @fig:beamforming_response shows
the beamformer power response with the true and estimated bearings marked.

![ULA beamformer response vs bearing.](../output/figures/beamforming_response.png){#fig:beamforming_response}

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
Physically, the {{HULL_OPERATING_DEPTH_M}}-metre operating hull collapses
only at {{HULL_COLLAPSE_DEPTH_M}} metres (safety factor
{{HULL_SAFETY_FACTOR}}, feasibility {{HULL_FEASIBLE}}), and reaching neutral
buoyancy calls for {{BALLAST_VOLUME_L}} L of ballast water.

![Submersible conversion readiness by requirement.](../output/figures/conversion_readiness.png){#fig:conversion_readiness}

## Mission outcome

The `MissionProvider` execute stage runs all six concept modules against the
canonical scenario and returns a deterministic `MissionOutcome` whose
`success` flag is true only when the contact is detected, the capture
succeeds, and the hull is feasible at operating depth, together with full
`Provenance` (package version, seed, input hash).
