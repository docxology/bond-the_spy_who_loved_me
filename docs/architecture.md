# Architecture — LIPARUS

Module-by-module structure of `src/the_spy_who_loved_me/`, how the pieces
compose, and how `mission.py` implements the frozen `bond_api`
`MissionProvider`.

## Shape

```
scripts/                              thin CLIs — argv shaping and printing only
  mission_cli.py                        drive the five mission phases
  generate_figures.py                   render the five concept figures
  z_generate_manuscript_variables.py    hydrate tokens, resolve manuscript tree
        │
        ▼
src/the_spy_who_loved_me/
  ── six pure concept modules (no bond_api, no infrastructure) ──
  acoustics.py            propagation + passive sonar equation
  sub_tracking.py         energy detection + bearing-only TMA + EKF
  beamforming.py          ULA steering, delay-and-sum, bearing, CRB
  tanker_capture.py       clearance geometry + discrete-event capture
  vehicle_forensics.py    requirement traceability + Archimedean buoyancy
  hull_forensics.py       hoop stress, buckling, collapse depth, ballast
  ── composition and presentation ──
  scenario.py             canonical parameters + run_canonical() metric factory
  manuscript_variables.py token hydration from scenario + config + pyproject
  figures/plots.py        five deterministic matplotlib figures
  ── protocol boundary ──
  mission.py              bond_api adapter: MissionProvider + GADGETS
        │
        ▼
  bond_api  (path dependency — the frozen protocol)
```

The dependency arrow never reverses. Nothing in `src/` imports `scripts/`;
no concept module imports `mission.py`; no module anywhere imports
`infrastructure`.

## What each module computes

### The six concept modules

**`acoustics.py`** — the medium. `thorp_absorption` gives the Thorp (1967)
seawater absorption coefficient in dB/km; `transmission_loss` adds geometric
spreading to it as `TL(r) = n*10*log10(r) + alpha*r`, with `n = 2` spherical
or `1` cylindrical; `sound_speed_m_s` is Mackenzie's (1981) nine-term
equation in temperature, salinity and depth. `figure_of_merit_db` computes
`FOM = SL - (NL - DI) - DT` and `passive_sonar_equation` subtracts the
transmission loss from it to give the **signal excess** — not the SNR, which
is larger by the detection threshold and is available separately as
`signal_to_noise_ratio_db`. (The package called signal excess an SNR in its
code, prose and test names until that was corrected;
`PropagationResult.snr_db` became `signal_excess_db`.) `detection_range_m`
solves `TL(r) = FOM` by bisection — valid because `TL` is strictly increasing
in `r`, so the root is unique — and returns a `PropagationResult` that
reports `converged=False` when the contact is inaudible even at one metre.

**`sub_tracking.py`** — the largest module, and the sensor problem proper.
`detect_contract` is a Neyman–Pearson energy detector: it windows the
waveform, forms `T = sum(x^2)/sigma^2` per window, and compares against the
`(1 - P_FA)`-quantile of a chi-square with `window` degrees of freedom. That
quantile comes from `chi2_quantile` (Wilson–Hilferty) over
`inverse_normal_cdf` (Acklam), both in closed form, so detection needs no
scipy and no tables. `simulate_signal` synthesises a seeded waveform;
`simulate_target_track` builds a constant-velocity target observed by a
*manoeuvring* ownship on a dogleg. The manoeuvre is load-bearing, not
decoration: a constant-velocity target's absolute range and speed are
unobservable from a straight-running observer, because scaling the whole
geometry produces identical bearings. `estimate_tma` does batch
least-squares target motion analysis over the state `[px, py, vx, vy]`,
seeded by a coarse range/course/speed grid search and refined by
Gauss–Newton. That grid is a **bounded envelope** (3000-6500 m, 5-35 m/s by
default, overridable per call) which brackets the canonical scenario, so
canonical accuracy says nothing about arbitrary geometry — see the caveat in
[`../AGENTS.md`](../AGENTS.md). `PassiveBearingTracker` is the recursive EKF
equivalent for online use — its `measurement_noise_rad` is a standard
deviation and is squared into the covariance `R` — and `tracking_rms_error`
scores either.

**`beamforming.py`** — where the contact *is*. `steering_vector` is the
plane-wave phase progression `a(theta) = exp(-j 2 pi (d/lambda) k sin
theta)`; `array_snapshot` draws a seeded complex snapshot; `beam_power`
evaluates the conventional delay-and-sum response `P(theta) = |a(theta)^H
x|^2`; `estimate_bearing_deg` takes its peak over a scan grid;
`cramer_rao_bearing_std_deg` reports the statistical floor. Note the peak
search is a **grid** search, so its output is quantised — see the caveat in
[`AGENTS.md`](AGENTS.md) and Section 3 of the manuscript.

**`tanker_capture.py`** — can the Liparus swallow it? `clearance_metrics`
computes exact per-axis margins between a `SubmarineSpec` and a `BayConfig`;
`classify_clearance` labels them `fits` / `tight` / `denied` against the
required margin; `stowage_capacity` divides the hold. `simulate_capture`
runs the four-phase discrete-event sequence — approach, ingress, hatch-seal,
secure — returning a `CaptureRun` with a per-phase timeline. Only *ingress*
and *secure* carry a discriminating predicate, and both are pure geometry:
no seal integrity is modelled, and the per-phase durations are declared
constants rather than a timing model, so the reported total is a schedule
and not a result.

