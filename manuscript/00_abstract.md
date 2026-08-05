# Abstract

{{LIPARUS_TITLE}} is a deterministic special-agent mission model built around
the concepts of *The Spy Who Loved Me* (1977) under mission codename
{{LIPARUS_CODENAME}}. It comprises {{NUM_CONCEPT_MODULES}} standalone,
infrastructure-free domain modules — passive acoustic detection and
bearing-only tracking, Liparus-class tanker capture, submersible vehicle
conversion forensics, underwater acoustics and the passive sonar equation,
uniform-linear-array beamforming, and pressure-hull collapse/ballast
analysis — exposed to the BOND fleet through a frozen `MissionProvider`
adapter.

Every result in this manuscript is computed live by the domain core, never
hand-authored: the tracking pipeline recovers the quarry's position to within
{{SUB_TRACK_POS_ERR_M}} metres of truth, the ULA beamformer points the array
to within {{BEAM_BEARING_ERR_DEG}} degrees of the true bearing (Cramer-Rao
floor {{BEAM_CRB_DEG}} degrees), the passive sonar equation yields a
detection range of {{ACO_DETECTION_RANGE_M}} metres, and the Esprit-grade
pressure hull survives to a collapse depth of {{HULL_COLLAPSE_DEPTH_M}} metres
(a safety factor of {{HULL_SAFETY_FACTOR}} at its operating depth of
{{HULL_OPERATING_DEPTH_M}} metres) while requiring {{BALLAST_VOLUME_L}} L of
ballast to reach neutral buoyancy. All simulations are seeded and fully
deterministic, and the test suite holds line and branch coverage on `src/` at
or above 90%.
