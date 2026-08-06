# docs/ — LIPARUS documentation

Documentation for **the_spy_who_loved_me**, the PROJECT BOND film package
for *The Spy Who Loved Me* (1977) under mission codename **LIPARUS**.

This directory holds the operational rulebook: what the package is, how it
is built, how an agent should work inside it, and why the tests are shaped
the way they are. It is a small, complete set — five files, no stubs, and no
index entries for documents that do not exist.

## Contents

| File | What it holds | Read it when |
|---|---|---|
| [`README.md`](README.md) | This index | You are orienting |
| [`AGENTS.md`](AGENTS.md) | How an agent should work inside this package: scope, invariants, the frozen-protocol rule, the change protocol, and the verification commands | Before touching any file |
| [`agent_instructions.md`](agent_instructions.md) | The concrete operational rules — the seven hard constraints and the editing workflow, stated as instructions rather than description | Before your first edit |
| [`architecture.md`](architecture.md) | Module-by-module architecture of `src/`: what each module computes, how they compose, and how `mission.py` implements the frozen `bond_api` `MissionProvider` | Before adding or moving a module |
| [`testing_philosophy.md`](testing_philosophy.md) | The no-mock / real-data / determinism doctrine as it applies here, plus what each test file actually pins | Before writing or changing a test |

## The package in one paragraph

LIPARUS models the engineering behind two set pieces from the film: the
*Liparus*, a supertanker that swallows submarines whole, and the Lotus
Esprit that converts into a working submersible. Six concept modules do the
domain work — passive acoustic detection and bearing-only tracking,
underwater propagation and the passive sonar equation, uniform-linear-array
beamforming, Liparus capture geometry, submersible vehicle conversion
forensics, and pressure-hull collapse and ballast analysis. Three further
modules hold it together: `scenario.py` (the canonical parameter set and
metric factory), `manuscript_variables.py` (token hydration), and
`mission.py` (the frozen `bond_api` adapter). Every module is deterministic,
every manuscript number is computed rather than typed, and nothing in the
pure core imports the protocol.

## Where the rest of the documentation lives

| Location | Holds |
|---|---|
| [`../README.md`](../README.md) | Quick start: install, run, verify |
| [`../AGENTS.md`](../AGENTS.md) | Package identity and the layer contract table |
| [`../TODO.md`](../TODO.md) | Remaining work and declared integration points |
| [`../STANDALONE.md`](../STANDALONE.md) | Running this package outside the BOND suite |
| [`../src/AGENTS.md`](../src/AGENTS.md), [`../src/STYLE.md`](../src/STYLE.md) | Source-tree conventions |
| [`../scripts/AGENTS.md`](../scripts/AGENTS.md) | Thin-orchestrator rules for the CLIs |
| [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md), [`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md) | Manuscript authoring: token protocol, figure labels, citation syntax |
| [`../manuscript/layer_contract.yaml`](../manuscript/layer_contract.yaml) | Machine-readable statement of which module may import what |

## Verification

Run all three from the package root. They are the whole gate.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/
```

The coverage floor is `fail_under` in `[tool.coverage.report]` of
`pyproject.toml`, and that is the single source of the number — the
manuscript reads it through `manuscript_variables.coverage_floor_pct()`
rather than restating it, so prose cannot claim a stricter gate than the one
that actually runs.

## Lineage

This package was scaffolded from the repository's generic code-project
exemplar and then rewritten for its own domain. That lineage is why the
directory shapes (`src/`, `scripts/`, `tests/`, `manuscript/`, `docs/`) match
the other BOND packages.

No exemplar code remains — but exemplar *prose* did, for longer than anyone
noticed. `STANDALONE.md` was wholesale un-rewritten scaffold text describing
an optimizer project, and `.agents/skills/…/SKILL.md` described the package
as a convergence-analysis exemplar. Both are rewritten now, and
`tests/test_repo_contracts.py::TestNoExemplarBoilerplate` fails on the
boilerplate itself rather than on one spelling of the exemplar's name — which
is why the old `rg` lineage check never saw it.
