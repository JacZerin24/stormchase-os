"""Verified archived multi-field HRRR convective-map data, NOT live products.

Uses eight authentic NOAA NODD GRIB messages from one 2026-10-27 17Z cycle:
f01/f02/f03 hourly maximum 2-5 km UH; at f03: simulated composite
reflectivity, 500 hPa height, 700 hPa temperature, SB CAPE, 0-1 km SRH.
Max over 3 contiguous hourly UH fields is a *UH forecast swath*, not a
storm track, observed radar echo or calibrated tornado probability.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
import json
import argparse

from pipelines.hrrr_subset import fetch_index,parse_idx,fetch_message,source_url
from pipelines.hrrr_convective import FIELDS,select

RUN=datetime(2026,10,27,17,tzinfo=timezone.utc)
PLANS={
    1:('uh25_max',),
    2:('uh25_max',),
    3:('uh25_max','refc','hgt500','t700','cape_sb','srh01')
}
# Sanity limits are deliberately wide. They prevent huge GRIB missing
# sentinels from becoming displayed forecast values, not scientific skill QA.
RANGES={
  'uh25_max':(-3000,3000),
  'refc':(-40,95),
  'hgt500':(3000,8000),
  't700':(170,350),
  'cape_sb':(0,20000),
  'srh01':(-3000,3000),
}
# Explicit native GRIB identities established by this real historical run.
# UH product is known in the NOAA catalog, but ecCodes reports its local
# parameter shortName/units as 'unknown'; never claim native-unit QC passed.
EXPECTED_NATIVE={
    'refc':('atmosphere',0,'dB'),
    'hgt500':('isobaricInhPa',500,'gpm'),
    't700':('isobaricInhPa',700,'K'),
    'cape_sb':('surface',0,'J kg**-1'),
    'srh01':('heightAboveGroundLayer',1000,'m**2 s**-2'),
    'uh25_max':('heightAboveGroundLayer',5000,'unknown'),
}
COLOR={
    'refc':([-10,5,15,25,35,45,55,65,75,85],
            [[15,38,55],[40,98,159],[55,156,189],[62,175,96],
             [207,214,61],[241,194,49],[239,115,48],[224,56,75],
             [192,69,165],[251,232,240]],5),
    'uh25_max':([0,25,50,75,100,150,200,300,500],
                [[20,38,57],[103,147,194],[101,199,162],[243,225,108],
                 [243,162,68],[228,97,66],[199,67,134],[139,73,161],[248,225,232]],25),
    'hgt500':([5000,5200,5300,5400,5500,5600,5700,5800,6000],
              [[51,69,124],[69,107,164],[86,148,180],[118,188,170],
               [180,206,142],[227,205,116],[238,174,102],[224,127,113],[146,81,141]],None),
    't700':([223,233,243,253,263,273,283,293,303],
            [[46,58,127],[69,119,181],[72,174,204],[133,195,171],
             [220,220,126],[237,193,102],[229,138,84],[203,83,86],[146,58,114]],None),
    'cape_sb':([0,100,250,500,1000,1500,2000,3000,4500,6500],
               [[37,51,71],[57,116,157],[70,166,158],[154,193,115],
                [221,218,114],[245,188,91],[240,132,81],[217,75,86],
                [172,70,141],[112,56,148]],100),
    'srh01':([-200,-100,0,50,100,150,200,300,450,650],
              [[78,96,173],[129,155,190],[216,219,217],[239,219,170],
               [237,189,128],[232,147,110],[211,99,111],[173,75,143],
               [133,74,143],[90,55,122]],None)
}


def window_contract(leads:list[int],run:datetime)->list[tuple[str,str]]:
    """Require contiguous, ordered UH-max forecast windows from ONE run."""
    if not leads or sorted(leads)!=leads or len(set(leads))!=len(leads) or leads[0]<1:
        raise ValueError('UH leads must be ordered and non-repeating')
    if leads!=list(range(leads[0],leads[-1]+1)):
        raise ValueError('Cannot bridge missing hourly UH maxima')
    if run.tzinfo is None or run.utcoffset()!=timedelta():
        raise ValueError('Model cycle must use explicit UTC')
    return [( (run+timedelta(hours=f-1)).isoformat().replace('+00:00','Z'),
              (run+timedelta(hours=f)).isoformat().replace('+00:00','Z')) for f in leads]


def spatial_regrid(lat,lon,values,range_values):
    import numpy as np
    from scipy.spatial import cKDTree
    from pipelines.hrrr_georeg import BOUNDS,STEP_DEG,MAX_NEAREST_KM,EARTH_RADIUS_KM,unit_sphere,raster_grid
    v=np.asarray(values,dtype=np.float64).ravel()
    la=np.asarray(lat,dtype=np.float64).ravel()
    lo=np.asarray(lon,dtype=np.float64).ravel()
    if not(len(v)==len(la)==len(lo)):
        raise ValueError('GRIB location/field count mismatch')
    lo=((lo+180)%360)-180
    w,s,e,n=BOUNDS
    min_v,max_v=range_values
    mask=(np.isfinite(v)&np.isfinite(la)&np.isfinite(lo)&
          (v>=min_v)&(v<=max_v)&(lo>=w-.2)&(lo<=e+.2)&
          (la>=s-.2)&(la<=n+.2))
    if int(mask.sum())<300:raise ValueError('Too few valid native source cells')
    glon,glat=raster_grid(BOUNDS,STEP_DEG)
    d,ix=cKDTree(unit_sphere(lo[mask],la[mask])).query(
        unit_sphere(glon.ravel(),glat.ravel()),k=1,workers=2)
    km=2*EARTH_RADIUS_KM*np.arcsin(np.clip(d/2,0,1))
    valid=(np.isfinite(km)&(km<=MAX_NEAREST_KM))
    if valid.mean()<.97:raise ValueError('Native GRIB grid fails geographic coverage')
    result=np.full(len(km),np.nan,dtype=np.float32)
    result[valid]=v[mask][ix[valid]]
    return result.reshape(glon.shape),{
        'matchingCoverageFraction':float(valid.mean()),
        'maximumNativeDistanceKm':float(km[valid].max()),
        'sourceCellsWithinRegion':int(mask.sum()),
        'missingPixels':int((~valid).sum()),
        'sampling':'nearest native grid point, NOT newly resolved meteorological detail'
    }


def decode(path:Path,run:datetime,lead:int,key:str):
    import eccodes as ec
    import numpy as np
    spec=FIELDS[key]
    with path.open('rb') as stream:
        gid=ec.codes_grib_new_from_file(stream)
        if gid is None:raise ValueError('ecCodes rejected GRIB2 field')
        try:
            props={k:ec.codes_get(gid,k) for k in (
                'edition','shortName','name','units','gridType','dataDate','dataTime',
                'validityDate','validityTime','stepType','stepRange','startStep',
                'endStep','typeOfLevel','level','numberOfPoints')}
            if int(props['edition'])!=2:
                raise ValueError('Wrong GRIB edition')
            if int(props['dataDate'])!=int(run.strftime('%Y%m%d')) or int(props['dataTime'])!=int(run.strftime('%H%M')):
                raise ValueError('GRIB initialization mismatch')
            valid=run+timedelta(hours=lead)
            if int(props['validityDate'])!=int(valid.strftime('%Y%m%d')) or int(props['validityTime'])!=int(valid.strftime('%H%M')):
                raise ValueError('GRIB valid-time mismatch')
            if int(props['endStep'])!=lead:
                raise ValueError('GRIB interval end not requested forecast hour')
            # Max/min time windows must remain exact; instant fields are not
            # silently converted to hour accumulations.
            if spec.timing=='hourly_max' and (
                str(props['stepType'])!='max' or int(props['startStep'])!=lead-1):
                raise ValueError('UH maximum interval metadata mismatch')
            if spec.timing=='instant' and str(props['stepType']) not in ('instant','instantaneous'):
                raise ValueError('Unexpected GRIB step type for instantaneous field')
            expected=EXPECTED_NATIVE[key]
            if (str(props['typeOfLevel']),int(props['level']),str(props['units']))!=expected:
                raise ValueError('Native GRIB type/level/units mismatch for '+key)
            if str(props['gridType'])!='lambert':
                raise ValueError('Expected documented native CONUS HRRR Lambert grid')
            la=np.asarray(ec.codes_get_array(gid,'latitudes'),dtype=np.float64)
            lo=np.asarray(ec.codes_get_array(gid,'longitudes'),dtype=np.float64)
            value=np.asarray(ec.codes_get_values(gid),dtype=np.float64)
            if len(value)!=int(props['numberOfPoints']) or len(la)!=len(value) or len(lo)!=len(value):
                raise ValueError('Native grid coordinates mismatch GRIB values')
        finally:
            ec.codes_release(gid)
    return la,lo,value,props


def paint(arr,field):
    import numpy as np
    cuts,colors,threshold=COLOR[field]
    c=np.asarray(colors,dtype=np.float64)
    x=np.asarray(arr,dtype=np.float64)
    rgb=np.stack([np.interp(x.ravel(),cuts,c[:,i]) for i in range(3)],axis=1)
    rgb=np.asarray(np.clip(np.rint(rgb),0,255),dtype=np.uint8).reshape((*x.shape,3))
    opacity=np.where(np.isfinite(x)&((x>=threshold) if threshold is not None else True),186,0)
    return np.dstack((rgb,opacity.astype(np.uint8)))


def generate(out:Path,run:datetime=RUN)->dict:
    import numpy as np
    from PIL import Image
    from pipelines.hrrr_georeg import BOUNDS,STEP_DEG,write_cog,spotcheck_output_against_eccodes
    if out.exists():raise FileExistsError('Refusing to overwrite immutable convective case')
    windows=window_contract(list(PLANS),run)
    with TemporaryDirectory() as tmp:
        tmpdir=Path(tmp)
        fields={}
        uh=[]
        transfer=0
        for lead,keys in PLANS.items():
            url=source_url(run,lead)
            entries=parse_idx(fetch_index(url),run)
            for key in keys:
                selection=select(entries,FIELDS[key],lead)
                if selection['status']!='index_verified':
                    raise ValueError(f'{key} forecast hour {lead} missing/ambiguous')
                body,_=fetch_message(url,selection['start'],selection['end'])
                transfer+=len(body)
                path=tmpdir/f'{key}_f{lead:02d}.grib2'
                path.write_bytes(body)
                lat,lon,values,grib=decode(path,run,lead,key)
                mapped,geo=spatial_regrid(lat,lon,values,RANGES[key])
                coord=spotcheck_output_against_eccodes(path,mapped)
                # The shared reference function was originally temperature-only.
                # Record generic source-field values without claiming all units K.
                geo['ecCodesCoordinateCrosscheck']={
                  'checkedPixelCenters':coord['checked_output_pixel_centers'],
                  'maxAbsoluteFieldDifferenceInGribUnits':coord['max_abs_temperature_residual_K'],
                  'maximumEcCodesDistanceKm':coord['max_eccodes_distance_km'],
                  'referenceMethod':'separate ecCodes nearest lookup using same NOAA GRIB source',
                }
                tag=f'{key}_f{lead:02d}'
                fields[tag]={
                    'field':key,'runAt':run.isoformat().replace('+00:00','Z'),
                    'leadHours':lead,'validAt':(run+timedelta(hours=lead)).isoformat().replace('+00:00','Z'),
                    'intervalStartAt':(run+timedelta(hours=lead-1)).isoformat().replace('+00:00','Z')
                         if FIELDS[key].timing=='hourly_max' else None,
                    'intervalEndAt':(run+timedelta(hours=lead)).isoformat().replace('+00:00','Z')
                         if FIELDS[key].timing=='hourly_max' else None,
                    'sourceURL':url,'sourceRecord':selection['record'],
                    'sourceSHA256':sha256(body).hexdigest(),'sourceBytes':len(body),
                    'gribMetadata':grib,'geographicQA':geo,
                    'catalogUnits':FIELDS[key].units,
                    'unitsInterpretation':('NOAA NCEP inventory units; ecCodes local parameter units unresolved'
                          if key=='uh25_max' else 'ecCodes native GRIB units validated'),
                    'minValue':float(np.nanmin(mapped)),'maxValue':float(np.nanmax(mapped)),
                }
                if key=='uh25_max':
                    uh.append(mapped)
                if lead==max(PLANS):
                    fields[tag]['array']=mapped
        swath=np.maximum.reduce(uh)
        # A multi-hour max of non-overlapping hourly maxima is a model UH SWATH,
        # not an observed storm-object track.
        fields['uh25_swath_3h']={
            'field':'uh25_max','runAt':run.isoformat().replace('+00:00','Z'),
            'leadHours':3,'validAt':(run+timedelta(hours=3)).isoformat().replace('+00:00','Z'),
            'intervalStartAt':windows[0][0],'intervalEndAt':windows[-1][1],
            'sourceHours':[1,2,3],
            'interpretation':'pixelwise maximum of 3 contiguous hourly 2-5km AGL UH maxima; NOT storm-object tracks',
            'array':swath,
            'minValue':float(np.nanmin(swath)),'maxValue':float(np.nanmax(swath))
        }
        out.mkdir(parents=True)
        size=0
        display=['refc_f03','hgt500_f03','t700_f03','cape_sb_f03','srh01_f03','uh25_max_f03','uh25_swath_3h']
        for tag in display:
            item=fields[tag]
            png=tag+'.png';cog=tag+'.tif'
            rgba=paint(item.pop('array'),'uh25_max' if tag=='uh25_swath_3h' else item['field'])
            item['png']=png
            Image.fromarray(rgba,'RGBA').save(out/png,optimize=True)
            item['pngSHA256']=sha256((out/png).read_bytes()).hexdigest()
            size+=(out/png).stat().st_size
        result={
          'schema':'stormchase-convective-archived-model/1',
          'status':'experimental_historical_not_current',
          'runAt':run.isoformat().replace('+00:00','Z'),
          'finalValidAt':(run+timedelta(hours=3)).isoformat().replace('+00:00','Z'),
          'bounds':list(BOUNDS),'crs':'EPSG:4326','stepDegrees':STEP_DEG,
          'model':'HRRR','provider':'NOAA NODD public HRRR archive',
          'sourceBytes':transfer,'derivedPNGBytes':size,
          'fieldProducts':fields,'displayOrder':display,
          'actualPublicationAt':None,'observedRadar':False,
          'observedStormTrack':False,'calibratedTornadoProbability':False,
          'independentForecastVerification':'not performed',
        }
        (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
        return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    z=generate(a.out)
    print(json.dumps({k:z[k] for k in ('runAt','finalValidAt','sourceBytes','derivedPNGBytes','displayOrder')},indent=2))
if __name__=='__main__':main()
