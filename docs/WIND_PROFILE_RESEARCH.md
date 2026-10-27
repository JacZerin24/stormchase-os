# Wind-profile scientific research slice

This is a small, unit-tested **experimental** wind-only calculation module, not a validated operational sounding or hodograph product. Wind vectors are u/v in meters per second, heights are meters **AGL**. Wind profiles must include a known 0 m AGL level; no extrapolation or silent height conversion.

Implemented:
- Linear wind interpolation within an explicitly known AGL profile, and 0–1 km/0–6 km layer shear when requested.
- Height-weighted mean winds.
- Height-layer storm-relative helicity using the discrete MetPy/Markowski hodograph summation, with explicitly specified storm motion.
- A prescribed Bunkers 2000-type mean-wind/deviation calculation; no Bunkers result if shear vector degenerates.

**The only completed verification is deterministic analytical/unit testing.** External MetPy comparisons, physically representative cases and observational RAOB profile verification are not yet run. Missing levels cause errors instead of inferred winds. This module does not compute CAPE, CIN, LCL, virtual temperature, effective SRH or any probability of severe weather.

Before integration in StormChase OS:
1. Provide real observed/model profiles with launch/run/valid time, source, pressure, temperature, dewpoint, height-coordinate semantics, missing data and vertical resolution/QC.
2. Compare results with pinned MetPy and observed known sounding cases; cover storm-motion variants, nonuniform vertical sampling and lowest-level gaps.
3. Add parcel physics via MetPy under versioned parcel/virtual correction/thermodynamic assumptions. Never label CAPE/SRH etc validated from just these analytic tests.
4. Connect map point selection to the profile provider and build a reviewed, accessibility-tested Skew-T/hodograph component.

Reference formulas: https://unidata.github.io/MetPy/latest/api/generated/metpy.calc.storm_relative_helicity.html ; https://unidata.github.io/MetPy/latest/api/generated/metpy.calc.bunkers_storm_motion.html ; https://unidata.github.io/MetPy/v1.6/api/generated/metpy.calc.bulk_shear.html .


## Independent formula comparison — 2026-10-27

[GitHub Actions run 40553922597](https://github.com/JacZerin24/stormchase-os/actions/runs/40553922597) passed reference comparisons using pinned `MetPy==1.7.1`. An earlier failing test exposed a ~0.94 m/s Bunkers right-mover discrepancy from **height-weighted vs pressure-coordinate-weighted** mean winds. The implementation now requires an explicit strictly decreasing pressure profile corresponding to the AGL wind heights, and integrates winds with respect to pressure as in MetPy's `weighted_continuous_average` implementation. It also passed nonuniform-profile SRH and bulk-shear comparisons. Do not silently substitute geometric-height weighting under the same method name.

The reference profiles remain synthetic. Real observed/raw model sounding samples, metadata/QC, thermodynamics and complex edge-case validation are **not complete**. No operational sounding or hodograph service is claimed.
