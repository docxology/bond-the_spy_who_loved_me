# Testing Philosophy — LIPARUS

Why the suite is shaped the way it is, and what each file actually pins.

## No mock framework, and no dependency replacement

No `unittest.mock`, `MagicMock`, `mocker.patch`, or `create_autospec`
anywhere in `tests/`. Every test runs a **real algorithm on real, generated,
deterministic data**.

The reason is not purity. A mocked test asserts on call signatures, so it
stays green while the mathematics underneath it rots — a detector that
returns the wrong threshold, a bisection that converges to the wrong root,
and a buckling formula with a cubed term dropped all pass a mock-based suite
unchanged. Here the numbers are cheap to compute exactly, so there is no
reason to substitute anything.

**The suite is also free of `monkeypatch.setattr` on production callables.**
This section used to say something weaker and self-serving. It read:

> There is exactly one use of `pytest.MonkeyPatch` in the suite […] Nothing
> is stood in for; the real algorithms still produce the baseline. That is
> environment isolation.

The code it described was
`monkeypatch.setattr(mv_module, "run_canonical", degenerate)` — a locally
defined function installed over a production dependency for the duration of
a test. That is a dependency replacement. No mock *framework* was imported,
so the narrower claim survived, but the taxonomy this project inherits
counts substituted dependencies whether or not a library helped, and calling
it environment isolation did not make it one.

The fix was structural, not editorial. `_canonical_metrics` now delegates to
`manuscript_variables.check_metrics(metrics)`, a pure predicate over an
already-computed mapping. Exercising the guard means calling it with a real
`run_canonical()` dict that has one field degraded — the algorithms still
run, nothing is substituted, and the gate is still provably able to fire.

## Determinism

Every test is reproducible to the bit. Seeds are fixed (`scenario.SEED`),
`numpy.random.default_rng(seed)` is the only entropy source, and no test
reads the wall clock. `test_scenario.py::test_run_canonical_is_deterministic`
asserts `run_canonical() == run_canonical()` on the whole metric dict, which
would catch any dict-ordering, floating-point-accumulation, or hidden-global
regression across the entire package in one assertion.

Figures render under `MPLBACKEND=Agg`, pinned in `tests/conftest.py`, so
plotting never depends on a display.

## Tests that can fail

A test that cannot fail is worse than no test, because it reports safety it
does not provide. Two specific hazards have been hit in this package and are
now guarded:

**Grid alignment.** The canonical beamforming scenario places the true
bearing at exactly 30 degrees, which lands on a node of the 0.5-degree scan
grid, so the measured error is exactly zero — below the Cramer-Rao bound,
which no unbiased estimator can achieve. Asserting on that zero would pass
by construction and prove nothing about the estimator.
`TestScanGridQuantisation` therefore uses bearings placed deliberately
*between* nodes, asserts the estimate snaps to a node, asserts the error is
bounded by half a cell, asserts the error is strictly non-zero (so the bound
is not vacuous), and asserts a finer grid reduces it.

**Restated constants.** `test_beam_snr_is_derived_from_the_snapshot_not_declared`
re-derives the element SNR from the snapshot amplitude and noise standard
deviation, so an edit to either that failed to update the SNR fails here
rather than silently mis-stating the Cramer-Rao bound in the manuscript.
`test_beam_scan_step_is_read_off_the_estimator_grid` does the same for the
quantisation floor.

**Shape assertions in place of accuracy assertions.** Every EKF test used to
end at `.shape`, so a units defect — a bearing standard deviation sitting in
the measurement-*variance* slot — was invisible under 100% coverage.
`TestEkfActuallyEstimates` bounds the estimate against truth with a threshold
placed between the correct behaviour (8.0% of mean range) and the buggy one
(9.9%), and separately asserts `R == sigma**2`.

**Restating a constant as a result.** `test_successful_capture_phases` used
to assert `total_time_s == 630.0  # 240+180+90+120`, which pinned the sum of
four declared constants and read as a timing result.
`TestReportedTimeIsASchedule` instead pins that the total *is* the schedule
sum for the phases that ran, that an aborted run reports less, and that two
very different submarines report the same — the properties that are actually
true of it.

