# Agent Instructions — LIPARUS

Operational rules for AI agents and developers working inside
`projects/working/bond/the_spy_who_loved_me`. Read this before modifying any
file.

## Scope and identity

- This is a **PROJECT BOND film package** (codename **LIPARUS**) for *The Spy
  Who Loved Me (1977)*. Work only inside this directory; never touch sibling
  packages, bond root files, or the template repo.
- **Local-only tree**: no remote, never push. Commit path-scoped within this
  package's own git repo.

## The 7 hard rules

1. **Zero mocks.** No `unittest.mock`, `MagicMock`, `@patch`, or
   `create_autospec` anywhere in `tests/`. Tests exercise the real,
   deterministic algorithms on real (generated) data.
2. **≥90% coverage on `src/`.** Run `uv run pytest tests/ --cov=src
   --cov-fail-under=90`. Line and branch.
3. **Thin orchestrators in `scripts/`.** Business logic lives in `src/`;
   scripts delegate and shape argv only.
4. **Pure domain core is protocol-free.** `sub_tracking.py`,
   `tanker_capture.py`, `vehicle_forensics.py` must not import `bond_api` or
   `infrastructure`. Only `mission.py` imports `bond_api`.
5. **Show-not-tell in the manuscript.** Reference explicit functions/paths,
   not vague descriptions; every metric flows from
   `manuscript_variables.py`, never hand-authored in prose.
6. **Type hints, docstrings, ruff, mypy.** Sign public API; keep `ruff
   check`/`format` and `mypy` clean on `src/` and `scripts/`.
7. **Determinism.** Fixed seeds, no untracked RNG, no wall-clock in
   persisted artifacts.

## Mission protocol

`src/the_spy_who_loved_me/mission.py` implements the **frozen** `bond_api`
`MissionProvider` lifecycle (brief, recon, plan, execute, debrief). The
protocol types live in the `bond-api` path dependency (see `pyproject.toml`);
do not invent your own. The provider answers to slug `the_spy_who_loved_me`
and registers concept gadgets on a `GadgetRegistry`.

## Editing workflow

1. Read the relevant module and its tests before editing.
2. Make the change in `src/` (or a thin `scripts/` wrapper).
3. Add/update a deterministic test in `tests/`.
4. If a manuscript number changes, update the corresponding section to use
   the `{{TOKEN}}` from `manuscript_variables.generate_variables()`.
5. Run the full verification below before committing.

## Verification (run before “done”)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short   # clean after a path-scoped commit
```

## Documentation index

- `AGENTS.md` — layer contract + package identity.
- `architecture.md` — module boundaries and dependency direction.
- `testing_philosophy.md` — zero-mock policy + coverage mechanics.
