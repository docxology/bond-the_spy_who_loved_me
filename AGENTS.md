# the_spy_who_loved_me — LIPARUS (The Spy Who Loved Me, 1977)

**PROJECT BOND film package** — special-agent mission software exposing six
deterministic domain concepts to the BOND fleet through the frozen `bond_api`
mission protocol. No DOI, no release tag, no package registry; the only git
remote is this package's own repository
(`github.com/docxology/bond-the_spy_who_loved_me`, default branch `main`).

## Package identity

| Field | Value |
|---|---|
| Film | The Spy Who Loved Me (1977) |
| Mission codename | LIPARUS |
| Package (`name`) | `the_spy_who_loved_me` |
| Protocol | `bond_api.MissionProvider` (frozen, via local path dependency) |
| Core language | Python (stdlib + numpy + matplotlib + pyyaml) |

## Layer contract

| Surface | Rule |
|---|---|
| `src/the_spy_who_loved_me/sub_tracking.py` | Pure domain core — passive acoustic detection + bearing-only tracking. No `bond_api`/`infrastructure` imports. |
| `src/the_spy_who_loved_me/tanker_capture.py` | Pure domain core — Liparus swallowing-submarine simulation. Standalone. |
| `src/the_spy_who_loved_me/vehicle_forensics.py` | Pure domain core — submersible conversion forensics. Standalone. |
| `src/the_spy_who_loved_me/acoustics.py` | Pure domain core — underwater propagation + passive sonar equation. Standalone. |
| `src/the_spy_who_loved_me/beamforming.py` | Pure domain core — ULA beamforming + bearing estimation. Standalone. |
| `src/the_spy_who_loved_me/hull_forensics.py` | Pure domain core — pressure-hull collapse + ballast analysis. Standalone. |
| `src/the_spy_who_loved_me/scenario.py` | Canonical single source of truth consumed by `mission` and `manuscript_variables`. |
| `src/the_spy_who_loved_me/manuscript_variables.py` | `{{TOKEN}}` hydration from `manuscript/config.yaml` + live domain-metric runs. |
| `src/the_spy_who_loved_me/mission.py` | Thin `bond_api` adapter: `MissionProvider` implementation + `GadgetRegistry` registration. |
| `scripts/` | Thin orchestrators (CLIs + manuscript/figure generation). |

The six concept modules are infrastructure-free and importable *without*
`bond_api`; only `mission.py` (the adapter) imports the protocol, so the pure
core keeps working if the path dependency ever fails.

## Concepts & algorithms

1. **Passive acoustic submarine tracking** (`sub_tracking.py`) — Neyman–Pearson
   energy detector with Wilson–Hilferty chi-square thresholds; bearing-only
   target motion analysis (batch least-squares + Gauss–Newton) and an
   Extended Kalman Filter, with a fundamentally-motivated requiring observer
   maneuver for observability.
2. **Liparus-class tanker capture** (`tanker_capture.py`) — exact per-axis
   clearance geometry + discrete-event capture simulation (approach, ingress,
   hatch-seal, secure).
3. **Submersible vehicle forensics** (`vehicle_forensics.py`) — requirement
   traceability, readiness scoring/classification, and Archimedean buoyancy
   feasibility for Lotus-Esprit-grade conversions.
4. **Underwater acoustics & passive sonar** (`acoustics.py`) — Thorp
   absorption, geometric-spreading transmission loss, the passive sonar
   equation, a monotone-bisection detection-range solve, and the Mackenzie
   sound-speed equation.
5. **ULA beamforming** (`beamforming.py`) — steering vectors, the conventional
   delay-and-sum beamformer, peak-search bearing estimation, and the
   Cramer–Rao bound on bearing precision.
6. **Pressure-hull & ballast forensics** (`hull_forensics.py`) — hoop stress,
   long-cylinder elastic buckling, governing collapse pressure/depth,
   design safety factor, and Archimedean ballast volume for neutral buoyancy.

## Known modelling caveats

Recorded here so no reader mistakes an artefact for a result. The two
literals in the first bullet are bound to the canonical run by
`tests/test_repo_contracts.py::TestDocsAgreeWithTheRun`, so a `scenario.py`
edit that moves them fails the suite instead of silently falsifying this
file.

