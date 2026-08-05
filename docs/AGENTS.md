# docs/AGENTS.md — working inside LIPARUS

How an agent should operate inside
`projects/working/bond/the_spy_who_loved_me`. Read this before the first
edit; [`agent_instructions.md`](agent_instructions.md) is the shorter
command-level companion.

## Scope

Your scope is exactly this directory. Do not touch a sibling BOND package,
the bond root files, or the template repository. This is a **local-only**
tree with **no git remote** — commit here, never push.

## The five invariants

These are the properties the gate enforces. Everything else is style.

1. **No mock framework, and no dependency replacement either.** No
   `unittest.mock`, `MagicMock`, `mocker.patch`, or `create_autospec`
   anywhere in `tests/`, and no `monkeypatch.setattr` substituting a
   production callable. Every test runs the real algorithm on real,
   generated data. The suite briefly carried
   `monkeypatch.setattr(mv_module, "run_canonical", degenerate)` and
   defended it as environment isolation; a function being stood in for is a
   stand-in whatever it is called. The strict output gate is now the pure
   predicate `manuscript_variables.check_metrics(metrics)`, exercised by
   handing it a genuine metric dict with one field degraded.
2. **Determinism.** Fixed seeds (`scenario.SEED`), no untracked RNG, no
   wall-clock in persisted artefacts. `run_canonical() == run_canonical()`
   is a test.
3. **Coverage at or above the floor** in `[tool.coverage.report]
   fail_under`, line *and* branch, on `src/`.
4. **Thin orchestrators.** `scripts/` shapes argv and prints; every piece of
   domain math lives in `src/`.
5. **No hand-authored metric in manuscript prose.** Numbers arrive as
   `{{TOKEN}}`s from `manuscript_variables.generate_variables()`. The strict
   resolver fails the build on any leftover token, and
   `tests/test_manuscript_variables.py` fails on any prose token that has no
   generator behind it.

## The frozen surface — do not change its shape

`src/the_spy_who_loved_me/mission.py` is consumed across packages by
`bond-cli`, `bond-coordinator`'s reconcile, and `bond-orchestrator`'s
discovery. The following are **frozen in public shape**:

| Surface | Contract |
|---|---|
| `MissionProvider` class at module top level | Discovery imports `<slug>.mission` and instantiates this name |
| `brief()` / `recon(request)` / `plan(brief)` / `execute(plan)` / `debrief(outcome)` | The five lifecycle methods and their `bond_api.protocol` types |
| `MissionProvider.film` | Must equal the package slug, `the_spy_who_loved_me` |
| Module-level `GADGETS` registry | The fleet enumerates gadgets from it |

Deepening happens *inside*: add modules, enrich what `execute` computes,
extend the gadget mapping. Renaming a method, changing a signature, or
moving `GADGETS` breaks three other packages silently — discovery will
simply find nothing rather than raise.

## The layer contract

`manuscript/layer_contract.yaml` is the machine-readable version. In prose:

- The **six concept modules** plus `scenario.py` are pure. They import numpy
  and the standard library and nothing else from this repository's world —
  no `bond_api`, no `infrastructure`. They must remain importable with the
  protocol absent.
- **`mission.py` alone** imports `bond_api`. It is the only file that knows
  a protocol exists.
- **`manuscript_variables.py`** imports `scenario` and reads
  `manuscript/config.yaml` and `pyproject.toml`. It computes no domain math
  of its own.
- **`scripts/`** import from `src/` and print. No math.

Verify the contract holds:

```bash
uv run pytest tests/test_repo_contracts.py::TestLayerContract -v
```

`TestLayerContract` parses `manuscript/layer_contract.yaml` and checks that
every listed path exists, that every module under `src/` and `scripts/` is
covered by exactly one section, that no pure-core file imports `bond_api` or
`infrastructure`, that the set of `bond_api` importers is within the declared
adapter/script list, and that nothing anywhere imports `infrastructure`.

Two shell one-liners used to stand here:

```bash
grep -rln "bond_api" src/the_spy_who_loved_me/ | grep -v "mission.py" \
  || echo "OK — only mission.py references the protocol"
```

