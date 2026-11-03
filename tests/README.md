# tests/ — the suite, and the gates that keep the prose honest

One module per domain concept, plus the adapter, the canonical scenario, the manuscript tokens, the
figures, the CLIs — and `test_repo_contracts.py`, which binds the package's documentation to the
package itself. Everything here runs on real computation with real data; the doctrine is in
[`docs/testing_philosophy.md`](../docs/testing_philosophy.md).

| Module | Subject |
| --- | --- |
| `test_sub_tracking.py` | Passive acoustic detection and bearing-only tracking: the energy detector, batch least-squares target-motion analysis, the extended Kalman filter |
| `test_tanker_capture.py` | Liparus capture geometry and the discrete-event capture simulation |
| `test_vehicle_forensics.py` | Conversion requirement traceability, readiness scoring, Archimedean buoyancy feasibility |
| `test_acoustics.py` | Thorp absorption, spreading loss, the passive sonar equation, the detection-range solve, Mackenzie sound speed |
| `test_beamforming.py` | Steering vectors, the delay-and-sum beamformer, peak-search bearing estimation, and the grid-quantisation property that makes the canonical bearing error what it is |
| `test_hull_forensics.py` | Hoop stress, elastic buckling, governing collapse pressure and depth, ballast volume |
| `test_scenario.py` | The canonical scenario as the single source of truth |
| `test_mission.py` | The provider against the frozen protocol |
| `test_manuscript_variables.py` | Token hydration and the token cross-reference |
| `test_figures.py` | Real rendering on a headless backend |
| `test_scripts_smoke.py` | The CLIs, in subprocesses |
| `test_repo_contracts.py` | The documentation gates described below |

## The documentation gates

`test_repo_contracts.py` exists because a prose claim in this tree was false while every test was green.
Each assertion names the claim it guards, and is written so that restoring the false state turns it red:

- **One version, declared once.** `pyproject.toml` is the authority; the other declaration sites must
  agree with it.
- **The layer contract is read by a gate.** `manuscript/layer_contract.yaml` is a machine-readable
  statement of which module may import what, and the pure core is checked against it — neither the
  protocol nor infrastructure may appear there, and only the adapter may import `bond_api`.
- **The figure registries are complete in both directions.** `experiment_plan.yaml` and
  `domain_profile.yaml`, the manuscript's figure references, and the figures the code produces must all
  describe the same set.
- **No document claims a publication location this package does not have**, and the documents do name
  the one location it really has.
- **No exemplar boilerplate survives** in prose.
- **Hardcoded prose figures match the run.** The root guide states the beamformer scan grid and the
  canonical true bearing as literals; the gate recomputes both from the canonical scenario.
- **The claim ledger is real.** Its `source` paths and symbols must exist and its values must match a
  run of the models.
- **The scan set is pinned, with a positive control**, so none of the above can pass by scanning
  nothing. A document added to this package joins that scan set.

## Where to go next

[`docs/testing_philosophy.md`](../docs/testing_philosophy.md) for the doctrine; `conftest.py` for the
headless backend and the `src/` path insert; the root guide's "Known modelling caveats" before treating
any number here as a result rather than a first-order model output.
