# Archived NOAA HRRR convective-field pilot

Runs **one fixed, explicitly historical HRRR 2026-10-27 17Z cycle**, acquiring 2–5 km hourly UH at f01/f02/f03 and, at f03, **simulated composite reflectivity**, 500-hPa geopotential height, 700-hPa temperature, surface CAPE and model-provided 0–1 km SRH. The scientific QA checks exact source GRIB indexes and forecast step descriptors, HTTP 206 ranges, init/valid times, native ecCodes units/grid/interval windows, spatial source-coordinate registration, bounded legitimate field-value ranges and no geographic extrapolation.

A 17–20Z **3-hour UH forecast swath** is formed by taking the pixelwise maximum of the verified hourly (17–18, 18–19, 19–20Z) 2–5 km UH maxima. This is NOT a storm track, observed tornado path, probability, or evidence that storms truly occurred. Simulated composite reflectivity is NOT observed radar reflectivity.

Mapping stage is **archived only**; no public current-model delivery or radar warning service. Must preserve source hash, model initialization, valid and exact accumulation windows, native grid CRS and units. The current archived pilot region follows the tested small Southern Plains QA domain; do not invent precise forecast skill or extrapolate missing native cells.

This first pilot outputs georeferenced PNG assets and a source/provenance JSON only; scientific acceptance is contingent on a successful real NOAA run. More comprehensive upper-level charts need independently checked wind vectors, height contours, vorticity, moisture advection and soundings. Do not call a scalar-height raster a complete dynamical upper-air chart.

Official inventory reference: https://www.nco.ncep.noaa.gov/pmb/products/hrrr/hrrr.t00z.wrfsfcf02.grib2.shtml .
