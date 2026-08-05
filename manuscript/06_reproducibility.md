# Reproducibility {#sec:reproducibility}

LIPARUS is reproducible by construction.

* **Determinism**: every algorithm is a pure function of its inputs and a
  fixed seed; the simulator uses no untracked random draws and no wall-clock
  value in persisted artefacts. Re-running the canonical scenarios on one
  interpreter yields byte-identical results, which
  `tests/test_manuscript_variables.py::TestPersistedArtefactIsDeterministic`
  enforces by regenerating the variable map twice and comparing it, and by
  rejecting any token whose value parses as a timestamp. The single
  environment-dependent token is `PYTHON_VERSION`, which is reported in
  Section @sec:setup precisely so a reader can tell which interpreter a given
  artefact came from; the claim is byte-identity per interpreter, not across
  interpreters. (A `GENERATION_TIMESTAMP` token used to be written into
  `output/data/manuscript_variables.json`, which made every regeneration
  differ and this bullet false. It was removed, not softened — no manuscript
  section consumed it.)
* **Seeding**: the tracking scenario is driven by a fixed seed and the
  mission provider carries that same `seed` in its `Provenance`, alongside
  the package version ({{LIPARUS_VERSION}}) and an input hash.
* **Input hash**: the `Provenance.input_hash` is a SHA-256 over a stable
  serialisation of the canonical parameter set
  (`scenario.canonical_input_hash`), so editing any canonical input changes
  it and re-running unchanged inputs does not. It was previously the fixed
  string `"liparus-mission-input"`, which identified the package rather than
  the inputs and could not have changed if the scenario had — the one thing
  an input hash exists to detect.
  `tests/test_scenario.py::TestCanonicalInputHash` perturbs every parameter
  in turn and asserts the digest moves, so a parameter that stops reaching
  the hash fails the suite.
* **Real data only**: tests exercise the actual algorithms on generated,
  deterministic data — no mock framework anywhere in `tests/`.
* **Regenerable artefacts**: figures and reports land under `output/`, which
  is git-ignored; `scripts/generate_figures.py` and
  `scripts/z_generate_manuscript_variables.py` rebuild them deterministically.
* **Verification**: `uv run pytest tests/ --cov=src --cov-fail-under=90`,
  `ruff check`/`format`, `mypy`, and the lineage scan are the acceptance
  gate before any commit.
