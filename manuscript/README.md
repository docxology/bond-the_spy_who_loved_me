# Manuscript — LIPARUS

Manuscript source for **The Spy Who Loved Me: LIPARUS — Special-Agent
Mission Software**, a PROJECT BOND film package.

## Section files

| File | Role |
|---|---|
| `00_abstract.md` | Abstract with live result tokens |
| `01_introduction.md` | Film context + package structure |
| `02_methodology.md` | Algorithms: detector, TMA/EKF, acoustics, beamforming, capture, vehicle + hull forensics |
| `03_results.md` | Measured results + all five figures |
| `04_conclusion.md` | Summary |
| `05_experimental_setup.md` | Canonical scenarios + mission identity |
| `06_reproducibility.md` | Determinism, seeding, regeneration |
| `07_scope_and_related_work.md` | Scope + scholarly references |
| `99_references.md` | Bibliography |

## Token protocol

Metrics are **never hand-authored** in prose. Every `{{TOKEN}}` resolves
through `src/the_spy_who_loved_me/manuscript_variables.py::generate_variables()`,
which reads `config.yaml` and computes metrics live from the deterministic
domain core.

```bash
uv run python scripts/z_generate_manuscript_variables.py
# writes output/data/manuscript_variables.json + resolves output/manuscript/
```

The live cross-reference test
(`tests/test_manuscript_variables.py`) asserts that every `{{TOKEN}}` in the
numbered sections exists in `generate_variables()`.

## Figures

| Label | File | Generator |
|---|---|---|
| `fig:bearing_track` | `output/figures/bearing_track.png` | `figures/plots.plot_bearing_track` |
| `fig:sonar_detection_range` | `output/figures/sonar_detection_range.png` | `figures/plots.plot_sonar_detection_range` |
| `fig:beamforming_response` | `output/figures/beamforming_response.png` | `figures/plots.plot_beamforming_response` |
| `fig:capture_feasibility` | `output/figures/capture_feasibility.png` | `figures/plots.plot_capture_feasibility` |
| `fig:conversion_readiness` | `output/figures/conversion_readiness.png` | `figures/plots.plot_conversion_readiness` |

## Config

`config.yaml` holds the LIPARUS identity (title, version, codename, seed)
consumed by the variable hydration and publication metadata. The tree carries
no DOI, so no DOI fields are present.
