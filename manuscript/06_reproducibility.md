# Reproducibility

LIPARUS is reproducible by construction.

* **Determinism**: every algorithm is a pure function of its inputs and a
  fixed seed; the simulator uses no untracked random draws and no wall-clock
  in persisted artefacts. Re-running the canonical scenarios yields
  byte-identical results.
* **Seeding**: the tracking scenario is driven by a fixed seed and the
  mission provider carries a fixed `seed` in its `Provenance`, alongside the
  package version ({{LIPARUS_VERSION}}) and an input hash, so any outcome
  can be audited without re-execution.
* **Real data only**: tests exercise the actual algorithms on generated,
  deterministic data — no mock framework anywhere in `tests/`.
* **Regenerable artefacts**: figures and reports land under `output/`, which
  is git-ignored; `scripts/generate_figures.py` and
  `scripts/z_generate_manuscript_variables.py` rebuild them deterministically.
* **Verification**: `uv run pytest tests/ --cov=src --cov-fail-under=90`,
  `ruff check`/`format`, `mypy`, and the lineage scan are the acceptance
  gate before any commit.
