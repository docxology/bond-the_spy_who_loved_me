# Methodology {#sec:methodology}

## Passive acoustic detection and bearing-only tracking

`src/the_spy_who_loved_me/sub_tracking.py` models the sensor problem of a
passive array hunting a submarine that emits nothing deliberately.

**Detection** uses a Neyman–Pearson energy detector
(`detect_contract`). A received waveform is split into non-overlapping
windows; each window statistic `T = sum(x^2)/noise_var` is compared against a
threshold. Under the noise-only hypothesis `T ~ chi^2(window)`, so the
threshold is the `(1 - P_FA)`-quantile of that chi-square distribution,
computed in closed form with the Wilson–Hilferty approximation
(`chi2_quantile`), whose standard-normal-quantile primitive is Acklam's
algorithm (`inverse_normal_cdf`). The detector therefore makes its decision
at a controlled false-alarm probability `P_FA`, and `Detection.margin_db`
reports the statistic-to-threshold margin.

**Tracking** is the harder problem. `simulate_target_track` generates a
deterministic scenario: a constant-velocity submarine observed by a
*maneuvering* ownship (a dogleg course change), yielding noisy relative
bearings. The maneuver is not cosmetic — a fundamental result of passive
sonar is that a constant-velocity target's absolute range and speed are
*unobservable* from a stationary observer (the whole trajectory can be
scaled and produce identical bearings). Only a change of observer course
renders the state observable.

`estimate_tma` then performs batch least-squares target motion analysis:
over the state `[px, py, vx, vy]` it minimises the sum of squared bearing
residuals
`sum_i (bearing_i - atan2(p_y + v_y t_i - o_y, p_x + v_x t_i - o_x))^2`,
initialised by a coarse grid search over range/course/speed and refined by
Gauss–Newton.

That grid search is **bounded, and its bounds bracket the canonical
scenario**: candidate initial ranges run 3000–6500 m in 500 m steps and
candidate speeds 5–35 m/s in 5 m/s steps, against a canonical truth of
4000 m and 25 m/s. This is a declared search envelope, not a property of the
estimator, and canonical accuracy is therefore not evidence about arbitrary
geometry. The degradation outside it is graceful rather than a cliff — with
only the initial range varied, a 15 km target is still recovered to 293 m
because Gauss–Newton escapes the poor seed, while a 60 km target leaves a
25 km error (42% of range) that widening the range bound to 80 km cuts to
4.9 km. `estimate_tma` accepts keyword overrides for the envelope, and
`tests/test_sub_tracking.py::TestCoarseSearchEnvelope` pins all three of
those measurements.

`PassiveBearingTracker` is the matching recursive Extended Kalman Filter for
online use, with the relative-bearing measurement model and a
constant-velocity transition; its `measurement_noise_rad` is a bearing
standard deviation and is squared into the measurement covariance `R`.
`tracking_rms_error` reports steady-state accuracy.

## Liparus-class tanker capture

`src/the_spy_who_loved_me/tanker_capture.py` models the *Liparus* swallowing
a submarine as a deterministic geometric-feasibility check plus a
discrete-event sequence. `clearance_metrics` computes the per-axis margins
between a `SubmarineSpec` and a `BayConfig` mouth/hold, and
`classify_clearance` labels the fit `fits` / `tight` / `denied` against a
required safety margin. `stowage_capacity` is how many submarines the hold
can stow. `simulate_capture` runs the four-phase operation (approach,
ingress, hatch-seal, secure) and returns a `CaptureRun` with a per-phase
timeline and final status.

Only two of those four phases test anything. *Ingress* requires the mouth to
clear the submarine's beam and depth by the safety margin, and *secure*
requires the hold to clear its length by the same margin; *approach* and
*hatch-seal* always succeed. No seal-integrity quantity is modelled anywhere
in the package, so the hatch-seal stage has nothing of its own to check — a
`seal_requirement` field on `BayConfig` supplied the appearance of one until
it was removed, because the constructor validated it into `[0, 1]` and the
predicate then compared it against `1.0`, a conjunct that could never be
false. The per-phase durations are likewise declared constants, not a timing
model; Section @sec:results says what that means for the reported elapsed
time.

## Submersible vehicle forensics

`src/the_spy_who_loved_me/vehicle_forensics.py` forensically assesses
whether a road vehicle can be converted to submersible duty.
`SUBMERSIBLE_REQUIREMENTS` is a traced requirement set (pressure hull,
watertight seals, ballast, air supply, and optional systems). `assess_conversion`
scores the spec, `classify_conversion` maps the result to `road-only`,
`amphibious`, or `submersible`, and `recommend_upgrades` returns the missing
critical systems as an ordered retrofit list. `buoyancy_status` applies
Archimedes' principle (`F_b = displacement * rho_water * g` vs weight) to
classify the as-spec vehicle `floats` / `neutral` / `sinks`.

