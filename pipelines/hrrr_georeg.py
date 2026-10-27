"""Reproducible real-HRRR Lambert-grid to geographic QA map pilot.

This does NOT constitute operational model dissemination. Requires previously
authenticated/decoded official GRIB2 inputs. Generates two archived, same-valid-
time forecast layers and a difference map after spatial/temporal validations.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
# rasterio bundles GDAL/native libraries; load it before ecCodes' bundled
# GRIB C stack to avoid competing GDAL/libproj initializations.
import numpy as np
from scipy.spatial import cKDTree
from rasterio import open as rio_open
from rasterio.shutil import copy as cog_copy
from rasterio.transform import from_bounds
from PIL import Image
import eccodes as ec

# Fixed QA pilot domain, not a chase-target recommendation.
BOUNDS = (-103.0, 33.0, -94.0, 39.4)  # west, south, east, north
STEP_DEG = 0.04
EARTH_RADIUS_KM = 6371.0088
MAX_NEAREST_KM = 5.0
# A fixed physical temperature scale in Fahrenheit; no autoscaling that could
# exaggerate an unremarkable forecast gradient.
BREAKS_F = np.array([0,20,32,40,50,60,70,80,90,100,110],dtype=np.float64)
COLORS = np.array([
  [63,45,131],[73,95,176],[61,147,196],[80,183,200],[115,199,169],
  [189,211,127],[242,214,118],[245,167,98],[224,106,83],[175,69,87],[104,50,88]
],dtype=np.uint8)


def unit_sphere(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Earth-centered unit Cartesian coordinates, handles longitude wrapping."""
    phi=np.deg2rad(lat)
    lam=np.deg2rad(lon)
    return np.column_stack((np.cos(phi)*np.cos(lam),np.cos(phi)*np.sin(lam),np.sin(phi)))


def raster_grid(bounds: tuple[float,float,float,float], step:float) -> tuple[np.ndarray,np.ndarray]:
    west,south,east,north=bounds
    if not -180<=west<east<=180 or not -90<=south<north<=90 or not 0<step<=0.25:
        raise ValueError("Invalid bounded longitude/latitude pilot region")
    width=round((east-west)/step)
    height=round((north-south)/step)
    if not 4<=width<=1000 or not 4<=height<=1000 or (
        abs(width*step-(east-west))>1e-8 or abs(height*step-(north-south))>1e-8
    ):
        raise ValueError("Extent must exactly match bounded pixel grid")
    xx=west+(np.arange(width,dtype=np.float64)+0.5)*step
    yy=north-(np.arange(height,dtype=np.float64)+0.5)*step
    lon,lat=np.meshgrid(xx,yy)
    return lon,lat


def nearest_regrid(source_lat:np.ndarray, source_lon:np.ndarray,
                   source_values_K:np.ndarray,
                   bounds=BOUNDS,step=STEP_DEG,max_km=MAX_NEAREST_KM):
    """Nearest gridpoint in spherical distance; transparent beyond radius.

    NO geographic extrapolation, interpolation pretending to be model native
    resolution, or silent missing-cell filling. Maps actual point coordinates.
    """
    lat=np.asarray(source_lat,dtype=np.float64).ravel()
    lon=np.asarray(source_lon,dtype=np.float64).ravel()
    v=np.asarray(source_values_K,dtype=np.float64).ravel()
    if len(lat)!=len(lon) or len(lat)!=len(v):
        raise ValueError("ecCodes latitude/longitude/value pairing count mismatch")
    west,south,east,north=bounds
    lon=((lon+180)%360)-180
    inside=(np.isfinite(lat)&np.isfinite(lon)&np.isfinite(v)&
            (v>150)&(v<350)&(lat>=south-0.2)&(lat<=north+0.2)&
            (lon>=west-0.2)&(lon<=east+0.2))
    glon,glat=raster_grid(bounds,step)
    # Apply an absolute production minimum while permitting small synthetic
    # geometries in deterministic tests (not production data).
    required=min(200,max(4,int(glon.size*0.25)))
    if inside.sum()<required:
        raise ValueError("Too few valid source gridpoints for pilot region")
    loc=unit_sphere(lon[inside],lat[inside])
    distances,indices=cKDTree(loc).query(unit_sphere(glon.ravel(),glat.ravel()),k=1,workers=2)
    # Chord length to great-circle geodesic distance, including curvature.
    nearest_km=2*EARTH_RADIUS_KM*np.arcsin(np.clip(distances/2,0,1))
    valid=(np.isfinite(nearest_km)&(nearest_km<=max_km))
    nearest_values=np.asarray(v[inside])[indices]
    arr=np.full(glat.size,np.nan,dtype=np.float32)
    arr[valid]=nearest_values[valid]
    coverage=float(valid.mean())
    if coverage<0.97:
        raise ValueError(f"Insufficient geographically matched HRRR grid coverage ({coverage:.1%})")
    return arr.reshape(glat.shape), {
        "coverage_fraction":coverage,
        "max_nearest_km":float(np.max(nearest_km[valid])),
        "p95_nearest_km":float(np.percentile(nearest_km[valid],95)),
        "median_nearest_km":float(np.median(nearest_km[valid])),
        "unmatched_cells":int((~valid).sum()),
        "source_valid_points_in_buffer":int(inside.sum()),
    }


