# Scope and related work

## Scope

This package models *detection*, *tracking*, *capture geometry*, and
*conversion forensics* at a level appropriate to deterministic,
reproducible research software. It does not model hydrodynamics, propeller
cavitation spectra, real acoustic channel propagation, or structural
after-dive defects; those remain future extensions. The bearing-only tracker
assumes an ideal constant-velocity target and a precisely known ownship
path.

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
* **Discrete-event simulation** of the capture phase draws on standard
  queueing/event-sequence practice.
* **Requirement traceability** and Archimedean **buoyancy feasibility** are
  the chapter-and-verse of naval-architecture conversion analysis.

The novelty here is not the individual algorithms but their assembly into a
deterministic, protocol-adapter mission package whose claims are all
code-generated.
