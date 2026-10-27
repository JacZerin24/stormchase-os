# Archived NOAA HRRR convective-field pilot

Runs **one fixed, explicitly historical HRRR 2026-10-27 17Z cycle**, acquiring 2–5 km hourly UH at f01/f02/f03 and, at f03, **simulated composite reflectivity**, 500-hPa geopotential height, 700-hPa temperature, surface CAPE and model-provided 0–1 km SRH. The scientific QA checks exact source GRIB indexes and forecast step descriptors, HTTP 206 ranges, init/valid times, native ecCodes units/grid/interval windows, spatial source-coordinate registration, bounded legitimate field-value ranges and no geographic extrapolation.

A 17–20Z **3-hour UH forecast swath** is formed by taking the pixelwise maximum of the verified hourly (17–18, 18–19, 19–20Z) 2–5 km UH maxima. This is NOT a storm track, observed tornado path, probability, or evidence that storms truly occurred. Simulated composite reflectivity is NOT observed radar reflectivity.

Mapping stage is **archived only**; no public current-model delivery or radar warning service. Must preserve source hash, model initialization, valid and exact accumulation windows, native grid CRS and units. The current archived pilot region follows the tested small Southern Plains QA domain; do not invent precise forecast skill or extrapolate missing native cells.

This first pilot outputs georeferenced PNG assets and a source/provenance JSON only; scientific acceptance is contingent on a successful real NOAA run. More comprehensive upper-level charts need independently checked wind vectors, height contours, vorticity, moisture advection and soundings. Do not call a scalar-height raster a complete dynamical upper-air chart.

Official inventory reference: https://www.nco.ncep.noaa.gov/pmb/products/hrrr/hrrr.t00z.wrfsfcf02.grib2.shtml .


## Genuine NOAA archived GRIB and browser evidence — October 27, 2026

Source-scoped [HRRR scientific processing run](https://github.com/JacZerin24/stormchase-os/actions/runs/40573978062) downloaded **eight indexed NOAA GRIB2 messages**, totaling **4,181,791 bytes**, and generated seven 225×160 RGBA PNG forecast overlays totaling **85,947 bytes**. Initial outputs included 500-hPa height (5,752–5,837 gpm within the fixed Plains box), 700-hPa temperature (273.95–280.76 K), SB CAPE (0–2,290 J/kg), model 0–1km SRH (about −15.3 to +171.8 in decoded GRIB units), and simulated composite reflectivity (−10 to 37.19 dB). These are descriptive values in a real archived model forecast, NOT verified observed convection.

The same source run provided 1-hour, 2-hour and 3-hour forecast UH maxima from consecutive 17–18Z, 18–19Z and 19–20Z hourly intervals. Their pixelwise maximum formed the **17–20Z 2–5km UH forecast swath**; the archived Southern Plains regional maximum was only about **0.2** (physical interpretation per official NCEP inventory; ecCodes reported local UH parameter units `unknown`). The visualization masks values below a **25 m²/s² catalog-unit** threshold and will appear largely transparent. This is a legitimate low-signal forecast display, not a map of observed storms or the absence of real tornadoes.

The initial map generation performed **16 independent ecCodes source-coordinate lookups per native source message**. A subsequent scientific QA revision additionally rejects wrong native height/pressure/surface levels and unexpected GRIB unit metadata; UH's ecCodes local-unit gap remains explicit in its manifest and cannot be called native-unit independently verified. The source-derived map graphics have fixed color thresholds rather than visually exaggerated per-frame auto-normalization.

A [separate desktop and mobile Chromium run](https://github.com/JacZerin24/stormchase-os/actions/runs/40575262259) successfully exercised all **seven** locally served archived NOAA-derived PNGs and required explicit archive/not-current wording, separate simulated-radar language and the UH-swath-not-track disclaimer. This is browser behavior QA; it is **not** independent skill or full production Pages scientific signoff.

**Still missing and not silently approximated:** 500mb geopotential contours and proper wind barbs, 250/300 jet analysis, 700mb RH/moisture transport, 850mb thermal/wind structure, parcel and effective shear derived profiles, actual tracked forecast storm objects, multi-hour radar/reflectivity animation, RRFS/REFS validation and live updating publish/cache service.