**A gate nothing runs.** `manuscript/layer_contract.yaml` was documented as
the machine-readable import contract and was read by no script, test or hook.
`tests/test_repo_contracts.py` reads it now, along with the version
declarations, the figure registries, and the documentation-lineage scan whose
shell predecessor could not fail.

When adding a gate, write down the input that would make it fail. If no such
input exists, the gate is decoration. Then actually feed it that input once,
and watch it go red.

## What each test file pins

| File | Pins |
|---|---|
| `test_acoustics.py` | Thorp absorption monotonicity and magnitude; spherical vs cylindrical spreading; the sonar equation against a hand-checkable budget; bisection convergence, the capped-range branch, and the inaudible-at-1 m `converged=False` branch; Mackenzie sound speed across the valid envelope; input validation |
| `test_beamforming.py` | Steering-vector phase progression and validation; snapshot determinism under a fixed seed; delay-and-sum peak location; CRB decreasing with SNR and element count and diverging at endfire; scan-grid quantisation on off-grid bearings |
| `test_sub_tracking.py` | Neyman–Pearson decisions with signal present and absent at controlled `P_FA`; Wilson–Hilferty and Acklam quantile properties; deterministic scenario generation; batch TMA convergence against truth with a manoeuvring ownship; **EKF steady-state accuracy against truth and the `R = sigma**2` convention**; **the coarse-search envelope's real limits, on both sides**; `tracking_rms_error` |
| `test_tanker_capture.py` | Clearance metrics and the `fits` / `tight` / `denied` classification; stowage capacity; the full four-phase capture success path and each failure path; **that the reported time is the declared schedule for the phases run, not a result**; **that the secure predicate is hold-length geometry and nothing else** |
| `test_vehicle_forensics.py` | Requirement traceability; readiness classification across all three classes; explicit-`False` and omitted systems agreeing, with no double-counting; the `amphibious` predicate matching its docstring; Archimedean buoyancy in all three states; upgrade ordering |
| `test_hull_forensics.py` | Hoop stress; long-cylinder buckling; yield pressure; collapse pressure taking the governing minimum in both regimes; collapse depth; safety factor; ballast volume sign convention; input validation |
| `test_scenario.py` | The canonical run being complete, deterministic, and seeded; reported setup parameters re-derived from measured output rather than restated; derived SNR and scan step; **the provenance input hash moving when any canonical parameter moves, and covering every scenario constant** |
| `test_mission.py` | The frozen `bond_api.MissionProvider` lifecycle; runtime-checkable protocol conformance; deterministic results; gadget registration and lookup through `GadgetRegistry` |
| `test_manuscript_variables.py` | Config loading and its two rejection paths; the live token cross-reference over `manuscript/[0-9]*.md`; strict and non-strict tree resolution; the coverage floor matching `pyproject.toml`; each strict output guard firing, via a pure predicate rather than a substituted dependency; **the persisted variable map being identical across regenerations, and carrying no wall-clock value under any name** |
| `test_figures.py` | All five figures rendering to non-empty files; the capture-feasibility colour branches for all three fit classes |
| `test_scripts_smoke.py` | The thin CLIs run as subprocesses with `sys.executable`, exit zero, and write the artefacts they claim to |
| `test_repo_contracts.py` | **The documentation against the package**: one version across ten declaration sites; the layer contract in `manuscript/layer_contract.yaml` actually enforced; the figure registries equal to `build_all_figures()`; no fabricated publication identity in any document; no exemplar boilerplate; `AGENTS.md`'s hardcoded scenario numbers equal to the canonical run; the claim ledger pointing at files and symbols that exist |

## The live cross-reference

`test_manuscript_variables.py` scans every `manuscript/[0-9]*.md` for
`{{TOKEN}}` patterns and asserts each one has a key in
`generate_variables()`. This is what makes "no hand-authored metrics" an
enforced property rather than a convention: prose can only quote a number
that some code path computed. The complementary direction — a token with no
prose consumer — is harmless and not gated.

## The gate

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Line **and** branch coverage on `src/`, at or above the floor declared in
`[tool.coverage.report] fail_under`. That floor is the single source of the
number; `manuscript_variables.coverage_floor_pct()` reads it so the
manuscript cannot quote a different one.

Coverage is a floor, not a target. A hundred percent of lines executed by
assertions that check nothing is worth less than eighty percent under
assertions that pin values — which is why the table above describes what
each file *pins* rather than what it touches.
