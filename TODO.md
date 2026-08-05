# the_spy_who_loved_me — LIPARUS TODO

Forward-only backlog for the LIPARUS film package. Kept current as built;
declared integration points are explicit so later BOND phases can bind
without rework.

## Deep improvement (phase-4, current)

Three new deterministic domain modules were added, deepening the submarine
tracking and marine-forensics payload behind an unchanged `MissionProvider`:

- `acoustics.py` — Thorp (1967) absorption, geometric-spreading transmission
  loss, the passive sonar equation (`passive_sonar_equation`), a monotone
  bisection detection-range solve, and the Mackenzie (1981) sound-speed
  equation.
- `beamforming.py` — ULA steering vectors, conventional delay-and-sum
  beamformer, peak-search bearing estimation, and the Cramer-Rao bound on
  bearing precision.
- `hull_forensics.py` — hoop stress, long-cylinder elastic buckling, the
  governing collapse pressure/depth, design safety factor, and Archimedean
  ballast volume for neutral buoyancy.
- `scenario.py` — canonical single source of truth (`run_canonical`) shared
  by `mission.execute` and `manuscript_variables`, so outcome `results` and
  manuscript `{{TOKEN}}`s can never disagree. `NUM_CONCEPT_MODULES` is now 6.
- Two new figures (`beamforming_response`, `sonar_detection_range`); new
  `{{TOKEN}}`s (ACO_*, BEAM_*, HULL_*, BALLAST_*); references.bib extended
  with Urick, Thorp, Mackenzie, Van Trees, and Ross.

Gate (measured): `uv run pytest tests/ --cov=src --cov-fail-under=90` at
≥90% (target 98%+), 0 mocks, 0 skipped; `ruff check`/`format` + `mypy`
clean; lineage `rg` clean; `git status` clean after commit.

## Built (phase-1 conversion)

- **Pure domain core** in `src/the_spy_who_loved_me/`:
  - `sub_tracking.py` — Neyman–Pearson energy detector (`detect_contract`,
    `chi2_quantile`, `inverse_normal_cdf`), maneuvering-ownship scenario
    (`simulate_target_track`), batch least-squares TMA (`estimate_tma`),
    recursive EKF (`PassiveBearingTracker`), `tracking_rms_error`.
  - `tanker_capture.py` — `clearance_metrics`, `classify_clearance`,
    `stowage_capacity`, `simulate_capture` (4-phase discrete-event), plus
    `CaptureRun`/`PhaseRecord`/`Clearance` result types.
  - `vehicle_forensics.py` — `SUBMERSIBLE_REQUIREMENTS`, `assess_conversion`,
    `classify_conversion`, `buoyancy_status`, `recommend_upgrades`.
- **Frozen protocol adapter** `src/the_spy_who_loved_me/mission.py`:
  `MissionProvider` (brief/recon/plan/execute/debrief) implementing
  `bond_api`; registers 4 concept gadgets on a `GadgetRegistry` under slug
  `the_spy_who_loved_me`. Discoverable via `bond_api.discovery`.
- **Manuscript plumbing**: `manuscript/config.yaml` (LIPARUS identity) +
  `src/the_spy_who_loved_me/manuscript_variables.py` (live `{{TOKEN}}`
  metrics); numbered sections updated with LIPARUS tokens and figures.
- **Figures** `src/the_spy_who_loved_me/figures/plots.py`: bearing-track,
  capture-feasibility, conversion-readiness.
- **Thin CLIs** `scripts/`: `mission_cli.py` (brief/recon/plan/execute/
  debrief/full), `generate_figures.py`, `z_generate_manuscript_variables.py`.
- **Tests** (deterministic, zero-mock) per module + manuscript token
  cross-reference + script smoke.
- **Gate** (measured): `uv run pytest tests/ --cov=src --cov-fail-under=90`
  passes at ≥90% line+branch on `src/`; `ruff check`/`format` and `mypy`
  clean; lineage `rg` clean; `git status` clean after commit.

## Declared integration points

1. **`bond-api` path dependency** is wired in `pyproject.toml`
   (`[tool.uv.sources] bond-api = { path = .../bond-api }`) and listed in
   `[project] dependencies`. If the path dep ever fails, the pure core in
   `src/the_spy_who_loved_me/` imports without it — only `mission.py` needs
   `bond_api`. Acceptance: `uv run python -c "import bond_api, the_spy_who_loved_me.mission"`.
2. **Fleet provenance helper** (`bond_utilities.mission_io.
   record_provenance_outcome`) is not yet bound. When `bond-utilities` ships
   a stable helper, `mission.py::execute` should call it to persist its
   `MissionOutcome` record instead of the current local JSON write in
   `scripts/mission_cli.py`. Acceptance: outcome record carries the same
   `provenance` block (package_version, seed, input_hash).
3. **Orchestrator discovery**: `bond-orchestrator` will discover this film by
   slug via `bond_api.discovery`; the provider is exposed at module top level
   in `mission.py` under `MissionProvider` with `film = "the_spy_who_loved_me"`.
   Acceptance: `discover()` returns the provider and `run_mission` succeeds.

## Verification commands

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short   # clean after a path-scoped commit
```
