# Style Guide — LIPARUS

1. **Zero mocks.** Tests exercise real, deterministic algorithms on real data.
2. **Pure domain core.** `sub_tracking.py`, `tanker_capture.py`,
   `vehicle_forensics.py` import neither `bond_api` nor `infrastructure`.
3. **Thin orchestrators.** `scripts/` delegate to `src/`; no domain math there.
4. **Show-not-tell.** Manuscript references name explicit functions/paths.
5. **Explicit paths.** No implicit working-directory dependence in imports.
6. **Type hints + docstrings** on all public API; `ruff` + `mypy` clean.
7. **Error messages** are actionable (mention the offending value and remedy).

Run: `uv run ruff format src/ scripts/ tests/`, `uv run ruff check src/ scripts/ tests/`,
`uv run mypy src/ scripts/`.
