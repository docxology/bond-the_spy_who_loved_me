# TODO — the_spy_who_loved_me (LIPARUS)

LIPARUS is the PROJECT BOND film package for *The Spy Who Loved Me* (1977).
Six pure domain modules model the film's engineering — passive acoustic
detection and bearing-only tracking, underwater propagation and the passive
sonar equation, ULA beamforming, Liparus-class tanker capture geometry,
submersible conversion forensics, and pressure-hull collapse/ballast — and
three support modules compose them: `scenario.py` (the canonical parameter
set and `run_canonical()`), `manuscript_variables.py` (`{{TOKEN}}` hydration)
and `mission.py` (the frozen `bond_api.MissionProvider` adapter). No DOI, no
release tag, and no remote other than `github.com/docxology/bond-the_spy_who_loved_me`.

**Verified state, measured 2026-08-06 (Round-2 deep-improvement, commit `0aa55c5` + this round):**
`uv run pytest tests/ --cov=src --cov-fail-under=90` → **225 passed**,
**100.00%** line *and* branch coverage on `src/` (948 statements, 192
branches, 0 missed). `ruff check`, `ruff format --check`, `mypy src/`,
`scripts/mission_cli.py full` and `scripts/z_generate_manuscript_variables.py`
all pass. See the **Round-2 (2026-08-06)** section at the bottom for the
findings fixed and the ones deliberately left open.

Everything below is open. Finished work is in git history, not here.

---

## Open work

### Correctness — things that are wrong

#### C2. The capture elapsed time is a declared constant, not a model

`_PHASE_DURATIONS` (`src/the_spy_who_loved_me/tanker_capture.py:235`) is four
uncited literals summing to 630 s. Nothing makes a phase duration depend on
the submarine or the bay, so the reported `capture_time_s` is identical for a
10 m boat and a 72 m one and carries no information about either.

This is now labelled everywhere it appears — the module docstring
(`tanker_capture.py:31-34`), `total_time_s`'s own docstring (`:186-192`),
`manuscript/03_results.md:66-72`, `AGENTS.md`, and `data/claim_ledger.yaml`
(`claim_id: capture-elapsed-time`, `source_tier: declared_constant`) — and
`tests/test_tanker_capture.py::TestReportedTimeIsASchedule` pins it as a
schedule. It is labelled, not fixed.

- **Done looks like:** either the phase durations are derived from the
  geometry (an ingress transit at a stated tow speed, a seal cycle at a stated
  actuation rate) with every rate traced to a cited source, or the timeline
  leaves `manuscript/03_results.md` entirely.
- **Closing condition:** `capture_time_s` changes when submarine length
  changes, and the claim ledger entry stops being `declared_constant`.
- **Command:** `uv run pytest tests/test_tanker_capture.py -v && uv run python -c "from the_spy_who_loved_me.scenario import run_canonical; print(run_canonical()['capture_time_s'])"`

*Carried from the adversarial pass as unresolved.*

#### C3. Two of the four capture phases carry no failing predicate

