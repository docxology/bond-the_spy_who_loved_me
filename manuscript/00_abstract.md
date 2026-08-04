# Abstract

{{LIPARUS_TITLE}} is a deterministic special-agent mission model built around
the three concepts of *The Spy Who Loved Me* (1977) under mission codename
{{LIPARUS_CODENAME}}. It comprises {{NUM_CONCEPT_MODULES}} standalone,
infrastructure-free domain modules — passive acoustic submarine detection and
bearing-only tracking, a Liparus-class tanker capture simulation, and
submersible vehicle conversion forensics — exposed to the BOND fleet through
a frozen `MissionProvider` adapter.

Every result in this manuscript is computed live by the domain core, never
hand-authored: the passive tracker recovers the quarry's position to within
{{SUB_TRACK_POS_ERR_M}} metres of truth, a representative Liparus swallow
completes in {{TANKER_CAPTURE_TIME_S}} seconds, and the Lotus-Esprit-grade
conversion is classified {{FORENSICS_CLASS}}. All simulations are seeded and
fully deterministic, and the test suite holds line and branch coverage on
`src/` at or above 90%.
