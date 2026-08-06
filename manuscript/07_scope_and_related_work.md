# Scope and related work

## Scope

This package models *detection*, *tracking*, *bearing estimation*,
*propagation*, *capture geometry*, and *conversion forensics* at a level
appropriate to deterministic, reproducible research software. Each model is
first-order by design, and the boundaries are worth stating precisely
because they are where the results stop being trustworthy:

* **Propagation** is a range-independent budget: geometric spreading plus
  Thorp absorption. There is no sound-speed profile, no ray tracing, no
  surface/bottom interaction, no convergence zones and no shadow zones — so
  the solved detection range is an upper bound in an idealised channel, not
  a field prediction.
* **Tracking** assumes an ideal constant-velocity target and a precisely
  known ownship path. Neither manoeuvring targets nor navigation error are
  modelled. The recursive EKF shares both assumptions and adds its own: a fixed
  (white) process noise and a fixed bearing-noise variance, so its steady-state
  error is a statement about that ideal filter on that ideal trajectory, not
  about a real receiver.
* **Detection** is a fixed-threshold Neyman-Pearson energy detector over
  zero-mean Gaussian noise: no fluctuating target, no multipath fading, no
  signal-correlated noise, no non-stationary ambient levels. The reported
  `P_FA` and margin are therefore a *controlled but idealised* operating
  point, not a detection probability in a real noise field.
* **Beamforming** is conventional delay-and-sum on a single snapshot: no
  adaptive (MVDR/MUSIC) processing, no multipath, no coherent multi-snapshot
  averaging. The grid bearing is quantised to the scan step; the parabolic
  refinement is a local quadratic fit that *approaches* the Cramer-Rao bound
  but cannot reach the true CRB performance of an optimal estimator on finite
  data, and the two are reported separately for exactly that reason.
* **Hull analysis** treats an unstiffened long cylinder under uniform
  external pressure. Ring stiffening, end-cap effects, out-of-roundness and
  weld/fatigue defects — the things that actually govern a real submersible
  — are outside the model.
* **Capture** is a geometric-clearance and discrete-event feasibility check.
  Hydrodynamics, wake interaction, mooring loads and propeller cavitation
  spectra are not modelled.

Structural after-dive defect analysis remains a future extension.

## Related work

* **Neyman–Pearson detection** and the **Wilson–Hilferty** chi-square
  approximation are standard signal-detection results (Kay, *Fundamentals of
  Statistical Signal Processing: Detection Theory*).
* **Bearing-only target motion analysis** and the observer-maneuver
  observability requirement are established passive-sonar results (Nardone &
  Aidala, "Observability criteria for bearings-only target motion
  analysis").
* **Extended Kalman filtering** follows the canonical state-estimation
  treatment (Anderson & Moore, *Optimal Filtering*).
* **Underwater propagation and the passive sonar equation** follow Urick,
  *Principles of Underwater Sound* [@urick_principles_1983]; the absorption
  coefficient is Thorp's low-frequency expression [@thorp_1967] and the
  sound speed is Mackenzie's nine-term equation [@mackenzie_1981].
* **Array processing** — the ULA steering vector, the conventional
  delay-and-sum beamformer, and the Cramer-Rao bound on bearing — is Van
  Trees, *Optimum Array Processing* [@van_trees_2002].
* **Elastic buckling of a long cylinder under external pressure**, the
  expression that governs the collapse depth here, is Timoshenko & Gere,
  *Theory of Elastic Stability* [@timoshenko_gere_1961]; the thin-wall
  hoop-stress relation is standard [@young_roark_2011].
* **Discrete-event simulation** of the capture phase draws on standard
  queueing/event-sequence practice.
* **Requirement traceability** and Archimedean **buoyancy feasibility** are
  the chapter-and-verse of naval-architecture conversion analysis
  [@tupper_naval_2013].

The novelty here is not the individual algorithms but their assembly into a
deterministic, protocol-adapter mission package whose claims are all
code-generated.
