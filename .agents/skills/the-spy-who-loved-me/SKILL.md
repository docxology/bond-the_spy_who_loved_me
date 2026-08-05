---
name: the-spy-who-loved-me
description: LIPARUS — deterministic mission software for The Spy Who Loved Me (1977) — passive acoustic detection and bearing-only tracking, underwater propagation and the passive sonar equation, ULA beamforming, Liparus-class tanker capture geometry, submersible conversion forensics, and pressure-hull collapse and ballast analysis, behind the frozen bond_api MissionProvider.
version: 0.1.0
author: docxology
license: MIT
tags: [bond, mission-provider, sonar, tracking, deterministic, thin-orchestrator]
---

# the-spy-who-loved-me

Project-scoped skill for the PROJECT BOND film package at
`projects/working/bond/the_spy_who_loved_me/`. Load this when working inside
the package.

> This file previously described a code-centric numerical-optimisation
> research exemplar, with a dashboard and a convergence study, and pointed at
> template pipeline stages that this package does not have. That was
> un-rewritten scaffold boilerplate from the exemplar the package was copied
> from; none of it was ever true here.

## When to Use

- Working inside `the_spy_who_loved_me` — running the mission CLI, editing a
  domain module, regenerating figures or manuscript tokens.
- Checking that the package's contracts still hold: the layer contract
  (`manuscript/layer_contract.yaml`), the no-mock rule, determinism, and the
  live manuscript-token cross-reference.

## Quick Reference

All commands run **from the package directory**, not the monorepo root.

```bash
uv sync --extra dev

uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/

uv run python scripts/mission_cli.py full                # brief→recon→plan→execute→debrief
uv run python scripts/generate_figures.py                # five figures to output/figures/
uv run python scripts/z_generate_manuscript_variables.py # hydrate every {{TOKEN}}
```

If `uv` reports `Failed to initialize cache` or `Operation not permitted`,
that is a sandbox restriction on the `uv` cache directory, not a package
failure.

## Pitfalls

- **The `bond_api` surface is frozen.** `MissionProvider`'s five methods and
  the module-level `GADGETS` registry must not change shape.
- **Only `mission.py` may import `bond_api`.** Nothing anywhere imports the
  template `infrastructure` package. `tests/test_repo_contracts.py` enforces
  both against `manuscript/layer_contract.yaml`.
- **No mock framework.** Real data, real computation, fixed seeds.
- **No number is typed into prose.** Every manuscript figure flows from
  `scenario.run_canonical()` through `manuscript_variables.generate_variables()`
  as a `{{TOKEN}}`.
- **Outputs are disposable.** Never hand-edit `output/`; regenerate it.
- **Know which reported numbers are schedules, not results.** The capture
  `total_time_s` is a sum of declared per-phase constants and carries no
  information about the submarine or the bay — see `tanker_capture` and
  `manuscript/03_results.md`.

## Cross-refs

- Package contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Architecture and testing doctrine: [`docs/`](../../../docs/README.md)
