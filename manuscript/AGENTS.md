---
title: "Manuscript directory: the_spy_who_loved_me (LIPARUS)"
type: "manuscript_guide"
version: "0.1.0"
---

# Manuscript (`projects/working/bond/the_spy_who_loved_me/manuscript/`)

Operational rules for the LIPARUS manuscript. Repository-wide agent rules live
in [`../docs/agent_instructions.md`](../docs/agent_instructions.md).

## File roles

| File | Role |
|---|---|
| `00_abstract.md` – `07_scope_and_related_work.md` | Numbered prose sections |
| `99_references.md` | Bibliography |
| `config.yaml` | Paper identity + mission block (loaded by `manuscript_variables.py`) |
| `config.yaml.example` | Reference copy |
| `layer_contract.yaml` | Layer contract (pure core / adapter / scripts) |
| `references.bib` | BibTeX |
| `preamble.md` | LaTeX injections for PDF rendering |
| `SYNTAX.md` | Token / figure / citation reference |

## Token protocol

Every metric is a `{{TOKEN}}` resolved through
`src/the_spy_who_loved_me/manuscript_variables.py::generate_variables()`.
Never hardcode a result in prose. The live cross-reference test
(`tests/test_manuscript_variables.py`) fails if any prose token is missing
from the generator.

Pipeline: `uv run python scripts/z_generate_manuscript_variables.py`
writes `output/data/manuscript_variables.json` and the resolved tree to
`output/manuscript/`.

## Figure protocol

Reference figures by Pandoc-crossref label, never a hardcoded number:

| Label | File |
|---|---|
| `fig:bearing_track` | `output/figures/bearing_track.png` |
| `fig:beamforming_response` | `output/figures/beamforming_response.png` |
| `fig:sonar_detection_range` | `output/figures/sonar_detection_range.png` |
| `fig:capture_feasibility` | `output/figures/capture_feasibility.png` |
| `fig:conversion_readiness` | `output/figures/conversion_readiness.png` |

## Editing a section

1. Change the domain/prose, then re-run
   `scripts/z_generate_manuscript_variables.py`.
2. If you introduce a new token, add it to
   `src/the_spy_who_loved_me/manuscript_variables.py` and reference it in a
   numbered section; the cross-reference test covers it automatically.
3. Verify the gates (pytest + ruff + mypy) before committing (path-scoped).
