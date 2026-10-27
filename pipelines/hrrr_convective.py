"""Source-grounded HRRR convective/upper-air inventory (NOT decoded forecasts).

Each product must match the exact NOAA source variable, layer and time-window
descriptor. 'UH track' is a forecast max-over-time swath, not an observed storm
trajectory or tornado probability; REFC is simulated, never observed radar.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass,asdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json
from pipelines.hrrr_subset import Entry,fetch_index,parse_idx,source_url,utc_cycle

CAP_BYTES=16*1024*1024
DATA = "# key|group|label|GRIB key|level|semantics|units\nrefc|storm|Simulated composite reflectivity|REFC|entire atmosphere|instant|dBZ\nmaxref_1km|storm|Hourly max simulated 1km reflectivity|MAXREF|1000 m above ground|hourly_max|dBZ\nrefd_1km|storm|Simulated 1km reflectivity|REFD|1000 m above ground|instant|dBZ\nrefd_4km|storm|Simulated 4km reflectivity|REFD|4000 m above ground|instant|dBZ\nvil|storm|Model vertically integrated liquid|VIL|entire atmosphere|instant|kg/m2\necho_top|storm|Simulated echo-top height|RETOP|cloud top|instant|m\nuh25_max|storm|Hourly max 2-5km updraft helicity|MXUPHL|5000-2000 m above ground|hourly_max|m2/s2\nuh25_min|storm|Hourly min 2-5km updraft helicity|MNUPHL|5000-2000 m above ground|hourly_min|m2/s2\nuh02_max|storm|Hourly max 0-2km updraft helicity|MXUPHL|2000-0 m above ground|hourly_max|m2/s2\nuh02_min|storm|Hourly min 0-2km updraft helicity|MNUPHL|2000-0 m above ground|hourly_min|m2/s2\nuh03_max|storm|Hourly max 0-3km updraft helicity|MXUPHL|3000-0 m above ground|hourly_max|m2/s2\nupdraft_max|storm|Hourly max updraft speed|MAXUVV|100-1000 mb above ground|hourly_max|m/s\ndowndraft_max|storm|Hourly max downdraft speed|MAXDVV|100-1000 mb above ground|hourly_max|m/s\nhail_max|storm|Model hail diagnostic|HAIL|entire atmosphere|hourly_max|m\nltng|storm|Model lightning diagnostic|LTNG|entire atmosphere|instant|index\ncape_sb|buoyancy|Surface CAPE|CAPE|surface|instant|J/kg\ncin_sb|buoyancy|Surface CIN|CIN|surface|instant|J/kg\ncape_ml180|buoyancy|0-180hPa AGL-layer CAPE|CAPE|180-0 mb above ground|instant|J/kg\ncin_ml180|buoyancy|0-180hPa AGL-layer CIN|CIN|180-0 mb above ground|instant|J/kg\ncape_ml90|buoyancy|0-90hPa AGL-layer CAPE|CAPE|90-0 mb above ground|instant|J/kg\ncin_ml90|buoyancy|0-90hPa AGL-layer CIN|CIN|90-0 mb above ground|instant|J/kg\ncape_mu255|buoyancy|0-255hPa AGL-layer CAPE|CAPE|255-0 mb above ground|instant|J/kg\ncin_mu255|buoyancy|0-255hPa AGL-layer CIN|CIN|255-0 mb above ground|instant|J/kg\ncape_03km|buoyancy|0-3km AGL CAPE|CAPE|0-3000 m above ground|instant|J/kg\nlcl_hgt|buoyancy|Surface parcel LCL height|HGT|level of adiabatic condensation from sfc|instant|gpm\nli_sfc|buoyancy|Surface lifted index|LFTX|500-1000 mb|instant|K\npwat|moisture|Precipitable water|PWAT|entire atmosphere (considered as a single layer)|instant|kg/m2\nt2m|surface|2m temperature|TMP|2 m above ground|instant|K\ntd2m|surface|2m dewpoint|DPT|2 m above ground|instant|K\nrh2m|surface|2m RH|RH|2 m above ground|instant|%\nu10m|surface|10m U wind|UGRD|10 m above ground|instant|m/s\nv10m|surface|10m V wind|VGRD|10 m above ground|instant|m/s\ngust|surface|Surface gust|GUST|surface|instant|m/s\nmaxwind10|surface|Hourly maximum 10m wind|WIND|10 m above ground|hourly_max|m/s\nsrh01|shear|Model storm-relative helicity 0-1km|HLCY|1000-0 m above ground|instant|m2/s2\nsrh03|shear|Model storm-relative helicity 0-3km|HLCY|3000-0 m above ground|instant|m2/s2\nshearu01|shear|0-1km vertical U wind gradient|VUCSH|0-1000 m above ground|instant|s-1\nshearv01|shear|0-1km vertical V wind gradient|VVCSH|0-1000 m above ground|instant|s-1\nshearu06|shear|0-6km vertical U wind gradient|VUCSH|0-6000 m above ground|instant|s-1\nshearv06|shear|0-6km vertical V wind gradient|VVCSH|0-6000 m above ground|instant|s-1\nstorm_u|shear|Model storm-motion U|USTM|0-6000 m above ground|instant|m/s\nstorm_v|shear|Model storm-motion V|VSTM|0-6000 m above ground|instant|m/s\napcp_since_run|precip|Accumulated rain since run|APCP|surface|since_run_accum|kg/m2\napcp_1h|precip|1h accumulated rain|APCP|surface|hourly_accum|kg/m2\nprate|precip|Precipitation rate|PRATE|surface|instant|kg/m2/s\nhgt500|upper|500hPa geopotential height|HGT|500 mb|instant|gpm\nt500|upper|500hPa temperature|TMP|500 mb|instant|K\ntd500|upper|500hPa dewpoint|DPT|500 mb|instant|K\nu500|upper|500hPa U wind|UGRD|500 mb|instant|m/s\nv500|upper|500hPa V wind|VGRD|500 mb|instant|m/s\nhgt700|upper|700hPa geopotential height|HGT|700 mb|instant|gpm\nt700|upper|700hPa temperature|TMP|700 mb|instant|K\ntd700|upper|700hPa dewpoint|DPT|700 mb|instant|K\nu700|upper|700hPa U wind|UGRD|700 mb|instant|m/s\nv700|upper|700hPa V wind|VGRD|700 mb|instant|m/s\ndzdt700|upper|700hPa geometric vertical velocity|DZDT|700 mb|instant|m/s\nhgt850|upper|850hPa geopotential height|HGT|850 mb|instant|gpm\nt850|upper|850hPa temperature|TMP|850 mb|instant|K\ntd850|upper|850hPa dewpoint|DPT|850 mb|instant|K\nu850|upper|850hPa U wind|UGRD|850 mb|instant|m/s\nv850|upper|850hPa V wind|VGRD|850 mb|instant|m/s\nt925|upper|925hPa temperature|TMP|925 mb|instant|K\ntd925|upper|925hPa dewpoint|DPT|925 mb|instant|K\nu925|upper|925hPa U wind|UGRD|925 mb|instant|m/s\nv925|upper|925hPa V wind|VGRD|925 mb|instant|m/s\nu250|upper|250hPa U wind|UGRD|250 mb|instant|m/s\nv250|upper|250hPa V wind|VGRD|250 mb|instant|m/s\nu300|upper|300hPa U wind|UGRD|300 mb|instant|m/s\nv300|upper|300hPa V wind|VGRD|300 mb|instant|m/s"
@dataclass(frozen=True)
class Field:
    key:str
    group:str
    label:str
    variable:str
    level:str
    timing:str
    units:str

def load_catalog()->dict[str,Field]:
    result={}
    for raw in DATA.splitlines():
        if not raw or raw.startswith('#'):continue
        parts=raw.split('|')
        if len(parts)!=7:raise ValueError('Malformed fixed provider catalog')
        f=Field(*parts)
        if f.key in result:raise ValueError('Duplicate field key')
        if f.timing not in ('instant','hourly_max','hourly_min','hourly_accum','since_run_accum'):
            raise ValueError('Unknown time statistic')
        result[f.key]=f
    return result

FIELDS=load_catalog()
def descriptor(field:Field,lead:int)->str:
    if type(lead) is not int or lead<1 or lead>48:raise ValueError('Lead must be 1..48')
    kind=field.timing
    if kind=='instant':return f'{lead} hour fcst'
    if kind=='hourly_max':return f'{lead-1}-{lead} hour max'
    if kind=='hourly_min':return f'{lead-1}-{lead} hour min'
    if kind=='hourly_accum':return f'{lead-1}-{lead} hour acc'
    if kind=='since_run_accum':return f'0-{lead} hour acc'
    raise ValueError('Unknown statistic')

def select(entries:list[Entry],field:Field,lead:int)->dict:
    matches=[(i,e) for i,e in enumerate(entries) if
             (e.variable,e.level,e.descriptor)==(field.variable,field.level,descriptor(field,lead))]
    if len(matches)!=1:
        return {'status':'missing' if not matches else 'ambiguous','count':len(matches)}
    i,e=matches[0]
    end=entries[i+1].offset-1 if i+1<len(entries) else None
    if end is None or not 0<end-e.offset+1<=CAP_BYTES:
        return {'status':'unbounded','count':1}
    start_lead=(lead-1 if field.timing in ('hourly_max','hourly_min','hourly_accum')
                else 0 if field.timing=='since_run_accum' else None)
    return {'status':'index_verified','count':1,'record':e.raw,'start':e.offset,
            'end':end,'bytes':end-e.offset+1,'descriptor':e.descriptor,
            'intervalStartLead':start_lead,'intervalEndLead':lead if start_lead is not None else None,
            'validTimeMeaning':'interval_end' if start_lead is not None else 'instant'}

def inspect(run:datetime,lead:int,keys:list[str]|None=None,fetcher=fetch_index)->dict:
    selected=list(FIELDS) if keys is None else keys
    if not selected or len(selected)>len(FIELDS) or len(set(selected))!=len(selected):
        raise ValueError('Empty/duplicate/unbounded selection')
    if set(selected)-set(FIELDS):raise ValueError('Unknown products')
    url=source_url(run,lead)
    entries=parse_idx(fetcher(url),run)
    records={k:select(entries,FIELDS[k],lead) for k in selected}
    return {
        'schema':'stormchase-hrrr-convective-inventory/1',
        'source':url,'index':url+'.idx','runAt':run.isoformat().replace('+00:00','Z'),
        'validAt':(run+timedelta(hours=lead)).isoformat().replace('+00:00','Z'),
        'forecastHour':lead,'observedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        'inventoryRecords':len(entries),'checkedProducts':len(records),
        'indexVerified':sum(v['status']=='index_verified' for v in records.values()),
        'products':records,'decoded':False,'modelOutputOnly':True,
        'firstPublicationAt':None,'independentForecastVerification':'not performed'}

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',required=True)
    p.add_argument('--lead',type=int,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--fields',nargs='*')
    args=p.parse_args()
    report=inspect(utc_cycle(args.run),args.lead,args.fields)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('runAt','validAt','checkedProducts','indexVerified')},indent=2))
    print('Not index-verified:',{k:v['status'] for k,v in report['products'].items() if v['status']!='index_verified'})
if __name__=='__main__':main()
