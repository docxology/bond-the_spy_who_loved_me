# Architecture — LIPARUS

## Dependency direction

```
scripts/  (thin CLIs)
   │
   ▼
src/the_spy_who_loved_me/
   ├── sub_tracking.py        pure domain core (no bond_api, no infrastructure)
   ├── tanker_capture.py      pure domain core
   ├── vehicle_forensics.py   pure domain core
   ├── manuscript_variables.py  reads manuscript/config.yaml + live metrics
   ├── figures/plots.py       deterministic matplotlib figures
   └── mission.py             bond_api adapter (MissionProvider + GadgetRegistry)
            │
            ▼
   bond_api (path dependency — frozen protocol)
```

## Layer rules

- **Pure domain core** (`sub_tracking.py`, `tanker_capture.py`,
  `vehicle_forensics.py`): standalone, importable *without* `bond_api`.
  No `infrastructure.*` imports anywhere in this package.
- **`mission.py`** is the only module that imports `bond_api`. It adapts the
  domain core to the frozen `MissionProvider` lifecycle and registers
  gadgets.
- **`manuscript_variables.py`** computes every `{{TOKEN}}` metric by running
  the real domain algorithms; script/prose never hardcode numbers.
- **`scripts/`** are thin: `mission_cli.py` (phases), `generate_figures.py`,
  `z_generate_manuscript_variables.py`. No domain math lives here.

## Module responsibilities

| Module | Responsibility |
|---|---|
| `sub_tracking` | Energy detection (Neyman–Pearson/Wilson–Hilferty); maneuvering-ownship scenario; batch TMA + EKF tracking |
| `tanker_capture` | Clearance geometry; discrete-event capture; stowage |
| `vehicle_forensics` | Requirement traceability; classification; buoyancy |
| `manuscript_variables` | Config load + live metric tokens + manuscript tree resolution |
| `figures/plots` | Three deterministic concept figures |
| `mission` | Frozen protocol adapter + gadget registration |

## Forbidden patterns

- Math in `scripts/` (business logic must be in `src/`).
- `bond_api`/`infrastructure` imports in the pure concept modules.
- Hardcoded metrics in manuscript prose (must flow through
  `manuscript_variables.py`).
- Mocks, magic, or untracked randomness in tests.