def load_field(path:Path,expected_run:datetime,expected_lead:int):
    """Validate physical identity and preserve source geodetic coordinates."""
    from pipelines.grib_inspect import inspect
    report=inspect(path,expected_run,expected_lead)
    with path.open("rb") as fd:
        handle=ec.codes_grib_new_from_file(fd)
        if handle is None:
            raise ValueError("No GRIB message")
        try:
            if ec.codes_get(handle,"gridType")!="lambert":
                raise ValueError("Expected actual HRRR Lambert grid")
            lat=np.asarray(ec.codes_get_array(handle,"latitudes"),dtype=np.float64)
            lon=np.asarray(ec.codes_get_array(handle,"longitudes"),dtype=np.float64)
            values=np.asarray(ec.codes_get_values(handle),dtype=np.float64)
            if len(lat)!=len(values) or len(lon)!=len(values):
                raise ValueError("GRIB geolocation does not align with fields")
            # Verify gridpoint geolocation/value pairing with ecCodes' separate
            # nearest-neighbor lookup on a sparse geographically dispersed sample.
            for index in (20000,115000,450000,890000,1500000):
                if index>=len(values):continue
                nearest=ec.codes_grib_find_nearest(handle,float(lat[index]),float(lon[index]),npoints=1)
                if not nearest or nearest[0].index!=index or abs(float(nearest[0].value)-float(values[index]))>1e-5:
                    raise ValueError("ecCodes independent nearest-point lookup inconsistent with coordinate arrays")
        finally:
            ec.codes_release(handle)
    return lat,lon,values,report


def write_cog(destination:Path,array:np.ndarray,bounds=BOUNDS):
    """COG in EPSG:4326; pixel centers coincide with PNG image coordinates."""
    west,south,east,north=bounds
    transform=from_bounds(west,south,east,north,array.shape[1],array.shape[0])
    with TemporaryDirectory() as tmp:
        temp=Path(tmp)/"raw.tif"
        with rio_open(temp,"w",driver="GTiff",width=array.shape[1],height=array.shape[0],
                      count=1,dtype="float32",crs="EPSG:4326",transform=transform,
                      nodata=-9999.0,tiled=True,blockxsize=256,blockysize=256,
                      compress="DEFLATE",predictor=3) as ds:
            ds.write(np.where(np.isfinite(array),array,-9999.0).astype(np.float32),1)
        cog_copy(temp,destination,driver="COG",compress="DEFLATE",
                 blocksize=256,overview_resampling="NEAREST")
    with rio_open(destination) as source:
        if str(source.crs)!="EPSG:4326" or source.bounds!=source.bounds:
            raise ValueError("GeoTIFF CRS invalid")
        if not np.allclose([source.bounds.left,source.bounds.bottom,
                            source.bounds.right,source.bounds.top],bounds,atol=1e-8):
            raise ValueError("GeoTIFF geographic bounds changed")
        actual=source.read(1)
        if not np.allclose(actual,np.where(np.isfinite(array),array,-9999),atol=0,rtol=0):
            raise ValueError("COG pixel values changed during encoding")
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def png_rgba(values:np.ndarray,kind:str)->np.ndarray:
    valid=np.isfinite(values)
    if kind=="temperature":
        f=(values.astype(np.float64)-273.15)*1.8+32
        c=np.column_stack([np.interp(f.ravel(),BREAKS_F,COLORS[:,i]) for i in range(3)])
        rgb=np.clip(np.round(c),0,255).astype(np.uint8).reshape((*values.shape,3))
    elif kind=="trend":
        # Difference in Kelvin equals degree Celsius; Fahrenheit difference x1.8
        deltaF=np.asarray(values,dtype=np.float64)*1.8
        stops=np.array([-15,-10,-5,-2,0,2,5,10,15],dtype=float)
        hues=np.array([[61,78,155],[83,127,193],[143,187,217],[213,228,239],
                       [236,233,226],[244,216,198],[223,155,127],[185,97,75],[129,55,70]],dtype=np.uint8)
        c=np.column_stack([np.interp(deltaF.ravel(),stops,hues[:,i]) for i in range(3)])
        rgb=np.clip(np.round(c),0,255).astype(np.uint8).reshape((*values.shape,3))
    else:
        raise ValueError("Unknown overlay type")
    alpha=np.where(valid,185,0).astype(np.uint8)
    return np.dstack([rgb,alpha])


