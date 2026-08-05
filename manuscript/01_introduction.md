# Introduction

In *The Spy Who Loved Me* (1977), Bond confronts two icons of hydraulic
malevolence and mechanical possibility: the *Liparus*, a supertanker whose
hull opens like a mouth to swallow whole submarines, and the Lotus Esprit, a
road car that converts into a functional submersible. Both demand the same
kind of engineering reasoning that a special-agent mission plan needs: detect
the unseen contact, reason about capture geometry, and verify that a vehicle
can actually survive underwater.

This package — mission codename {{LIPARUS_CODENAME}} — realises those
capabilities as deterministic, testable software across
{{NUM_CONCEPT_MODULES}} concept modules. It is one package in the
PROJECT BOND suite, a set of film-themed mission packages made compatible by
the frozen `bond_api` mission protocol. The domain core is deliberately
independent of that protocol: the pure modules in
`src/the_spy_who_loved_me/` compute results with no knowledge of any
orchestrator, and the thin `mission.py` adapter in the same package exposes
them under the standard five-stage lifecycle (brief, recon, plan, execute,
debrief).

The structure of the package is:

| Module | Concept |
|---|---|
| `sub_tracking.py` | Passive acoustic detection and bearing-only tracking |
| `tanker_capture.py` | Liparus-class tanker swallowing-submarine simulation |
| `vehicle_forensics.py` | Submersible vehicle conversion forensics |
| `acoustics.py` | Underwater propagation and the passive sonar equation |
| `beamforming.py` | Uniform-linear-array beamforming and bearing estimation |
| `hull_forensics.py` | Pressure-hull collapse and ballast analysis |

Three further modules carry no domain concept of their own but hold the
package together: `scenario.py` is the single canonical parameter set and
metric factory that both the mission adapter and the manuscript hydration
consume (so an outcome and a printed number cannot disagree),
`manuscript_variables.py` turns those metrics into the substitution tokens
this document is written in, and `mission.py` is the thin frozen
`bond_api.MissionProvider` adapter plus gadget registry.

The six concepts compose rather than sit side by side: `acoustics.py` sets
the detection budget that says whether a contact is audible at all,
`sub_tracking.py` decides whether it *was* heard and where it is going,
`beamforming.py` converts the array's raw snapshot into the bearing that
tracking consumes, `tanker_capture.py` asks whether the quarry physically
fits inside the Liparus, and `vehicle_forensics.py` and `hull_forensics.py`
together answer the Lotus Esprit question from two sides — paperwork
(requirement traceability) and physics (collapse depth and ballast).

The remainder of this manuscript describes the algorithms (Section
@sec:methodology), their measured results (Section @sec:results), and the
deterministic experimental setup (Section @sec:setup).
