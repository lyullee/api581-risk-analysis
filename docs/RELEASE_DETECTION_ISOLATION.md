# Release detection and isolation

`api581.api.release.detection_isolation_rating(DetectionIsolationRatingInput(...))` first maps the qualitative Table 4.5 descriptions to A/B/C. `api581.api.release.detection_isolation(DetectionIsolationInput(...))` then implements the SI Table 4.6/4.7M selection used by Part 3 §4.6.

`api581.api.release.hole_size_selection(HoleSizeSelectionInput(...))` implements Table 4.4/4.4M class boundaries and representative diameters. SI and US printed boundaries are selected explicitly; rupture uses `min(component_diameter_m, 0.4064)`.

The API accepts the qualified Table 4.5 ratings (`A`, `B`, `C`), a canonical hole (`small`, `medium`, `large`, `rupture`), theoretical release rate and available mass. It returns the printed release-reduction fraction, adjusted rate, maximum leak duration, actual duration limited by inventory, and released mass.

Table 4.6 is represented explicitly for all nine detection/isolation pairs. Table 4.7M durations are returned in seconds for 6.4, 25 and 102 mm classes. `rupture` has no Table 4.7M duration; its duration is `None` and released mass is the available mass, preserving the standard's rupture exception rather than inventing a duration.

The Table 4.5 API does not inspect plant instrumentation, coverage or proof-test data; `qualification_basis` remains auditable evidence. The existing `release/detection-reduction` and `release/detection-duration` primitives remain available for workflows that compose the equations separately.

Verification: `tests/test_detection_isolation.py` (all Table 4.5 combinations, all nine Table 4.6 cells, duration anchors and rupture behavior), plus the full suite.
