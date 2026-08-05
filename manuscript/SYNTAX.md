# Manuscript Syntax — LIPARUS

## Cross-references

Use Pandoc-crossref attributes, never hardcoded numbers or raw `\ref{}`.

* Figures: `![alt](../output/figures/bearing_track.png){#fig:bearing_track}`,
  referenced as `@fig:bearing_track` (narrative) or `[@fig:bearing_track]`.
* Sections: add `{#sec:methodology}` to a heading; reference as
  `@sec:methodology`.

## Tokens

Metrics are `{{TOKEN}}`-driven; every token resolves through
`src/the_spy_who_loved_me/manuscript_variables.py::generate_variables()`.
Add a token there and assert it in `tests/test_manuscript_variables.py`
(the live cross-reference test fails if a prose token is missing).

## Citations

BibTeX in `references.bib`; cite with `[@key]`.

## Figures

| Label | Output |
|---|---|
| `fig:bearing_track` | `output/figures/bearing_track.png` |
| `fig:beamforming_response` | `output/figures/beamforming_response.png` |
| `fig:sonar_detection_range` | `output/figures/sonar_detection_range.png` |
| `fig:capture_feasibility` | `output/figures/capture_feasibility.png` |
| `fig:conversion_readiness` | `output/figures/conversion_readiness.png` |
