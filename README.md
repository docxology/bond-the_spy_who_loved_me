# The Spy Who Loved Me: LIPARUS

Special-agent mission software for **The Spy Who Loved Me (1977)** under
mission codename **LIPARUS** — a PROJECT BOND film package that models three
deterministic concepts behind the film's set pieces: passive acoustic
submarine detection/tracking, a Liparus-class tanker capture simulation, and
submersible vehicle conversion forensics.

## What this package does

| Concept | Module | Highlights |
|---|---|---|
| Passive acoustic tracking | `src/the_spy_who_loved_me/sub_tracking.py` | Neyman–Pearson detector (Wilson–Hilferty thresholds), bearing-only target motion analysis (batch least-squares + Gauss–Newton), Extended Kalman Filter |
| Underwater acoustics | `src/the_spy_who_loved_me/acoustics.py` | Thorp absorption, transmission loss, passive sonar equation, detection-range solve, Mackenzie sound speed |
| Beamforming | `src/the_spy_who_loved_me/beamforming.py` | ULA steering vectors, conventional beamformer, bearing estimation, Cramer–Rao bound |
| Liparus capture | `src/the_spy_who_loved_me/tanker_capture.py` | Exact clearance geometry, discrete-event capture (approach → ingress → seal → secure), stowage capacity |
| Vehicle forensics | `src/the_spy_who_loved_me/vehicle_forensics.py` | Requirement traceability, readiness classification, Archimedean buoyancy |
| Pressure-hull forensics | `src/the_spy_who_loved_me/hull_forensics.py` | Hoop stress, elastic buckling, collapse depth, ballast volume |
| Mission | `src/the_spy_who_loved_me/mission.py` | Frozen `bond_api.MissionProvider` + gadget registry |

Everything is deterministic (fixed seeds, no mocks), and every number in the
manuscript is computed live by the domain core — never hardcoded.

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
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
```

See [AGENTS.md](AGENTS.md) for the full layer contract and [TODO.md](TODO.md)
for the backlog.
