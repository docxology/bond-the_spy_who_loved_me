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
Gauss–Newton. `PassiveBearingTracker` is the matching recursive Extended
Kalman Filter for online use, with the relative-bearing measurement model and
a constant-velocity transition. `tracking_rms_error` reports steady-state
accuracy.

## Liparus-class tanker capture

`src/the_spy_who_loved_me/tanker_capture.py` models the *Liparus* swallowing
a submarine as a deterministic geometric-feasibility check plus a
discrete-event sequence. `clearance_metrics` computes the per-axis margins
between a `SubmarineSpec` and a `BayConfig` mouth/hold, and
`classify_clearance` labels the fit `fits` / `tight` / `denied` against a
required safety margin. `stowage_capacity` is how many submarines the hold
can stow. `simulate_capture` runs the four-phase operation (approach,
ingress, hatch-seal, secure), each phase decided by a fixed predicate, and
returns a `CaptureRun` with a per-phase timeline and final status.

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
The passive sonar equation ``SNR = SL - TL - (NL - DI) - DT``
(`passive_sonar_equation`) is the detection budget, and
`detection_range_m` solves for the maximum detectable range by monotone
bisection of the strictly-increasing transmission loss.

## Uniform-linear-array beamforming

`src/the_spy_who_loved_me/beamforming.py` turns the array's raw snapshots
into a bearing. `steering_vector` gives the plane-wave phase progression
``a(theta) = exp(-j 2 pi (d/lambda) k sin(theta))``; `array_snapshot`
produces a deterministic seeded snapshot; the conventional (delay-and-sum)
beamformer ``P(theta) = |a(theta)^H x|^2`` (`beam_power`) is scanned by
`estimate_bearing_deg` to locate the contact. `cramer_rao_bearing_std_deg`
reports the Cramer-Rao lower bound on the bearing estimate — the theoretical
floor the estimator cannot beat (Van Trees, *Optimum Array Processing*).

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

## Mission orchestration

`src/the_spy_who_loved_me/mission.py` adapts the six domain modules to the
frozen `bond_api` protocol: it implements `MissionProvider` (brief, recon,
plan, execute, debrief) with a fixed seed, exposes deterministic results
(with a validated collapse-depth safety factor) with full `Provenance`, and
registers the concept functions as gadgets on a `GadgetRegistry`.
