# Testing Philosophy — LIPARUS

## Zero-mock policy

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Every test exercises a **real algorithm on real (generated,
deterministic) data**. Mocks are banned because a mock can "pass" while the
underlying math is wrong — they test call signatures, not correctness.

## What the suite covers (deterministic, real computation)

- **`test_sub_tracking.py`** — Neyman–Pearson detection decisions (signal
  present/absent at controlled `P_FA`), Wilson–Hilferty / Acklam quantile
  properties, deterministic scenario generation, batch TMA convergence
  against truth (maneuvering ownship), EKF predict/update mechanics and
  error branches, `tracking_rms_error`.
- **`test_tanker_capture.py`** — clearance metrics + classification
  (`fits`/`tight`/`denied`), stowage capacity, full 4-phase capture success
  and failure paths, per-phase timing.
- **`test_vehicle_forensics.py`** — requirement traceability, readiness
  classification (road-only/amphibious/submersible), missing-critical
  detection, Archimedean buoyancy (floats/neutral/sinks), upgrade
  recommendations.
- **`test_mission.py`** — the frozen `bond_api.MissionProvider` lifecycle,
  protocol conformance (`isinstance` runtime-checkable), deterministic
  results, gadget registration/lookup via `GadgetRegistry`.
- **`test_manuscript_variables.py`** — config loading, live `{{TOKEN}}`
  cross-reference over `manuscript/[0-9]*.md` (every token in prose exists in
  `generate_variables()`), strict resolution.
- **`test_scripts_smoke.py`** — subprocess runs of the thin CLIs with
  `sys.executable` and `cwd=project_root`; exit codes and artifact
  assertions.

## Coverage gate

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Line and branch coverage on `src/` must be ≥90%. Live counts associate with
the package's `docs/_generated/COUNTS.md`; do not hardcode them elsewhere.
