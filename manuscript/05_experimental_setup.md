# Experimental setup {#sec:setup}

The package runs under Python {{PYTHON_VERSION}}. The manuscript variables
are hydrated by `scripts/z_generate_manuscript_variables.py`, which computes
metrics live from the domain core and resolves every manuscript token in
this tree.

## Canonical scenarios

Every parameter below is a substitution token read back out of
`src/the_spy_who_loved_me/scenario.py`, the module that actually configures
the run — the prose cannot describe a scenario the code did not execute.

* **Passive tracking**: a {{SUB_TRACK_DURATION_S}}-second scenario at a
  {{SUB_TRACK_DT_S}}-second cadence, yielding {{SUB_NUM_BEARINGS}} bearing
  samples; the target travels at {{SUB_TRACK_SPEED_M_S}} m/s on course
  {{SUB_TRACK_COURSE_DEG}}° from an initial range of {{SUB_TRACK_RANGE0_M}} m;
  the ownship runs a deterministic dogleg (east then north); relative
  bearings are corrupted by {{SUB_TRACK_BEARING_NOISE_DEG}}° of seeded noise.
* **Liparus capture**: a {{TANKER_HOLD_LENGTH_M}} m hold,
  {{TANKER_MOUTH_WIDTH_M}} m × {{TANKER_MOUTH_HEIGHT_M}} m mouth, and
  {{TANKER_CLEARANCE_M}} m required clearance swallowing a
  {{TANKER_SUB_LENGTH_M}} m submarine.
* **Vehicle forensics**: a Lotus-Esprit-grade spec
  ({{VEHICLE_DRY_MASS_KG}} kg dry mass, {{VEHICLE_DISPLACEMENT_M3}} m^3
  displacement) with the critical submersible systems fitted.
* **Passive sonar**: a {{ACO_SOURCE_LEVEL_DB}} dB source against a
  {{ACO_NOISE_LEVEL_DB}} dB noise floor and {{ACO_DIRECTIVITY_DB}} dB array
  directivity at {{ACO_FREQ_HZ}} Hz; sound speed at {{ACO_TEMP_C}} °C /
  {{ACO_SALINITY_PSU}} PSU at the surface.
* **Beamforming**: a half-wavelength ULA of {{BEAM_NUM_ELEMENTS}} elements
  observing a {{BEAM_TRUE_BEARING_DEG}}° bearing at {{BEAM_SNR_DB}} dB
  element SNR (seeded snapshot), scanned on a {{BEAM_SCAN_STEP_DEG}}° grid.
  The element SNR is *derived* from the snapshot amplitude and noise standard
  deviation rather than declared separately, so the Cramer-Rao bound in
  Section @sec:results always describes the array that was actually sampled.
* **Pressure hull**: a {{HULL_RADIUS_M}} m radius, {{HULL_THICKNESS_MM}} mm
  steel ({{HULL_YIELD_MPA}} MPa yield) cylinder operating at
  {{HULL_OPERATING_DEPTH_M}} m depth.

## Mission identity

The mission runs under codename {{LIPARUS_CODENAME}} with package version
{{LIPARUS_VERSION}} and a fixed seed. It serves {{NUM_CONCEPT_MODULES}}
concept modules to the BOND fleet through `bond_api` discovery and the
`GadgetRegistry`.

## Verification

Coverage and lineage are enforced by the package guardrails:
{{COVERAGE_FLOOR_PCT}}% line and branch on `src/`, no mock framework, no
leftover template lineage, and a clean `git status` after a path-scoped
commit. The quoted floor is itself read from `[tool.coverage.report]
fail_under` in `pyproject.toml` by
`manuscript_variables.coverage_floor_pct()`, so this sentence cannot claim a
gate stricter than the one that actually runs.