`simulate_capture` (`src/the_spy_who_loved_me/tanker_capture.py:243`) records
four phases. *approach* is unconditionally `True` (`:277`) and *hatch-seal* is
unconditionally `True` whenever ingress passed (`:289`, note "seal integrity
not modelled"), because no seal-integrity quantity exists anywhere in the
package. The `seal_requirement` field that once gave the appearance of a seal
predicate was removed rather than left as a dead conjunct — so the appearance
is gone, but the two inert phases remain.

- **Done looks like:** either a seal-integrity quantity that can actually fail
  (with a cited derivation for whatever it is computed from), or the sequence
  collapses to the two phases that decide the outcome (ingress, secure).
- **Closing condition:** every phase in the returned `CaptureRun.phases` has
  at least one input that makes its `ok` field `False`, pinned by a test that
  constructs that input for each phase.
- **Command:** `uv run pytest tests/test_tanker_capture.py -v`

*Carried from the adversarial pass as unresolved.*

### Verification — claims not yet bound by a test that can fail

#### V1. The EKF accuracy bound is empirical, not derived

`tests/test_sub_tracking.py:195-210`
(`TestEkfActuallyEstimates::test_filter_tracks_the_target`) bounds the
steady-state RMS error at `0.09 * mean_range_m`. The docstring is honest about
where 0.09 came from: it sits between the measured correct behaviour (8.0% of
mean range with `R = sigma**2`) and the measured units-bug behaviour (9.9%
with `R = sigma`). It is a real, proven-failable gate — but the number is
calibrated to observation, not derived from the filter's own uncertainty
claim.

- **Done looks like:** a consistency check (normalised estimation error
  squared / NEES) comparing the filter's reported covariance `P` against its
  actual error, so the bound follows from theory rather than from two
  measurements.
- **Closing condition:** reintroducing `self._r = float(measurement_noise_rad)`
  (dropping the square at `src/the_spy_who_loved_me/sub_tracking.py:504`) still
  fails the suite, and the assertion's threshold is a chi-square quantile
  rather than a hand-picked ratio.
- **Command:** `uv run pytest tests/test_sub_tracking.py::TestEkfActuallyEstimates -v`

*Carried from the adversarial pass as unresolved.*

### Extension — genuine future work

#### E2. Fleet provenance helper is not yet bound

`bond_utilities.mission_io.record_provenance_outcome` is not called anywhere
here. When `bond-utilities` ships a stable helper, `mission.py::execute` (or
`scripts/mission_cli.py:50-54`) should persist its `MissionOutcome` through it
instead of the current local JSON write, which already carries the provenance
block.

- **Done looks like:** the outcome record written by the fleet helper carries
  the same `provenance` block (`package_version`, `seed`, `input_hash`).
- **Note for whoever takes it:** `input_hash` is no longer the fixed literal
  `"liparus-mission-input"` — it is a SHA-256 over the canonical parameter set
  (`scenario.canonical_input_hash`), so any fleet consumer that treated it as
  an opaque package identifier will see a different, and now varying, value.
- **Command:** `uv run python -c "import bond_utilities.mission_io"` (currently
  the blocker) then `uv run python scripts/mission_cli.py execute`.

---

## Known limitations (not bugs)

Accepted and out of scope. Recorded so they are not re-litigated.

- **No publication identity, by design.** No public remote, no DOI reserved or
  deposited, no PyPI/Zenodo/HuggingFace/OSF/IPFS/Software Heritage presence,
  no release tag. `CITATION.cff`, `codemeta.json` and `.zenodo.json` are
  *prepared* metadata for a deposit that has not happened.
  `tests/test_repo_contracts.py::TestNoFabricatedPublicationIdentity` keeps it
  that way. See `STANDALONE.md`.
- **The TMA grid initialiser is tuned to the canonical scenario, and that is a
  soft limit.** Its default envelope (3000–6500 m, 5–35 m/s) brackets the
  canonical truth of 4000 m / 25 m/s. The audit stated a target outside the
  envelope "cannot be initialised"; that mechanism is wrong — Gauss-Newton
  escapes a poor seed, and a 15 km target still recovers to 293 m. Degradation
  becomes binding around 60 km (42% range error). Both directions are pinned by
  `tests/test_sub_tracking.py::TestCoarseSearchEnvelope` (`:246`, `:253`,
  `:259`), including the deliberate non-failure at 15 km so the caveat is not
  overclaimed in reverse. Canonical tracking accuracy is still not evidence
  about arbitrary geometry.
- **`output/` is gitignored, so regenerated artefacts are not committed
  evidence.** They are byte-identical across runs, but the committed evidence
  is the code and the gates, not the artefacts. Do not add `output/` to git to
  "prove" determinism — prove it with the determinism tests.
- **`PYTHON_VERSION` makes the variable map byte-identical per interpreter,
  not universally.** It is the single environment-dependent token
  (`src/the_spy_who_loved_me/manuscript_variables.py:144`). It is not
  wall-clock — the value is fixed for a given interpreter — and
  `06_reproducibility.md:12` says so. A `GENERATION_TIMESTAMP` token used to
  sit beside it and was removed.
- **Signal excess is not SNR, and the package now says so.**
  `passive_sonar_equation` returns `SL - TL - (NL - DI) - DT`, which is signal
  excess; `signal_to_noise_ratio_db` is the separate, larger quantity. The
  field was named `snr_db` until the two were separated. This is settled, not
  open.
- **Every model is first-order.** Range-independent propagation (no ray
  tracing, no sound-speed profile, no boundary interaction); an ideal
  constant-velocity target with exactly known ownship; an unstiffened long
  cylinder with no ring stiffening, end caps, or out-of-roundness.
  `manuscript/07_scope_and_related_work.md` enumerates the boundaries.
- **The `bond_api` path dependency is optional to the core.** Only
  `mission.py` imports the protocol; the six concept modules import without
  it. Verify with
  `uv run python -c "import bond_api, the_spy_who_loved_me.mission"`.
  Orchestrator discovery finds this film by slug via `bond_api.discovery`;
  `MissionProvider` is exposed at module top level in `mission.py` with
  `film = "the_spy_who_loved_me"`.

---

## Verification

Run from the package root. All five must pass before any commit.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/
uv run python scripts/mission_cli.py full
uv run python scripts/z_generate_manuscript_variables.py
git status --short   # empty after a path-scoped commit
```

**Expected outcomes (Round 2, 2026-08-06):** 225 passed, 100.00% coverage
(floor 90, line + branch); `All checks passed!` and `33 files already
formatted`; `Success: no issues found in 13 source files`; the mission CLI
prints the five phase objects and exits 0; hydration resolves every
`{{TOKEN}}` under strict mode and exits 0; `git status --short` empty after a
path-scoped commit.

The documentation gates — lineage/boilerplate, layer contract, version
cross-check, figure registries, publication identity, and `AGENTS.md`'s
hardcoded scenario numbers — live in `tests/test_repo_contracts.py` and run
inside the first command. There is no separate `rg` one-liner; the one that
used to be documented here could not fail (`rg` exits non-zero on *no* match,
so `|| echo Clean` fired on success) and did not match the boilerplate it was
aimed at.

If `uv` reports `Failed to initialize cache` or `Operation not permitted`,
that is a sandbox restriction on the `uv` cache directory, not a package
failure — re-run with the sandbox disabled.

---

## Round-2 (2026-08-06)

Deep-improvement pass on top of the `0aa55c5` baseline. **All five gates green:
225 passed, 100.00% line+branch coverage on `src/` (floor 90), `ruff check`
clean, `ruff format --check` (33 files), `mypy` clean (13 files), mission CLI
`full` exits 0, manuscript hydration resolves every `{{TOKEN}}` strictly.**

### Fixes in this round (each with a regression test)

* **C1 — parabolic refinement of the bearing estimate.** `beamforming.py`
  gains `interpolate_peak_deg` and an opt-in `interpolate=True` keyword on
  `estimate_bearing_deg` (default stays grid-quantised, so existing callers
  and the honest grid story are unchanged). `run_canonical` now also reports
  `beam_estimate_interp_deg` / `beam_bearing_err_interp_deg`. Evidence:
  `tests/test_beamforming.py::TestInterpolation` asserts the refined error is
  strictly smaller than the grid error on an off-grid bearing and within a
  sensible factor of the CRB; `tests/test_scenario.py` pins the metric is
  finite and bounded. On the canonical (grid-aligned) case the refined error
  is `BEAM_BEARING_ERR_INTERP_DEG` (a sub-cell snapshot-noise residual, 0.11°,
  vs the grid's alignment-artefact 0.00° and a 0.33° CRB floor). **Left open:**
  the default grid behaviour is preserved by design.
* **E1 — the EKF now reaches the manuscript.** `run_canonical` runs the
  recursive filter on the same bearing sequence and reports steady-state RMS
  (`track_ekf_rms_m`, 804 m ≈ 8% of the ~10 km mean range) alongside the batch
  TMA. `tests/test_scenario.py::test_ekf_metric_is_finite_and_reportable`
  bounds it relative to the geometry and `test_canonical_ekf_constants_reach_*`
  pins every EKF seed as a scenario input (no hidden literals). Section
  @sec:results compares batch vs recursive accuracy from tokens.
* **D1 — detection is now reported.** `run_canonical` reports `detection_p_fa`
  (the detector is run at an explicit `DetectionConfig(p_fa=...)`), and
  `manuscript_variables` emits `DETECTED`, `DETECTION_MARGIN_DB`,
  `DETECTION_P_FA`. Section @sec:results gains a Detection subsection.
* **C4 — persisted mission outcome keeps its provenance.** `mission_cli.py`
  `execute` now writes `{"provenance": {...}, "results": {...}}` to
  `output/data/mission_outcome.json`; it used to write only `results`, so the
  input hash a reader would audit against was printed and discarded.
  `tests/test_scripts_smoke.py::test_mission_cli_execute_persists_provenance`
  asserts the file parses and its `input_hash == scenario.canonical_input_hash()`.
* **V2 — claim-ledger values are bound to the run.** New
  `TestDocsAgreeWithTheRun::test_claim_ledger_values_match_the_run` resolves
  every numeric ledger `value` against the live `run_canonical` metric (or the
  declared `_PHASE_DURATIONS` schedule) and fails on drift, so e.g. a
  `clearance_m` edit that leaves the ledger saying 1.5 now turns the suite red.
* **V3 — the version cross-check now covers all declaration sites.** The gate
  adds `manuscript/config.yaml.example`, `manuscript/AGENTS.md` and the agent
  `SKILL.md` frontmatter alongside the seven already checked (now 10 sites).
* **V4 — figures are asserted byte-deterministic.** New
  `test_figures.py::TestFigureDeterminism` renders `build_all_figures()` twice
  and compares PNG bytes, so a matplotlib bump or embedded timestamp fails the
  determinism claim instead of passing under an existence+size check.
* **D2 / D3 — docs hygiene.** `docs/README.md`'s lint command now includes
  `tests/` (matching README/AGENTS), and the `.agents/` scaffolding prose no
  longer describes the film package as a template "exemplar" to fork.

### Manuscript improvements

Added enough tokenised coverage for the compendium: an abstract that now
carries the detection margin/`P_FA`, both tracker results and the refined
bearing; a Detection subsection and an EKF-vs-batch paragraph in
@sec:results; a recursive-filter bullet and detection `P_FA` in @sec:setup;
reproducibility notes for the new figure-determinism, persisted-provenance and
ledger/version gates in @sec:reproducibility; and detection / EKF /
interpolation caveats in @sec:scope. Every number in the new prose is a
`{{TOKEN}}` resolved by `scripts/z_generate_manuscript_variables.py` — none is
hand-typed.

### What remains (unchanged and still open from the list above)

* **C2 / C3 — the capture timeline is still a declared schedule.** `_PHASE_DURATIONS`
  remains four uncited constants and the hatch-seal / approach phases still
  carry no discriminating predicate. This is labelled everywhere it appears and
  pinned as a schedule by `TestReportedTimeIsASchedule`; it would need a real
  (cited) timing model or a two-phase collapse to close — deliberately left for
  a future round rather than fabricated.
* **V1 — the EKF accuracy bound is still empirical.** The new canonical EKF
  metric is bounded relative to the geometry, but a true normalised-estimation-error
  (NEES) consistency check against the filter's own covariance `P` remains open.
* **E2 — the fleet provenance helper is still not wired.** `record_provenance_outcome`
  from `bond-utilities` is not yet called (C4 fixed the local JSON path; wiring
  the fleet helper is still pending the stable helper).
