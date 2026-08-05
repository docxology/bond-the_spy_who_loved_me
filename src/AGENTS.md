# src/the_spy_who_loved_me — LIPARUS domain core

The importable logic of the LIPARUS film package. Lateral modules are pure
domain cores (no `bond_api`, no `infrastructure`); `mission.py` is the thin
`bond_api` adapter; `scenario.py` is the single source of truth shared by
`mission` and `manuscript_variables`.

| Module | Responsibility | Pure core? |
|---|---|---|
| `sub_tracking.py` | Passive acoustic detection + bearing-only tracking | yes |
| `tanker_capture.py` | Liparus capture simulation | yes |
| `vehicle_forensics.py` | Submersible conversion forensics | yes |
| `acoustics.py` | Underwater propagation + passive sonar equation | yes |
| `beamforming.py` | ULA beamforming + bearing estimation | yes |
| `hull_forensics.py` | Pressure-hull collapse + ballast analysis | yes |
| `scenario.py` | Canonical scenario (single source of truth) | yes |
| `manuscript_variables.py` | Live `{{TOKEN}}` hydration | reads config |
| `figures/plots.py` | Deterministic concept figures | yes (matplotlib) |
| `mission.py` | Frozen `bond_api.MissionProvider` + gadgets | adapter |

Public API is imported/exported from `__init__.py`. Keep the concept modules
standalone and protocol-free; only `mission.py` may import `bond_api`.

### Key functions

- `sub_tracking`: `detect_contract`, `estimate_tma`, `simulate_target_track`,
  `PassiveBearingTracker`, `chi2_quantile`, `tracking_rms_error`.
- `tanker_capture`: `clearance_metrics`, `classify_clearance`,
  `simulate_capture`, `stowage_capacity`.
- `vehicle_forensics`: `assess_conversion`, `classify_conversion`,
  `buoyancy_status`, `recommend_upgrades`.
- `acoustics`: `thorp_absorption`, `transmission_loss`,
  `passive_sonar_equation`, `detection_range_m`, `sound_speed_m_s`.
- `beamforming`: `steering_vector`, `array_snapshot`, `beam_power`,
  `estimate_bearing_deg`, `cramer_rao_bearing_std_deg`.
- `hull_forensics`: `hoop_stress_pa`, `elastic_buckling_pressure_pa`,
  `collapse_depth_m`, `design_safety_factor`, `ballast_volume_m3`.

Verification: `uv run pytest tests/ --cov=src --cov-fail-under=90`, `ruff
check`/`format`, `mypy`.
