# scripts/ — LIPARUS thin orchestration

Thin CLI wrappers around `src/`. No domain math lives here.

| Script | Purpose |
|---|---|
| `mission_cli.py` | Mission phases: `brief`, `recon`, `plan`, `execute`, `debrief`, `full` |
| `generate_figures.py` | Render the five concept figures to `output/figures/` |
| `z_generate_manuscript_variables.py` | Hydrate `{{TOKEN}}`s + render figures (runs last) |

Scripts self-insert `src/` into `sys.path`; run with `uv run python scripts/<x>.py`
from the package root. Smoke-tested via subprocess in `tests/test_scripts_smoke.py`.