- **The beamformer's measured bearing error is grid-limited, not
  CRB-limited.** `estimate_bearing_deg` peak-searches a 0.5-degree scan
  grid, and the canonical true bearing (30 degrees) lands exactly on a grid
  node, so the reported error is exactly zero — below the Cramer-Rao bound,
  which no unbiased estimator can beat. Section 3 of the manuscript states
  this explicitly and `tests/test_beamforming.py` pins the quantisation
  property on off-grid bearings, where it can actually fail.
- **The capture elapsed time is a declared schedule, not a result.**
  `tanker_capture._PHASE_DURATIONS` is four uncited constants; the reported
  total is their sum over the phases a run reached. It does not vary with
  submarine size or bay geometry, and it is the same for a capture that
  succeeds and one that fails at *secure*. Only two of the four phases carry
  a discriminating predicate, and both are pure geometry — no seal integrity
  is modelled anywhere in the package.
- **The TMA grid initialiser is tuned to the canonical scenario.** Its
  default envelope (3000–6500 m, 5–35 m/s) brackets the canonical truth of
  4000 m and 25 m/s. Degradation outside it is graceful, not a cliff — 15 km
  still recovers to 293 m — but by 60 km the default envelope leaves a 42%
  range error. Canonical tracking accuracy is not evidence about arbitrary
  geometry.
- **Signal excess is not SNR.** `passive_sonar_equation` returns
  `SL - TL - (NL - DI) - DT`, which is signal excess; the array-output SNR is
  larger by the detection threshold. Both are available; the package used to
  call the first one an SNR throughout.
- **Every model is first-order.** The propagation budget is
  range-independent (no ray tracing, no profile, no boundary interaction);
  the tracker assumes an ideal constant-velocity target and exactly known
  ownship; the hull is an unstiffened long cylinder with no ring
  stiffening, end caps, or out-of-roundness. `manuscript/
  07_scope_and_related_work.md` enumerates the boundaries.

## Mission protocol

`src/the_spy_who_loved_me/mission.py` implements the frozen
`bond_api.MissionProvider` (brief / recon / plan / execute / debrief) with a
fixed seed and full `Provenance`, and registers its concept gadgets on a
`GadgetRegistry` at import time under the slug `the_spy_who_loved_me`. The
orchestrator discovers it via `bond_api.discovery`.

## Setup & usage

```bash
# From this package directory
uv sync --extra dev            # installs deps + the bond-api path dependency
uv run python scripts/mission_cli.py full        # run the full mission lifecycle
uv run python scripts/generate_figures.py        # render concept figures
uv run python scripts/z_generate_manuscript_variables.py   # hydrate manuscript tokens
```

## Testing & verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/
uv run python scripts/mission_cli.py full                  # protocol still drivable
uv run python scripts/z_generate_manuscript_variables.py   # every token still resolves
git status --short   # clean after a path-scoped commit
```

Documentation lineage, the layer contract, the version cross-check, the
figure registries and the fabricated-publication scan are all in
`tests/test_repo_contracts.py`, so they run inside the first command.

That is deliberate. The lineage check used to be a shell one-liner,
`rg -n "template[_]code_project" . || echo Clean`, and it was vacuous twice
over: `rg` exits non-zero on *no* match so the `|| echo Clean` fired on
success and nothing failed on a hit, and the boilerplate it was meant to
catch never contained that string — `STANDALONE.md` was wholesale exemplar
text spelling the path `templates/the_spy_who_loved_me`. The replacement
matches the boilerplate itself and fails the suite.

Zero mock framework; real data + computation only; deterministic (fixed
seeds, no untracked RNG). Coverage is line **and** branch on `src/` at the
floor declared by `[tool.coverage.report] fail_under` in `pyproject.toml` —
that declaration is the single source of the figure, and the manuscript
reads it through `manuscript_variables.coverage_floor_pct()` rather than
restating it.

The manuscript-hydration step is part of the gate, not a nicety: strict
resolution is what proves every `{{TOKEN}}` in prose still has a generator
behind it.

If a `uv` command reports `Failed to initialize cache` or `Operation not
permitted`, that is a sandbox restriction on the cache directory, not a
package failure — re-run with the sandbox disabled.

## See also

- `../bond-api` — the frozen `MissionProvider` protocol (sibling package in the
  BOND suite; path dependency).
- [`docs/agent_instructions.md`](docs/agent_instructions.md) — operational
  rules for agents working here.
- [`TODO.md`](TODO.md) — forward-only backlog and declared integration points.
- [`README.md`](README.md) — quick start.
