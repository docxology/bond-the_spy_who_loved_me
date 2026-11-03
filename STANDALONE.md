# Standalone Fork Guide

Running `the_spy_who_loved_me` (LIPARUS) outside the PROJECT BOND suite.

## Publication identity: there is none

This package is **not published anywhere**. It has:

- no public remote — the only git remote is a private handoff mirror, and
  nothing here is released or pushed to a public host;
- no DOI, reserved or deposited;
- no PyPI, Zenodo, HuggingFace, OSF, IPFS, Software Heritage, GitHub Pages
  or Netlify presence;
- no release tag.

The only identity it carries is the version in `pyproject.toml`, mirrored in
`manuscript/config.yaml`, `CITATION.cff`, `codemeta.json`, `.zenodo.json` and
`mission.PACKAGE_VERSION` — and cross-checked across all six by
`tests/test_repo_contracts.py::TestVersionIsDeclaredOnce`.
`manuscript/config.yaml` records the same thing in prose: *"The only git remote
is this package's own repository; no DOI has been minted and no deposit exists.
Metadata is kept minimal and honest."*

`CITATION.cff`, `codemeta.json` and `.zenodo.json` exist as *prepared*
metadata for a deposit that has not happened. They are not evidence that one
has.

> This section replaced a generated `PUBLICATION_INDEX` block that asserted a
> standalone GitHub repository, a Zenodo concept DOI and version DOI, a Test
> PyPI release at version 2.5.2, and HuggingFace / IPFS / OSF / Netlify /
> Software Heritage locations. None of those exist. The block was boilerplate
> carried in from the template exemplar this package was scaffolded from, and
> every identifier in it was fabricated relative to this tree.
> `tests/test_repo_contracts.py::TestNoFabricatedPublicationIdentity` now
> fails if any such claim reappears in the documentation.

## Purpose

LIPARUS models six deterministic concepts from *The Spy Who Loved Me* (1977):
passive acoustic detection and bearing-only tracking, underwater propagation
and the passive sonar equation, uniform-linear-array beamforming,
Liparus-class tanker capture geometry, submersible vehicle conversion
forensics, and pressure-hull collapse and ballast analysis. It exposes them
to the BOND fleet through the frozen `bond_api.MissionProvider` protocol.

## What "standalone" means here

The six concept modules plus `scenario.py` import nothing but the standard
library, `numpy` and each other. They run with no `bond_api` and no template
`infrastructure` on the path:

```bash
uv run python -c "
import sys; sys.path.insert(0, 'src')
from the_spy_who_loved_me.scenario import run_canonical
print(run_canonical()['hull_collapse_depth_m'])
"
```

Four surfaces are *not* standalone, by design:

| Surface | Needs |
|---|---|
| `src/the_spy_who_loved_me/mission.py` | `bond_api` (the frozen protocol; a local path dependency declared in `pyproject.toml`) |
| `scripts/mission_cli.py` | `bond_api.serialization`, via `mission.py` |
| `src/the_spy_who_loved_me/figures/plots.py` | `matplotlib` |
| `src/the_spy_who_loved_me/manuscript_variables.py` | `pyyaml`, plus the on-disk `manuscript/config.yaml` and `pyproject.toml` |

Nothing here imports the template repository's `infrastructure` package.
`manuscript/layer_contract.yaml` states this machine-readably and
`tests/test_repo_contracts.py::TestLayerContract` enforces it.

## Forking it

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude '.mypy_cache/' --exclude 'output/' --exclude '*.egg-info/' \
  --exclude '.git/' \
  the_spy_who_loved_me/ ../my_project/
```

Then, at minimum:

1. Rename the package directory under `src/` and update `pyproject.toml`
   (`[project] name`), `mission.py` (`FILM`, `CODENAME`, `PACKAGE_VERSION`),
   and every `from the_spy_who_loved_me...` import.
2. Rewrite `manuscript/config.yaml`, `CITATION.cff`, `codemeta.json`,
   `.zenodo.json`, `domain_profile.yaml` and `experiment_plan.yaml` for the
   fork — **including deleting this file's identity claims**, which are about
   *this* tree.
3. Replace the domain modules and `scenario.py` with the fork's own research
   code, and replace the manuscript sections and figures with its own.
4. Repoint `[tool.uv.sources] bond-api`, or drop `mission.py` entirely if the
   fork is not a BOND film package.

## Validation

From the package root, after `uv sync --extra dev`:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/
uv run python scripts/mission_cli.py full
uv run python scripts/z_generate_manuscript_variables.py
```

## What not to claim

Do not carry any number, figure, or result from this tree into a fork's prose
until `scripts/z_generate_manuscript_variables.py` has been re-run against the
fork's own code. Every `{{TOKEN}}` in `manuscript/[0-9]*.md` resolves from a
live run, so a stale token is a stale claim.

Do not describe a fork as published, archived, or citable by DOI until it
actually is.
