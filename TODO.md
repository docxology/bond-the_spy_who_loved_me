# the_spy_who_loved_me — LIPARUS TODO

Remaining work only. Completed phases live in git history, not here — a TODO
that lists finished items stops being read.

## Open work

### 1. The beamformer's bearing estimate is grid-limited

`estimate_bearing_deg` peak-searches a fixed 0.5-degree scan grid, so its
error can never fall below half a cell no matter how good the array or the
SNR is. The canonical scenario's true bearing (30 degrees) sits exactly on a
node, which makes the reported error exactly zero — visually excellent and
statistically meaningless.

The manuscript and `docs/` now state this honestly rather than reading it as
precision, and `tests/test_beamforming.py::TestScanGridQuantisation` pins
the real property on off-grid bearings. What is *not* done is fixing the
estimator.

- [ ] Add quadratic (three-point parabolic) interpolation around the peak so
      the estimate is continuous rather than quantised and can approach the
      Cramer-Rao bound.
- [ ] Do this **additively** — a new function, or an opt-in keyword with the
      current behaviour as default. `estimate_bearing_deg` is in the
      `GADGETS` registry; changing what it returns for existing callers is a
      cross-package break.
- [ ] Acceptance: on an off-grid bearing at high SNR the interpolated error
      is strictly smaller than the grid-search error and within a small
      multiple of `cramer_rao_bearing_std_deg`.

### 2. The EKF is implemented but never exercised by the canonical scenario

`PassiveBearingTracker` is fully implemented and unit-tested, but
`run_canonical()` only runs the batch `estimate_tma`. No manuscript result
reports recursive-filter performance, so from the manuscript's point of view
the EKF is dead weight.

- [ ] Run the EKF over the same bearing sequence in `run_canonical()` and
      report its steady-state RMS error as a token alongside the batch TMA
      position error.
- [ ] Acceptance: a results-section sentence comparing batch and recursive
      accuracy on the same data, both from tokens.

### 3. Detection is measured but not reported

`run_canonical()` computes `detection_margin_db`, and the mission's
`success` flag depends on `detected`, but the results section never states
the detection outcome or its margin. A reader cannot tell at what
false-alarm rate the contact was declared.

- [ ] Add `DETECTION_MARGIN_DB` and the operating `P_FA` as tokens, and
      write a short detection paragraph in `03_results.md`.

### 4. Figure determinism is asserted only by file size

`tests/test_figures.py` asserts each figure renders to a non-empty file. It
does not assert that two renders of the same figure are byte-identical, so a
matplotlib version bump or a stray timestamp in PNG metadata would pass
unnoticed.

- [ ] Render twice and compare content hashes, normalising any embedded
      creation-date metadata.
- [ ] Acceptance: the test fails if a non-deterministic element is
      introduced into a plot.

### 5. The capture timeline is a declared constant, not a model

`tanker_capture._PHASE_DURATIONS` is four uncited numbers with no timing
model behind them, and the reported `total_time_s` therefore carries no
information about the submarine or the bay. This is now labelled honestly
everywhere it appears (module docstring, `03_results.md`, `AGENTS.md`, the
claim ledger) and pinned as a schedule by
`tests/test_tanker_capture.py::TestReportedTimeIsASchedule` — but it is
labelled, not fixed.

- [ ] Either derive phase durations from the geometry (an ingress transit at
      a stated tow speed, a seal cycle at a stated actuation rate) with the
      rates cited, or drop the timeline from the results section entirely.
- [ ] Acceptance: `capture_time_s` changes with submarine length, and each
      rate that drives it traces to a source.

### 6. Two of the four capture phases test nothing

*approach* always succeeds and *hatch-seal* succeeds whenever ingress did,
because no seal-integrity quantity exists anywhere in the package. The
`seal_requirement` field that gave the appearance of a seal predicate has
been removed rather than left as a dead conjunct.

- [ ] Either model a seal-integrity quantity that can fail (and cite what it
      is derived from), or collapse the sequence to the two phases that
      actually decide the outcome.
- [ ] Acceptance: every phase in the returned timeline has an input that
      makes it fail.

### 7. The EKF's accuracy bound is empirical, not derived

`TestEkfActuallyEstimates` bounds the steady-state error at 9% of mean target
range, a threshold chosen to sit between the measured correct behaviour
(8.0%) and the measured units-bug behaviour (9.9%). It is a real gate, but
the number is calibrated to observation rather than to theory.

- [ ] Compare the filter's reported covariance against its actual error
      (a normalised estimation error squared / consistency check) so the
      bound follows from the filter's own uncertainty claim.

## Declared integration points

1. **`bond-api` path dependency** is wired in `pyproject.toml`
   (`[tool.uv.sources] bond-api = { path = .../bond-api }`) and listed in
   `[project] dependencies`. If the path dep ever fails, the pure core
   imports without it — only `mission.py` needs `bond_api`. Acceptance:
   `uv run python -c "import bond_api, the_spy_who_loved_me.mission"`.
2. **Fleet provenance helper**
   (`bond_utilities.mission_io.record_provenance_outcome`) is not yet bound.
   When `bond-utilities` ships a stable helper, `mission.py::execute` should
   call it to persist its `MissionOutcome` instead of the current local JSON
   write in `scripts/mission_cli.py`. Acceptance: the outcome record carries
   the same `provenance` block (package_version, seed, input_hash).
   Note for that conversation: `input_hash` is no longer the fixed literal
   `"liparus-mission-input"` — it is now a SHA-256 over the canonical
   parameter set, so any fleet consumer that treated it as an opaque package
   identifier will see a different (and now varying) value.
3. **Orchestrator discovery**: `bond-orchestrator` discovers this film by
   slug via `bond_api.discovery`; the provider is exposed at module top
   level in `mission.py` as `MissionProvider` with
   `film = "the_spy_who_loved_me"`. Acceptance: `discover()` returns the
   provider and `run_mission` succeeds.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/
uv run python scripts/mission_cli.py full
uv run python scripts/z_generate_manuscript_variables.py
git status --short   # clean after a path-scoped commit
```

The documentation gates (lineage, layer contract, versions, figure
registries, publication identity) are in `tests/test_repo_contracts.py` and
run with the suite; the `rg`-based lineage one-liner that used to sit here
could not fail and did not match the boilerplate it was aimed at.
