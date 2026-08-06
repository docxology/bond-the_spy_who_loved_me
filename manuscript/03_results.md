# Results {#sec:results}

All numbers in this section are hydrated from the deterministic domain core
(the canonical scenario); the simulator is seeded so the outputs are
reproducible exactly. One of them — the capture timeline under *Liparus
capture* — is a **declared constant** rather than a computed quantity, and is
labelled as such where it appears. The rest are measured.

## Detection

The Neyman-Pearson energy detector is the gate the whole
downstream tracking chain stands behind: every conclusion below presupposes a
contact was heard at all. On the canonical waveform the detector declares the
contact **{{DETECTED}}**, with a statistic-to-threshold margin of
{{DETECTION_MARGIN_DB}} dB at a false-alarm probability of {{DETECTION_P_FA}}.
The margin is the number that matters operationally — how far the peak energy
statistic sits above the threshold the detector was asked to hold — and the
false-alarm probability is the operating point it was required to meet. No
other number in this section is meaningful if that predicate is false.

## Passive tracking

The canonical scenario observes a constant-velocity submarine over
{{SUB_NUM_BEARINGS}} bearing samples. Batch target motion analysis recovers
the quarry's initial position to within {{SUB_TRACK_POS_ERR_M}} metres of
truth (velocity error {{SUB_TRACK_VEL_ERR_M_S}} m/s) — well inside the
operating envelope of the tracking geometry.

The matching recursive extended Kalman filter runs the *same* bearing
sequence and settles to a steady-state position error of
{{SUB_TRACK_EKF_RMS_M}} metres. The two numbers are not competing claims but
one pipeline at two latencies: the batch estimate is the offline maximum-likelihood
answer (here the tighter of the two), while the filter is what a real receiver
could produce in real time as the bearings arrive. @fig:bearing_track overlays
the true trajectory, the TMA estimate, and the maneuvering ownship path.

![Passive bearing-only tracking: true track vs TMA estimate and ownship path.](../output/figures/bearing_track.png){#fig:bearing_track}

## Passive sonar equation

Against the canonical budget the passive sonar equation returns a detection
range of {{ACO_DETECTION_RANGE_M}} metres (figure of merit {{ACO_FOM_DB}} dB)
in a channel whose sound speed is {{ACO_SOUND_SPEED_M_S}} m/s and whose
absorption is {{ACO_ABSORPTION_DB_KM}} dB/km at the {{ACO_FREQ_HZ}} Hz scan
tone.
@fig:sonar_detection_range shows how the solved range grows with the
contact's source level.

![Passive sonar detection range vs source level.](../output/figures/sonar_detection_range.png){#fig:sonar_detection_range}

## Beamforming

The {{BEAM_NUM_ELEMENTS}}-element ULA estimates the contact bearing at
{{BEAM_ESTIMATE_DEG}} degrees, {{BEAM_BEARING_ERR_DEG}} degrees from truth,
against a Cramer-Rao floor of {{BEAM_CRB_DEG}} degrees.

That measured error must be read carefully rather than as a precision claim.
`estimate_bearing_deg` is a peak search over a discrete scan grid of
{{BEAM_SCAN_STEP_DEG}} degrees, so its output is quantised and its error
cannot exceed {{BEAM_QUANTISATION_FLOOR_DEG}} degrees for any snapshot whose
peak lands in the correct cell — *including* an error of exactly zero when,
as in the canonical scenario, the true bearing
({{BEAM_TRUE_BEARING_DEG}} degrees) falls on a grid node. A reported error
below the Cramer-Rao bound is therefore an artefact of grid alignment, not
evidence that the estimator beats the statistical floor, which no unbiased
estimator can do. The honest statement is the two-sided one: the beamformer
resolves the contact to within one scan cell, and the CRB of
{{BEAM_CRB_DEG}} degrees — finite and comfortably below the
{{BEAM_SCAN_STEP_DEG}}-degree grid — says the array geometry and SNR would
support a finer estimate than this grid can express.
`tests/test_beamforming.py` pins the quantisation property on *off-grid*
bearings, where the artefact cannot hide it. The opt-in parabolic refinement
(`estimate_bearing_deg(..., interpolate=True)`) exists precisely to approach
the CRB rather than stay floored at the grid: it fits a parabola through the
peak node and its neighbours and reports the apex. On the canonical (grid
aligned) true bearing the grid reports an error of exactly zero — a
snapshot-noise artefact of the node landing on the truth — while the refined
estimate settles at {{BEAM_BEARING_ERR_INTERP_DEG}} degrees, a sub-cell
residual it can actually achieve against the {{BEAM_CRB_DEG}} degree floor.
The two errors are therefore reported as what they are: the grid figure is
what this grid commits the estimator to, the refined figure is what the
estimator itself can reach, and the off-grid tests in `test_beamforming.py`
show the refinement strictly beating the grid where the grid is genuinely
limited. @fig:beamforming_response shows the beamformer power response with
the true and estimated bearings marked.

![ULA beamformer response vs bearing.](../output/figures/beamforming_response.png){#fig:beamforming_response}

## Liparus capture

For a bay whose hold is {{TANKER_HOLD_LENGTH_M}} metres long with a
{{TANKER_MOUTH_WIDTH_M}}-metre mouth and a required clearance of
{{TANKER_CLEARANCE_M}} metres, the canonical swallow succeeds and stows
{{TANKER_STOWAGE}} submarine(s) per pass. @fig:capture_feasibility shows the
per-axis clearance margins across a sweep of submarine sizes.

The capture model reports an elapsed time of {{TANKER_CAPTURE_TIME_S}}
seconds over {{TANKER_PHASES_RUN}} phases, and that number is **not a
result**. It is the sum of four fixed per-phase durations declared in
`tanker_capture._PHASE_DURATIONS` — assumptions with no cited source and no
timing model behind them. Nothing in the simulation makes a phase duration
depend on the submarine or the bay, so the total is identical for a 10-metre
boat and a 72-metre one, and identical for a capture that succeeds and one
that fails at the *secure* stage. The only thing it varies with is how far
the operation got before aborting: a run that fails at ingress reports two
phases instead of four. `tests/test_tanker_capture.py::TestReportedTimeIsASchedule`
pins exactly those properties rather than pinning the total, which would have
been a constant dressed as a measurement.

Two of the four phases likewise carry no discriminating predicate. *Approach*
always succeeds, and *hatch-seal* succeeds whenever ingress did, because no
seal-integrity quantity is modelled anywhere in the package. The feasibility
verdict is therefore pure geometry: mouth clearance at ingress, hold-length
clearance at secure.

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
`Provenance` (package version, seed, input hash). The input hash is a
SHA-256 over the canonical parameter set, so it moves when any input does —
see Section @sec:reproducibility, which also records what it used to be.
