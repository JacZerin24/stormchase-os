# Source-gated SPC hazards and conditional intensity (2026)

**Implemented in this PR:** An actual official-service metadata and sample-attribute survey, with deterministic tests. **Not implemented:** UI probability/CIG overlays or operational use.

The [SPC FeatureServer](https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/FeatureServer) identifies:
- Day 1 tornado CIG 2; tornado probability 3; hail CIG 4; hail probability 5; wind CIG 6; wind probability 7.
- Day 2 tornado CIG 10; tornado probability 11; hail CIG 12; hail probability 13; wind CIG 14; wind probability 15.
- Day 3 severe CIG 18 and severe probability 19.

**DO NOT** reuse categorical DN=2/3/4/5 etc labels for these layers, interpret CIG tiers as direct percentages, sum probability layers, or treat an absent hazard polygon as evidence of no severe potential. The live field/label encodings and valid times must be examined first, and formal official SPC probability/CIG product definitions/thresholds linked before implementing a hazard overlay. A 0-feature survey reflects the specific query time and cannot validate real polygons. GitHub Actions runs expose report artifacts, but no full alert or outlook geometry is stored.

Follow-up acceptance: compare hazard layer labels with official source legend/text; implement probability and CIG with separate semantic types/color ramps/hatching, source issue/valid times, geometry-count consistency and browser mobile tests, then obtain meteorological review.

Source: NOAA/NWS official SPC FeatureServer (Oct 2026 service). Results from any one survey do not establish all possible hazard values or future schema stability.
