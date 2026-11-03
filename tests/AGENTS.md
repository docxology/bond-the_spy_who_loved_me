# tests/ — agent guidance

The reader's view is [README.md](README.md); the package rules are in [the root guide](../AGENTS.md);
the doctrine is [`docs/testing_philosophy.md`](../docs/testing_philosophy.md).

## Run it

From the repository root:

```bash
python -m pytest tests/ -q --cov=src --cov-fail-under=90
```

The documented form is `uv run pytest tests/ ...`. Prefer the interpreter form (`python -m pytest`): a
relocated `.venv` can leave a `pytest` console script that runs a different environment's pytest and
exits zero, which reads as a gate that passed when it never ran.

A worktree cut outside the vault has no `.venv` and no sibling `../bond-api` checkout, which
`[tool.uv.sources]` needs. Run it with an interpreter that already exists — for example the parent
repository's `.venv/bin/python`.

**Dated:** as of 2026-11-03 the vendoring change in this suite replaces the `../bond-api` path
dependency with a `vendor/bond-api` directory, after which an ordinary `uv sync` in a worktree resolves
locally. Re-check this paragraph if that change has landed here.

## Rules

- **Zero mocks.** Tests run the real algorithms on real inputs; `conftest.py` says so at the top, and
  nothing here imports a mock framework.
- **A claim in prose needs a gate.** This is the package's own lesson, recorded in
  `test_repo_contracts.py`: a tree full of green tests once carried documents that were false. If you
  state a number, a version, a figure set or a contract in a document, either bind it to a
  recomputation or leave it out — `docs/_generated/COUNTS.md` is where measured figures belong.
- **The layer contract is enforced, not described.** `manuscript/layer_contract.yaml` plus the contracts
  suite hold the pure core free of the protocol and of infrastructure; only `mission.py` may import
  `bond_api`. A new module that needs the protocol is an adapter, and belongs where the contract says.
- **The canonical scenario is the single source of truth.** A quantity computed anywhere else is a
  second source that can disagree with the manuscript.
- **New documents join the scan set.** `tests/test_repo_contracts.py` walks every authored `.md`,
  `.yaml`, `.json`, `.cff` and `.toml` in the package and checks them against the publication-identity,
  boilerplate and figure-registry rules. A folder guide added here is scanned like any other document,
  so keep it free of publication-looking addresses, of exemplar scaffold language, and of hardcoded
  figures that no gate recomputes.
- **The beamformer's zero bearing error is grid-limited**, not a result: the canonical true bearing
  lands on a scan-grid node. The root guide records the caveats; `test_beamforming.py` pins the
  quantisation property where it can actually fail.

## What is absent here

No CI: this repository carries no `.github/` directory, so nothing runs this suite unless a person or a
lane invokes it. No coverage baseline is recorded in the package either; the run prints what it
measured.
