# Experimental setup {#sec:setup}

The package runs under Python {{PYTHON_VERSION}}. The manuscript variables
are hydrated by `scripts/z_generate_manuscript_variables.py`, which computes
metrics live from the domain core and resolves every manuscript token in
this tree.

## Canonical scenarios

* **Passive tracking**: a 600-second scenario at a 10-second cadence; the
  target travels at 25 m/s on course 090° from an initial range of 4000 m;
  the ownship runs a deterministic dogleg (east then north); relative
  bearings are corrupted by 0.5° of seeded noise.
* **Liparus capture**: a 140 m hold, 16 m × 14 m mouth, and 1.5 m required
  clearance swallowing a 72 m submarine.
* **Vehicle forensics**: a Lotus-Esprit-grade spec (1800 kg, 2.0 m^3
  displacement) with the critical submersible systems fitted.
* **Passive sonar**: a 160 dB source against a 70 dB noise floor and 20 dB
  array directivity at 400 Hz; sound speed at 10 °C / 35 PSU at the surface.
* **Beamforming**: an 8-element half-wavelength ULA observing a 30° bearing
  at 20 dB SNR (seeded snapshot).
* **Pressure hull**: a 0.8 m radius, 20 mm steel (350 MPa yield) cylinder
  operating at 40 m depth.

## Mission identity

The mission runs under codename {{LIPARUS_CODENAME}} with package version
{{LIPARUS_VERSION}} and a fixed seed. It is one of {{NUM_CONCEPT_MODULES}}
concept modules served to the BOND fleet through `bond_api` discovery and
the `GadgetRegistry`.

## Verification

Coverage and lineage are enforced by the package guardrails: 90% line and
branch on `src/`, no mock framework, no leftover template lineage, and a
clean `git status` after a path-scoped commit.
