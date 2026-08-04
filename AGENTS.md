# the_spy_who_loved_me — LIPARUS (The Spy Who Loved Me, 1977)

**PROJECT BOND film package** — special-agent mission software exposing three
deterministic domain concepts to the BOND fleet through the frozen `bond_api`
mission protocol. Local-only working tree (no remote, never push).

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
| `src/the_spy_who_loved_me/manuscript_variables.py` | `{{TOKEN}}` hydration from `manuscript/config.yaml` + live domain-metric runs. |
| `src/the_spy_who_loved_me/mission.py` | Thin `bond_api` adapter: `MissionProvider` implementation + `GadgetRegistry` registration. |
| `scripts/` | Thin orchestrators (CLIs + manuscript/figure generation). |

The three concept modules are infrastructure-free and importable *without*
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
uv run ruff check src/ scripts/ tests/
uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short   # clean after a path-scoped commit
```

Zero mocks; real data + computation only; ≥90% line+branch on `src/`;
deterministic (fixed seeds, no untracked RNG).

## See also

- `../bond-api` — the frozen `MissionProvider` protocol (son package in the
  BOND suite; path dependency).
- [`docs/agent_instructions.md`](docs/agent_instructions.md) — operational
  rules for agents working here.
- [`TODO.md`](TODO.md) — forward-only backlog and declared integration points.
- [`README.md`](README.md) — quick start.