Neither could fail. `grep` exits non-zero when it finds *nothing*, so the
`|| echo "OK"` branch fired on a clean tree and a violation printed a
filename while the command still exited 0. Nothing consumed the exit status
anyway. And until the pytest gate landed, nothing at all read
`layer_contract.yaml` — `docs/README.md` billed it as "the machine-readable
statement of which module may import what" while the discipline it encodes
was enforced only by prose.

## Change protocol

1. **Read before writing.** Read the module and its test file. `scenario.py`
   is the parameter set of record — if a number appears in two places, one
   of them is wrong.
2. **Change `src/`, not `scripts/`.** If the change is math, it belongs in a
   concept module.
3. **Add a test that could fail.** Not a shape assertion — a test that pins
   a value or a property and would go red if the behaviour inverted. Prefer
   a case that exercises the branch you added.
4. **If a metric changed**, add or update the variable in
   `manuscript_variables.generate_variables()` and reference the token in
   prose. Never type the number.
5. **If the scenario changed**, expect every downstream token to move. That
   is correct; the manuscript re-hydrates.
6. **Run the gate** (below) and commit path-scoped inside this repo.

## A note on green-by-construction

Several traps have already been found and fixed here; all are worth
recognising in new work.

- A **dead conjunct in a documented predicate**. `simulate_capture`'s secure
  stage read `length_clearance >= clearance and bay.seal_requirement <= 1.0`
  while `BayConfig.__post_init__` had already validated `seal_requirement`
  into `[0, 1]`. The second term could never be false, so the docstring's
  "and a seal is achievable at the bay's integrity requirement" described a
  test that did not exist. The field is gone and the predicate is stated as
  the geometry it is.
- A **units defect invisible under 100% coverage**. The EKF put a bearing
  standard deviation into the measurement-*variance* slot. Every EKF test
  asserted `.shape`, so nothing went red. Shape assertions are not accuracy
  assertions; `tests/test_sub_tracking.py::TestEkfActuallyEstimates` now
  bounds the estimate against truth with a threshold that sits between the
  correct and the buggy behaviour.
- A **constant reported as a result**. See the capture-timeline caveat in
  [`../AGENTS.md`](../AGENTS.md).
- A **fixed literal in a provenance hash**. `input_hash` was
  `"liparus-mission-input"` — it identified the package, not the inputs, and
  could not change when the scenario did.

- The canonical beamforming scenario places the true bearing at exactly
  30 degrees, which lands on a node of the 0.5-degree scan grid. The
  measured error is therefore exactly zero — *below* the Cramer-Rao bound,
  which no unbiased estimator can achieve. Asserting on that zero would be a
  test that passes by construction. `tests/test_beamforming.py` pins the
  quantisation property on **off-grid** bearings instead, where the
  assertion can actually fail, and Section 3 of the manuscript states the
  artefact explicitly rather than reading it as precision.
- The element SNR fed to the Cramer-Rao bound is *derived* from the snapshot
  amplitude and noise standard deviation rather than declared as its own
  constant, because a declared constant would silently describe a different
  array the moment either parameter moved.

When you add a gate, ask what input would make it fail, then write that
input down as a test.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/
uv run python scripts/mission_cli.py full                  # protocol still drivable
uv run python scripts/z_generate_manuscript_variables.py   # tokens still resolve
git status --short                                         # clean after commit
```

The manuscript hydration step is part of the gate, not a nicety: it is what
proves every `{{TOKEN}}` in prose still has a generator behind it.

If a `uv` command fails with `Failed to initialize cache` or `Operation not
permitted`, that is a sandbox restriction on the cache directory, not a
package failure — re-run it with the sandbox disabled.

## Cross-references

- [`README.md`](README.md) — index of this directory
- [`architecture.md`](architecture.md) — module-by-module structure
- [`testing_philosophy.md`](testing_philosophy.md) — what the tests pin and why
- [`../AGENTS.md`](../AGENTS.md) — package identity and layer-contract table
- [`../TODO.md`](../TODO.md) — remaining work and integration points
