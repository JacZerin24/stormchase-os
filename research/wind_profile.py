"""Explicitly experimental, height-AGL wind profile kinematics.

Analytical checks only; comparisons against an independent MetPy reference
dataset and observed sounding profiles are still REQUIRED before operational use.
All winds in m/s; all heights in meters AGL. Never infer storm motion silently.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import hypot, isfinite


@dataclass(frozen=True)
class Wind:
    z_agl_m: float
    u_ms: float
    v_ms: float


def checked(levels: list[Wind]) -> list[Wind]:
    if len(levels) < 2:
        raise ValueError("At least two wind levels required")
    if levels[0].z_agl_m != 0:
        raise ValueError("Profile needs a known 0 m AGL surface; no extrapolation")
    for i, point in enumerate(levels):
        if not all(isfinite(v) for v in (point.z_agl_m, point.u_ms, point.v_ms)):
            raise ValueError("Non-finite or missing vertical profile values")
        if point.z_agl_m < 0 or (i and point.z_agl_m <= levels[i-1].z_agl_m):
            raise ValueError("Wind heights must be strictly increasing AGL")
    return levels


def interpolate(levels: list[Wind], z_agl_m: float) -> Wind:
    checked(levels)
    if not isfinite(z_agl_m) or z_agl_m < 0 or z_agl_m > levels[-1].z_agl_m:
        raise ValueError("Outside observed/forecast profile height; no extrapolation")
    for low, high in zip(levels, levels[1:]):
        if low.z_agl_m <= z_agl_m <= high.z_agl_m:
            f = (z_agl_m-low.z_agl_m)/(high.z_agl_m-low.z_agl_m)
            return Wind(z_agl_m,
                        low.u_ms+f*(high.u_ms-low.u_ms),
                        low.v_ms+f*(high.v_ms-low.v_ms))
    raise ValueError("Missing interpolation levels")


def layer(levels: list[Wind], bottom_m: float, top_m: float) -> list[Wind]:
    if not 0 <= bottom_m < top_m:
        raise ValueError("Invalid wind layer bounds")
    checked(levels)
    result = [interpolate(levels, bottom_m)]
    result.extend(x for x in levels if bottom_m < x.z_agl_m < top_m)
    result.append(interpolate(levels, top_m))
    return result


def bulk_shear(levels: list[Wind], bottom_m: float, top_m: float) -> tuple[float, float, float]:
    """(du,dv,speed) for a prescribed AGL depth; m/s."""
    wind = layer(levels, bottom_m, top_m)
    du = wind[-1].u_ms-wind[0].u_ms
    dv = wind[-1].v_ms-wind[0].v_ms
    return du, dv, hypot(du, dv)


def srh(levels: list[Wind], bottom_m: float, top_m: float,
        storm_u_ms: float, storm_v_ms: float) -> tuple[float, float, float]:
    """MetPy/Markowski hodograph summation; positive, negative, total m^2/s^2.

    Storm motion components MUST be explicitly supplied; no assumed zero-motion.
    """
    if not all(isfinite(v) for v in (storm_u_ms, storm_v_ms)):
        raise ValueError("Explicit finite storm-motion vector required")
    winds = layer(levels, bottom_m, top_m)
    parts = [
        (b.u_ms-storm_u_ms)*(a.v_ms-storm_v_ms)
        - (a.u_ms-storm_u_ms)*(b.v_ms-storm_v_ms)
        for a, b in zip(winds, winds[1:])
    ]
    pos=sum(v for v in parts if v > 0)
    neg=sum(v for v in parts if v < 0)
    return pos, neg, pos+neg


def mean_wind(levels: list[Wind], bottom_m: float, top_m: float) -> tuple[float, float]:
    """Height-weighted (not pressure-weighted) mean wind by trapezoidal integration."""
    winds=layer(levels,bottom_m,top_m)
    depth=top_m-bottom_m
    return (
        sum((a.u_ms+b.u_ms)*0.5*(b.z_agl_m-a.z_agl_m) for a,b in zip(winds,winds[1:]))/depth,
        sum((a.v_ms+b.v_ms)*0.5*(b.z_agl_m-a.z_agl_m) for a,b in zip(winds,winds[1:]))/depth
    )


def bunkers_motion(levels: list[Wind]) -> dict[str, tuple[float,float]]:
    """Documented 0–6 km mean; low 0–0.5, high 5.5–6 km; 7.5 m/s orthogonal."""
    u,v=mean_wind(levels,0,6000)
    lo_u,lo_v=mean_wind(levels,0,500)
    hi_u,hi_v=mean_wind(levels,5500,6000)
    du,dv=hi_u-lo_u,hi_v-lo_v
    mag=hypot(du,dv)
    if mag < 1e-9:
        raise ValueError("Degenerate shear vector; Bunkers motion unavailable")
    off_u,off_v=7.5*dv/mag,-7.5*du/mag
    return {"mean":(u,v),"right":(u+off_u,v+off_v),"left":(u-off_u,v-off_v)}