def generate(earlier:Path,later:Path,output:Path):
    """Two legitimate real runs, same forecast valid time: 12Z+6 and 15Z+3."""
    t0=datetime(2026,10,27,12,tzinfo=timezone.utc)
    t1=datetime(2026,10,27,15,tzinfo=timezone.utc)
    if t0+timedelta(hours=6)!=t1+timedelta(hours=3):
        raise AssertionError("Model cycle comparison does not align valid time")
    output.mkdir(parents=True,exist_ok=True)
    products=[]
    fields=[]
    for path,run,lead in ((earlier,t0,6),(later,t1,3)):
        lat,lon,values,source=load_field(path,run,lead)
        area,geo=nearest_regrid(lat,lon,values)
        fields.append(area)
        stem=f"hrrr_{run:%Y%m%d_%H}z_f{lead:02d}_tmp2m"
        cog_name=stem+".tif";png_name=stem+".png"
        cog_sha=write_cog(output/cog_name,area)
        Image.fromarray(png_rgba(area,"temperature"),"RGBA").save(output/png_name,optimize=True)
        products.append({
            "model":"HRRR","parameter":"TMP","level":"2 m above ground",
            "units":"K","runAt":run.isoformat().replace("+00:00","Z"),
            "leadHours":lead,
            "validAt":(run+timedelta(hours=lead)).isoformat().replace("+00:00","Z"),
            "image":png_name,"cog":cog_name,
            "grib_sha256":source["sha256"],
            "image_sha256":hashlib.sha256((output/png_name).read_bytes()).hexdigest(),
            "cog_sha256":cog_sha,
            "geolocation_QA":geo,
            "min_K":float(np.nanmin(area)),"max_K":float(np.nanmax(area)),
        })
    diff=fields[1]-fields[0]
    Image.fromarray(png_rgba(diff,"trend"),"RGBA").save(output/"hrrr_valid18z_delta.png",optimize=True)
    result={
        "schema":"stormchase-hrrr-archived-pilot/1",
        "status":"historical-experimental-display-not-live",
        "provider":"NOAA NODD HRRR public archive",
        "sourceGribLicense":"NOAA public forecast data; check source terms for downstream redistribution",
        "generatedAt":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "validAt":"2026-10-27T18:00:00Z",
        "bounds":list(BOUNDS),
        "rasterStepDegrees":STEP_DEG,
        "rasterCrs":"EPSG:4326",
        "spatialMethod":"spherical nearest-neighbor within 5 km; no extrapolation",
        "temperaturePaletteF":{"breaks":BREAKS_F.tolist(),"colors":COLORS.tolist()},
        "differencePaletteF":{"bounds":[-15,15],"units":"deg F change between run initializations"},
        "products":products,
        "differenceImage":"hrrr_valid18z_delta.png",
        "difference_sha256":hashlib.sha256((output/"hrrr_valid18z_delta.png").read_bytes()).hexdigest(),
        "difference_min_K":float(np.nanmin(diff)),
        "difference_max_K":float(np.nanmax(diff)),
        "independentForecastVerification":"not performed",
        "nativeGridQA":"basic GRIB identity/ecCodes coordinate checks only",
    }
    (output/"manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--earlier",type=Path,required=True)
    p.add_argument("--later",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(generate(a.earlier,a.later,a.out),indent=2))


if __name__=="__main__":
    main()
