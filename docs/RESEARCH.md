# Scientific Research and Verification Protocol

The platform is decision support, not a validated chase-targeting model.

## Scientific questions

1. Which forecast fields provide incremental predictive value for storm initiation, convective mode, tornado, hail and severe-wind hazards compared with transparent baselines?
2. How strongly do spatial representativeness, valid-time uncertainty, boundary displacement, and data latency affect target selection?
3. Can chase practicality be estimated from road continuity, land cover, terrain, lawful observation sites and closures **separately** from meteorological hazard potential?
4. Can retrospective simulation reproduce the data available at an actual forecast decision time and measure performance without look-ahead bias?

## Data engineering requirements

- Keep provenance for product source, provider licensing, ingest/retrieval, issue, run initialization, forecast valid start/end, projection, vertical coordinate, units, revision and latency.
- Independent observations and truth sets: NOAA Storm Data/Storm Events, Storm Reports, radar-derived verification, surface analyses, reanalysis only with explicit retrospective restrictions; clarify known underreporting/coverage biases.
- Preserve operational availability: publication delay, preliminary/final distinction, report revisions, and NWP cycle availability. Don't use a retrospective reanalysis to assert operational forecast skill.
- Archive input snapshots + analysis code/config + hashes for repeatability where permitted.

## Evaluation

- Baselines first: climatology, operational SPC products where scientifically comparable, persistence, simple rule-based indices, and meaningful forecast lead times.
- Partition by *event* and date, then assess spatial/temporal holdouts; no same-outbreak leakage across training/test. Tune only on training/validation, hold test set once.
- Report correct denominators and exposure; rare event base rates; reliability curves, Brier/Brier skill when probabilities are properly defined, ROC/PR where appropriate, contingency statistics and confidence intervals by event.
- Stratify performance by region, season, convective regime, magnitude and observation density; quantification of uncertainty and sensitivity analysis.
- Distinguish occurrence, intensity, location/timing quality, chase visibility/observing success, and operational utility; these are different targets.
- Any initial chase suitability index is an *experimental heuristic score*, never a calibrated probability. Calibration requires independent held-out tests.

## v0.1 scientific QA

- SPC category mapping must follow the official numeric category renderer (DN values 2/3/4/5/6/8), not a guessed interpolation.
- Parse source-defined UTC timestamps or explicitly report unknown; distinguish a successful fetch from product issuance/validity.
- NWS active alerts with null polygon geometry are not represented on a polygon-only map; count/report them. Tests should demonstrate geometry selection.
- Empty collections are not fabricated into hazards. Feed errors must be plainly visible; avoid stale geometry appearing current.
- Future hazard probabilities/2026 CIG semantics require their own source-specific scientific review.

## Release approval checklist

Data service works in target browsers; valid/issued times inspected against NOAA originals; regional polygon geometry aligns with map; no silent missing-alert omission; no under-tested score/probability claims; CI and live smoke test confirmed.
