# StormChase OS — HRRR convective forecasting development architecture

**Scope:** Full severe-convection forecasting workspace, not a surface-temperature dashboard. Product-level sourcing from NOAA's [NCEP HRRR official f02 inventory](https://www.nco.ncep.noaa.gov/pmb/products/hrrr/hrrr.t00z.wrfsfcf02.grib2.shtml) and actual NOAA NODD source index audits. Product availability must be verified per cycle and forecast lead. Scientific and safety decisions always distinguish official observations from model output, analysis from prediction, a probabilistic forecast from an uncalibrated proxy, and issuance vs valid vs retrieval times.

## Data layers by forecasting question

| Operational forecast question | Initial products / diagnostic plan | Acceptance state |
| --- | --- | --- |
| Upper-level jet / forcing | 250- and 300-hPa U/V speed/direction, speed isotachs, ageostrophic wind/divergence and jet-entrance/exit evaluation with scientifically correct map projection | U/V source inventory verified; wind-vector derived display and numerical derivative QA pending |
| Midlevel ascent / trough evolution | 500-hPa HGT, temperature, wind, cyclonic relative/absolute vorticity and advection; 700-hPa HGT, DZDT (geometric m/s, **not** omega Pa/s), T/Td, winds and RH; trough timing and multi-cycle valid-hour differences | 500-HGT and 700-T archived geographic scalar maps verified; actual contours/barbs, vorticity and RH derivation pending |
| Low-level warm advection & boundaries | 925/850-hPa thermal and moisture fields, U/V winds, moisture transport, 2-m theta-e/mixing ratio, 10-m convergence, station observations and surface pressure | Several source fields verified; derived diagnostics, objective boundary detection and independent comparisons pending |
| Buoyancy / inhibition / initiation | SB CAPE/CIN, 90-hPa and 180-hPa mixed-layer CAPE/CIN, 255-hPa most-unstable candidate, 0–3km CAPE, LI, LCL, parcel Skew-T, lapse rates and diurnal CIN erosion | All listed source identity/step types verified; archived SB CAPE mapped; parcel origin/MetPy cross-comparison and sounding validation pending |
| Storm organization | 0–1 and 0–3km model SRH, model storm motion, 0–1/0–6km vertical shear **gradients** (not yet bulk shear), true bulk shear reconstructed from multi-level profiles, effective-layer shear/SRH, critical angles | Source HLCY verified and archived 0–1km map tested; true profile diagnostics experimental; vertical-level and storm-motion QC pending |
| Convective storm structure / short-range evolution | HRRR simulated composite reflectivity, 1km/4km reflectivity, echo tops, VIL, hourly maximum updraft/downdraft, simulated hail/lightning, hourly 0–2 and 2–5km UH, 3-hour UH maximum swaths | REFC and 2–5km UH mapped from genuine archived GRIB; no radar observations or storm-object tracking claimed |
| UH **tracks** vs swaths | First build exact hourly-max UH gridded history. For *actual forecast storm-object tracklines*, separately identify coherent updraft/reflectivity objects, associate between forecast frames with controlled displacement/association uncertainty, track splits/mergers, and evaluate using held-out events and objective matching to observed tracks | 3-hour UH **swath** implemented; actual tracked storm objects **not implemented**. Never call max-UH swath a predicted tornado track |
| Precipitation / cold pools | Distinguish last-hour APCP from run-total APCP, rain rate, gust swaths, hail size proxy, model outflow/boundary diagnostics and hazards | Both APCP interval descriptors verified; precipitation/rainfall maps and independent QA pending |
| Storm environments / uncertainty | HRRR lagged cycles aligned to the same valid hour; RAP, HREF/REFS/RRFS operational status and members separately validated; compare storm mode and placement with boundaries, reflectivity, soundings and satellites | Archived HRRR two-cycle temperature comparison and run-independent recent-stage pipeline tested; broader current-cycle field publication not deployed |
| Real-time observational overlay | Actual NEXRAD/MRMS (separate from REFC), GOES, ASOS/METAR/mesonet, actual warnings and SPC discussions/watches, latency and spatial co-location, storm reports | SPC Day 1–3 category and NWS warning baseline implemented; most observational integrations and active-event verification outstanding |
| Point soundings | Full HRRR `wrfprs` or `wrfnat` vertical levels (not a dozen sparse `wrfsfc` levels), geopotential / vertical coordinate handling, parcel assumptions, MetPy Skew-T/hodograph and storm motion | Not implemented; separate full-profile data and physically valid parcel QA needed |

## Plot standards

A finished operational upper-air chart must support geopotential height contours (gpm/dam carefully converted), wind barbs/vectors (m/s→kt), scalar colored field scale and uniform grid projection, temporal and source metadata. Forecast-valid-time selectors must not silently mix run cycles or forecast-step intervals. Simulated reflectivity uses dB/dBZ from source; it must never be labeled NEXRAD. UH local GRIB parameters may return **`units=unknown` in ecCodes** despite the official NCEP inventory describing UH units as m²/s²; store raw decoder fields and the separate catalog interpretation, and require independent consistency checks before treating that as physically verified.

For a multi-hour UH swath, require identical run, native grid, valid hour and exact contiguous nonoverlapping 1h maxima; combine as gridpoint maximum, transparently mask missing data and list each contributing forecast interval. UH swaths are *not* storm-object tracks. A forecast tracked-supercell feature requires storm objects, temporal matching, motion/mode inference and historical validation.

For convective proxies, avoid arbitrary tornado/hail/wind probabilities or implied verification. Use independent historical sample testing across region and regime, storm-event grouping, reliability/calibration and meaningful baselines. Apparent signal on a field is not automatically an initiation forecast.

## Phased implementation

**P0: Source contract and true demonstration (this workstream).** Catalog 69 HRRR `wrfsfc` fields; verify exact source message-level timing, 2–5km UH windows, REFC, 500HGT, 700T, CAPE, SRH. Produce fully attributed, strictly archived regional map pilot with fixed scales and browser QA.

**P1: Live model-asset publishing infrastructure.** Add bounded field priority tiers and cycle-discovery by NOAA index; GRIB bitmap/QC, manifest retention with immutable hashes, source publication observation and robust source-failure behavior. Measure processing/egress/storage, design object-store or cache solution. No recurring full-CONUS bulk download and no publishing when source/valid/interval QC fails.

**P2: Real convective-analysis panels.** Add actual upper-level vector/contour charts, theta-e/moisture, exact accumulated precipitation, near-surface convergence, multiple CAPE/CIN definitions, 1–3km shear/SRH, composite reflectivity and continuous UH/reflectivity time animation. Map legend/cursor sampled values and data age always visible.

**P3: Profiles, trends and object evolution.** Validate full vertical `wrfprs` fields, point soundings/MetPy calculations, true multi-cycle run comparison, reflectivity/updraft object segmentation and candidate tracks with geographic/temporal error bounds.

**P4: Operational integration and research.** Reconcile radar/MRMS/satellite and warnings with model maps, perform hindcast studies, forecasting verification and benchmark against reliable references. Experimental targeting remains separate until independent validation.

**Scientific caution:** The currently mapped 2026-10-27 17Z example is a fixed archived test case. The three-hour UH field maximum is nearly zero within its small Southern Plains domain, and is deliberately mostly transparent below a fixed 25 m²/s² display threshold; that does not imply actual storms/tornadoes were absent elsewhere or at other times. No claim of live convective forecasting or calibrated hazard probability is made.
