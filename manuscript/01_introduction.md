# Introduction

In *The Spy Who Loved Me* (1977), Bond confronts two icons of hydraulic
malevolence and mechanical possibility: the *Liparus*, a supertanker whose
hull opens like a mouth to swallow whole submarines, and the Lotus Esprit, a
road car that converts into a functional submersible. Both demand the same
kind of engineering reasoning that a special-agent mission plan needs: detect
the unseen contact, reason about capture geometry, and verify that a vehicle
can actually survive underwater.

This package — mission codename {{LIPARUS_CODENAME}} — realises those three
capabilities as deterministic, testable software. It is one package in the
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
| `mission.py` | Frozen `bond_api.MissionProvider` adapter + gadget registry |

The remainder of this manuscript describes the algorithms (Section
@sec:methodology), their measured results (Section @sec:results), and the
deterministic experimental setup (Section @sec:setup).