**`vehicle_forensics.py`** — the paperwork side of the Lotus Esprit.
`SUBMERSIBLE_REQUIREMENTS` is a traced requirement set of nine systems, four
of them critical. `assess_conversion` walks a spec against it, separating
satisfied, missing, and unrecognised keys; a system explicitly set to
`False` and a system omitted entirely are treated identically.
`classify_conversion` maps the result to `road-only` / `amphibious` /
`submersible`, `recommend_upgrades` sorts the gaps critical-first, and
`buoyancy_status` applies Archimedes to classify the as-spec vehicle, in
seawater — the same density `hull_forensics` uses, so one vehicle is judged
in one fluid (this module used fresh water at 1000 kg/m^3 until that was
fixed).

**`hull_forensics.py`** — the physics side of the same question.
`hoop_stress_pa` is `sigma = p r / t`; `elastic_buckling_pressure_pa` is the
long-cylinder mode-2 pressure `p_cr = E (t/r)^3 / (4 (1 - nu^2))`;
`yield_pressure_pa` is `p_y = sigma_y t / r`. `collapse_pressure_pa` takes
the **minimum** of the two — thin hulls buckle before they yield, which is
why real submersibles are ring-stiffened — and `collapse_depth_m` converts
that to a depth. `design_safety_factor` is the ratio to operating depth, and
`ballast_volume_m3` gives the flood volume for neutral buoyancy.

### The composition layer

**`scenario.py`** is the single source of truth. It holds every canonical
parameter as a module-level constant, and `run_canonical()` runs all six
modules over them, returning one flat metric dict. Both `mission.execute`
and `manuscript_variables.generate_variables` consume that one factory, so
an outcome record and a printed manuscript number cannot disagree. It also
reports its own configuration (durations, dimensions, levels) alongside its
results, which is what lets the experimental-setup section be written
entirely in tokens.

Two derivations inside it are deliberate rather than incidental: the
beamforming element SNR is computed from the snapshot amplitude and noise
standard deviation rather than declared separately, and the scan-grid step
is read back off the grid the estimator actually scanned. Both exist so a
parameter edit cannot leave the manuscript describing a different
experiment.

**`manuscript_variables.py`** turns metrics into `{{TOKEN}}` strings. It
loads `manuscript/config.yaml` for identity fields, calls `run_canonical()`
for measurements, and reads `[tool.coverage.report] fail_under` out of
`pyproject.toml` via `coverage_floor_pct()` so the coverage figure quoted in
prose is the enforced one. `resolve_manuscript_tree` copies each `NN_*.md`
section to `output/manuscript/` with tokens substituted and, in strict mode,
raises on any leftover `{{...}}`. `_canonical_metrics` additionally gates the
run in strict mode via the pure predicate `check_metrics`: a contact that was
not detected, a non-positive detection range, or an infeasible hull each
abort rather than render. It emits no wall-clock value — the persisted
variable map is byte-identical across regenerations on one interpreter, and
`PYTHON_VERSION` is the only environment-dependent token.

**`figures/plots.py`** renders five deterministic figures — bearing track,
sonar detection range, beamformer response, capture feasibility, conversion
readiness — under the Agg backend, returning the written paths.

## How `mission.py` implements the frozen MissionProvider

`mission.py` is an adapter and nothing more. It contains no math; every
number it reports comes from `run_canonical()`.

| Method | Signature | What it does here |
|---|---|---|
| `brief()` | → `MissionBrief` | Declares film, codename `LIPARUS`, two objectives, one `Asset` per concept module, and a `determinism` `Constraint` |
| `recon(request)` | `ReconRequest` → `ReconReport` | Echoes the goal and returns `Finding`s naming the detection, tracking and hull models available |
| `plan(brief)` | `MissionBrief` → `MissionPlan` | Emits eight ordered `Step`s: detect, track, sonar, beamform, capture, forensics, hull, verify |
| `execute(plan)` | `MissionPlan` → `MissionOutcome` | Calls `run_canonical()` once; `success` is true only when the contact was detected **and** the capture succeeded **and** the hull is feasible; attaches `Provenance` with package version, seed, and a SHA-256 input hash over the canonical parameter set (`scenario.canonical_input_hash`) |
| `debrief(outcome)` | `MissionOutcome` → `Debrief` | Formats four lessons out of the outcome's own `results`, so the summary cannot drift from the run |

`MissionProvider.film` is the package slug, which is how discovery matches
it. `wall_time_s` in the provenance is fixed at `0.0` rather than measured,
because a real duration would make the outcome non-reproducible.

Module-level `GADGETS` is a `bond_api.registry.GadgetRegistry` populated at
import time under the slug, mapping twelve names to the domain callables the
fleet may invoke directly. Registration happens on import, so importing
`<slug>.mission` is by itself enough for the coordinator to see them.

## Forbidden patterns

- Domain math in `scripts/`.
- `bond_api` or `infrastructure` imports in any concept module.
- A metric typed into manuscript prose instead of flowing through
  `manuscript_variables.py`.
- A constant restated in two places — put it in `scenario.py` and derive.
- Mocks, dependency substitution via `monkeypatch.setattr`, or randomness
  without a fixed seed, anywhere in `tests/`.
- A conjunct in a predicate that the constructor has already made
  unfalsifiable.
- A declared constant reported as though it were measured.
- A "gate" written as a shell one-liner whose exit status nothing consumes.

The layer contract above is enforced by
`tests/test_repo_contracts.py::TestLayerContract`, which reads
`manuscript/layer_contract.yaml`. Before that test existed, no script, test
or hook read the file at all.