## Underwater acoustics and the passive sonar equation

`src/the_spy_who_loved_me/acoustics.py` puts numbers on the *medium* the
Liparus and its quarry move through. `thorp_absorption` implements the Thorp
(1967) seawater absorption coefficient, ``transmission_loss`` combines
geometric spreading with absorption to give ``TL(r) = n*10*log10(r) +
alpha*r``, and `sound_speed_m_s` implements the Mackenzie (1981) equation.
The passive sonar equation in signal-excess form
``SE = SL - TL - (NL - DI) - DT`` (`passive_sonar_equation`) is the detection
budget, and `detection_range_m` solves for the maximum detectable range by
monotone bisection of the strictly-increasing transmission loss — the range
at which the signal excess reaches zero.

Signal excess is not the signal-to-noise ratio, and the two are kept apart
here because this package previously called the quantity above an SNR in
code, prose and test names. Following Urick [@urick_principles_1983], the
array-output SNR is ``SL - TL - (NL - DI)`` — larger than the signal excess
by exactly the detection threshold ``DT``, and available as
`signal_to_noise_ratio_db`. With the canonical budget the difference is
{{ACO_DETECTION_THRESHOLD_DB}} dB, so calling the figure of merit an SNR
overstates the margin by that much.

## Uniform-linear-array beamforming

`src/the_spy_who_loved_me/beamforming.py` turns the array's raw snapshots
into a bearing. `steering_vector` gives the plane-wave phase progression
``a(theta) = exp(-j 2 pi (d/lambda) k sin(theta))``; `array_snapshot`
produces a deterministic seeded snapshot; the conventional (delay-and-sum)
beamformer ``P(theta) = |a(theta)^H x|^2`` (`beam_power`) is scanned by
`estimate_bearing_deg` to locate the contact. `cramer_rao_bearing_std_deg`
reports the Cramer-Rao lower bound on the bearing estimate — the theoretical
floor the estimator cannot beat (Van Trees, *Optimum Array Processing*
[@van_trees_2002]).

Two properties of this estimator matter for reading Section @sec:results.
First, the peak search runs over a *discrete* grid, so the estimate is
quantised to the grid step and its measured error is floored at half a step
regardless of array quality — the statistical bound reported by the CRB and
the error achievable on this grid are different quantities, and on this
scenario the latter is the binding one. Second, the element SNR passed to
the CRB is derived in `scenario.py` from the snapshot amplitude and noise
standard deviation rather than declared independently, so the bound always
describes the array that was in fact sampled.

## Pressure-hull and ballast forensics

`src/the_spy_who_loved_me/hull_forensics.py` checks that the converted
vehicle can actually dive. `hoop_stress_pa` evaluates the circumferential
stress ``sigma = p r / t``; `elastic_buckling_pressure_pa` gives the
long-cylinder buckling pressure ``p_cr = E (t/r)^3 / (4(1-nu^2))`` and
`yield_pressure_pa` the strength limit ``p_y = sigma_y t / r``;
`collapse_depth_m` is the governing (minimum) collapse pressure expressed as
a depth in seawater. `ballast_volume_m3` applies Archimedes to find the
flood-water volume needed for neutral buoyancy — the threshold between a
road car and a submarine.

Flooding a tank adds mass at constant displaced volume, so neutral buoyancy
is `D rho g = (m + V rho) g`, giving `V = D - m/rho`: positive when the
vehicle displaces more than it weighs and must be made heavier to dive,
negative when it is already denser than the water it displaces. The
module's published derivation previously read `(D + V) rho g = m g`, which
solves to the negation of what the code computes, and read the negative case
backwards as well. The code was right and the derivation wrong; the
derivation is corrected rather than the code. `vehicle_forensics.buoyancy_status`
uses the same seawater density as this module, so the two verdicts on one
vehicle describe one fluid — it used fresh water at 1000 kg/m³ until this was
fixed.

## Mission orchestration

`src/the_spy_who_loved_me/mission.py` adapts the six domain modules to the
frozen `bond_api` protocol: it implements `MissionProvider` (brief, recon,
plan, execute, debrief) with a fixed seed, exposes deterministic results
(with a validated collapse-depth safety factor) with full `Provenance`, and
registers the concept functions as gadgets on a `GadgetRegistry`.
