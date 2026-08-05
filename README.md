# The Spy Who Loved Me: LIPARUS

Special-agent mission software for **The Spy Who Loved Me (1977)** under
mission codename **LIPARUS** — a PROJECT BOND film package that models six
deterministic concepts behind the film's set pieces. The *Liparus* is the
supertanker whose hull opens to swallow submarines whole; the Lotus Esprit
is the road car that converts into a working submersible. Both raise the
same engineering questions: can you hear the contact, can you say where it
is, does it physically fit, and will the conversion survive the depth?

## What this package does

Six pure concept modules do the domain work, and three more compose and
expose them.

| Concept | Module | What it computes |
|---|---|---|
| Underwater acoustics | `src/the_spy_who_loved_me/acoustics.py` | Thorp absorption, spreading + absorption transmission loss, the passive sonar equation, bisection detection-range solve, Mackenzie sound speed |
| Passive acoustic tracking | `src/the_spy_who_loved_me/sub_tracking.py` | Neyman–Pearson energy detector (Wilson–Hilferty thresholds over Acklam's normal quantile), bearing-only target motion analysis (grid search + Gauss–Newton), Extended Kalman Filter |
| Beamforming | `src/the_spy_who_loved_me/beamforming.py` | ULA steering vectors, conventional delay-and-sum beamformer, peak-search bearing estimation, Cramer–Rao bound |
| Liparus capture | `src/the_spy_who_loved_me/tanker_capture.py` | Exact per-axis clearance geometry, discrete-event capture (approach → ingress → seal → secure), stowage capacity |
| Vehicle forensics | `src/the_spy_who_loved_me/vehicle_forensics.py` | Requirement traceability over nine systems, readiness classification, Archimedean buoyancy |
| Pressure-hull forensics | `src/the_spy_who_loved_me/hull_forensics.py` | Hoop stress, long-cylinder elastic buckling, governing collapse depth, design safety factor, ballast volume |

| Support module | What it does |
|---|---|
| `src/the_spy_who_loved_me/scenario.py` | The canonical parameter set and `run_canonical()`, the one metric factory both the mission adapter and the manuscript consume — so an outcome and a printed number cannot disagree |
| `src/the_spy_who_loved_me/manuscript_variables.py` | Hydrates every manuscript `{{TOKEN}}` from live metrics, `manuscript/config.yaml`, and the coverage floor in `pyproject.toml` |
| `src/the_spy_who_loved_me/figures/plots.py` | Five deterministic matplotlib figures |
| `src/the_spy_who_loved_me/mission.py` | The frozen `bond_api.MissionProvider` adapter + `GADGETS` registry |

Everything is deterministic (fixed seeds, no mock framework), and every
number in the manuscript is computed live by the domain core — never
hardcoded.

## The MissionProvider surface

`mission.py` exposes the frozen protocol the rest of the BOND fleet consumes
(`bond-cli`, the coordinator's reconcile, the orchestrator's discovery). Its
public shape does not change:

| Surface | Contract |
|---|---|
| `MissionProvider` (module top level) | Discovery imports `the_spy_who_loved_me.mission` and instantiates this name |
| `brief() -> MissionBrief` | Film, codename, objectives, one `Asset` per concept module, determinism constraint |
| `recon(ReconRequest) -> ReconReport` | Goal echo plus `Finding`s for the detection, tracking and hull models |
| `plan(MissionBrief) -> MissionPlan` | Eight ordered `Step`s: detect, track, sonar, beamform, capture, forensics, hull, verify |
| `execute(MissionPlan) -> MissionOutcome` | One `run_canonical()` call; `success` requires detection **and** capture **and** hull feasibility; full `Provenance` (version, seed, input hash) |
| `debrief(MissionOutcome) -> Debrief` | Four lessons formatted from the outcome's own results |
| `GADGETS` | `GadgetRegistry` registered at import under slug `the_spy_who_loved_me`, exposing twelve domain callables |

Drive it end to end with `uv run python scripts/mission_cli.py full`.

## Quick start

```bash
uv sync --extra dev
uv run python scripts/mission_cli.py full            # run the full mission
uv run python scripts/generate_figures.py            # render figures to output/figures/
uv run python scripts/z_generate_manuscript_variables.py   # hydrate manuscript tokens
```

## Layout

```
src/the_spy_who_loved_me/     # domain core + manuscript_variables + mission
scripts/                      # thin CLIs (mission phases, figures, manuscript vars)
tests/                        # deterministic, zero-mock test suite
manuscript/                   # config.yaml + numbered sections (LIPARUS identity)
output/                       # regenerable figures/data (git-ignored)
```

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/
```

The coverage gate is line **and** branch on `src/`, at the floor declared by
`[tool.coverage.report] fail_under` in `pyproject.toml`. That declaration is
the single source of the number — the manuscript reads it through
`manuscript_variables.coverage_floor_pct()` rather than restating it, so no
document here can quote a stricter gate than the one that runs.

If a `uv` command fails with `Failed to initialize cache` or `Operation not
permitted`, that is a sandbox restriction on the `uv` cache directory rather
than a package failure; re-run with the sandbox disabled.

## Documentation

| Where | What |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Package identity and the full layer contract |
| [`TODO.md`](TODO.md) | Remaining work and declared integration points |
| [`STANDALONE.md`](STANDALONE.md) | Running this package outside the BOND suite |
| [`docs/`](docs/) | Agent instructions, module-by-module architecture, testing doctrine |
| [`manuscript/`](manuscript/) | Manuscript sources, token protocol, figure registry |
