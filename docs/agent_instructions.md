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

## The 8 hard rules

1. **Zero mocks.** No `unittest.mock`, `MagicMock`, `@patch`, or
   `create_autospec` anywhere in `tests/`. Tests exercise the real,
   deterministic algorithms on real (generated) data. The single
   `pytest.MonkeyPatch` use in `tests/test_manuscript_variables.py` degrades
   one field of a genuinely-computed metric dict so the strict output gate
   can be proven to fire — environment isolation, not a stand-in.
2. **Coverage at or above the floor on `src/`.** Run `uv run pytest tests/
   --cov=src --cov-fail-under=90`. Line and branch. The floor of record is
   `[tool.coverage.report] fail_under` in `pyproject.toml`; do not quote a
   coverage number in prose, cite the gate or use the
   `{{COVERAGE_FLOOR_PCT}}` token.
3. **Thin orchestrators in `scripts/`.** Business logic lives in `src/`;
   scripts delegate and shape argv only.
4. **Pure domain core is protocol-free.** All six concept modules —
   `sub_tracking.py`, `tanker_capture.py`, `vehicle_forensics.py`,
   `acoustics.py`, `beamforming.py`, `hull_forensics.py` — plus
   `scenario.py` must not import `bond_api` or `infrastructure`. Only
   `mission.py` imports `bond_api`.
5. **One source per constant.** Canonical scenario parameters live in
   `scenario.py` and nowhere else. If a value can be derived from another,
   derive it rather than restating it — a restated constant is a silent
   drift waiting to happen.
6. **Show-not-tell in the manuscript.** Reference explicit functions/paths,
   not vague descriptions; every metric flows from
   `manuscript_variables.py`, never hand-authored in prose.
7. **Type hints, docstrings, ruff, mypy.** Sign public API; keep `ruff
   check`/`format` and `mypy` clean on `src/` and `scripts/`.
8. **Determinism.** Fixed seeds, no untracked RNG, no wall-clock in
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
3. Add/update a deterministic test in `tests/`. Before writing it, name the
   input that would make it fail; if there is none, the test is decoration.
4. If a manuscript number changes, update the corresponding section to use
   the `{{TOKEN}}` from `manuscript_variables.generate_variables()`.
5. If you added a scenario parameter, report it from `run_canonical()` and
   token it, rather than typing it into the experimental-setup section.
6. Run the full verification below before committing.

## Verification (run before “done”)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short   # clean after a path-scoped commit
```

## Documentation index

- [`README.md`](README.md) — index of this `docs/` directory.
- [`AGENTS.md`](AGENTS.md) — scope, the five invariants, the frozen mission
  surface, the layer contract, and the change protocol.
- [`architecture.md`](architecture.md) — what each module in `src/`
  computes, how they compose, and how `mission.py` implements the frozen
  `MissionProvider`.
- [`testing_philosophy.md`](testing_philosophy.md) — the no-mock/real-data/
  determinism doctrine and a per-file table of what the suite pins.
- [`../AGENTS.md`](../AGENTS.md) — package identity and layer-contract table.
