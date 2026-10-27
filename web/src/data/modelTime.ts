/** Strict contract for *decoded and QA'd* forecast assets; not a data provider. */
export type ModelName='HRRR'|'RAP'|'RRFS'|'REFS'|'GFS'|'GEFS';
export type ProcessingState='inventory-only'|'decoded-unverified'|'validated'|'rejected';
export interface ModelFieldAsset {
  model:ModelName;
  parameter:string;
  level:string;
  units:string|null;
  runAt:string;
  leadHours:number;
  validAt:string;
  accumulationStartAt:string|null;
  accumulationEndAt:string|null;
  sourceUrl:string;
  assetUrl:string|null;
  assetFormat:'cog'|'raster-tiles'|'geojson'|null;
  crs:string|null;
  sha256:string|null;
  firstSeenAt:string|null;
  processingState:ProcessingState;
  processingVersion:string|null;
  missingFraction:number|null;
}
const models=new Set<ModelName>(['HRRR','RAP','RRFS','REFS','GFS','GEFS']);
const statuses=new Set<ProcessingState>(['inventory-only','decoded-unverified','validated','rejected']);
function record(x:unknown):x is Record<string,unknown>{
  return typeof x==='object'&&x!==null&&!Array.isArray(x);
}
/** Reject timezone-naive inputs and impossible dates. */
export function strictUtc(value:unknown):string {
  if(typeof value!=='string'||!/^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?)(Z|[+-]\d\d:\d\d)$/.test(value)){
    throw new Error('Timestamp must explicitly include UTC/offset seconds');
  }
  const time=Date.parse(value);
  if(!Number.isFinite(time))throw new Error('Invalid timestamp');
  return new Date(time).toISOString();
}
function string(x:unknown,name:string):string {
  if(typeof x!=='string'||!x.trim())throw new Error(name+' must be nonempty');
  return x;
}
export function parseModelFieldAsset(input:unknown):ModelFieldAsset {
  if(!record(input))throw new Error('Field manifest must be an object');
  const d=input;
  if(!models.has(d.model as ModelName))throw new Error('Unknown model');
  if(!statuses.has(d.processingState as ProcessingState))throw new Error('Unknown processing state');
  const runAt=strictUtc(d.runAt),validAt=strictUtc(d.validAt);
  if(typeof d.leadHours!=='number'||!Number.isInteger(d.leadHours)||d.leadHours<0||d.leadHours>384){
    throw new Error('Invalid forecast lead');
  }
  if(Date.parse(runAt)+d.leadHours*3_600_000!==Date.parse(validAt))throw new Error('Run/lead/valid mismatch');
  const accumStart=d.accumulationStartAt===null?null:strictUtc(d.accumulationStartAt);
  const accumEnd=d.accumulationEndAt===null?null:strictUtc(d.accumulationEndAt);
  if((accumStart===null)!==(accumEnd===null))throw new Error('Accumulation interval bounds required as pair');
  if(accumStart&&accumEnd&&!(accumStart<accumEnd&&accumEnd===validAt&&accumStart>=runAt)){
    throw new Error('Invalid accumulation interval');
  }
  const firstSeen=d.firstSeenAt===null?null:strictUtc(d.firstSeenAt);
  const missing=d.missingFraction;
  if(missing!==null&&(typeof missing!=='number'||!Number.isFinite(missing)||missing<0||missing>1)){
    throw new Error('Invalid missing fraction');
  }
  const stage=d.processingState as ProcessingState;
  if(stage==='validated' && (!d.units||!d.crs||!d.sha256||!d.assetUrl||!d.assetFormat||!firstSeen)){
    throw new Error('Validated model field missing provenance/units/grid asset');
  }
  if(d.sha256!==null && (typeof d.sha256!=='string'||!/^[a-f0-9]{64}$/.test(d.sha256))){
    throw new Error('Invalid SHA256');
  }
  const format=d.assetFormat;
  if(format!==null && format!=='cog'&&format!=='raster-tiles'&&format!=='geojson')throw new Error('Unsupported asset format');
  const assetUrl=d.assetUrl;
  if(assetUrl!==null) {
    string(assetUrl,'assetUrl');
    if(!(assetUrl.startsWith('/')&&!assetUrl.startsWith('//'))&&!/^https:\/\//.test(assetUrl)){
      throw new Error('Asset URL must be absolute HTTPS or local root path');
    }
  }
  return {
    model:d.model as ModelName,
    parameter:string(d.parameter,'parameter'),level:string(d.level,'level'),
    units:d.units===null?null:string(d.units,'units'),
    runAt,leadHours:d.leadHours,validAt,
    accumulationStartAt:accumStart,accumulationEndAt:accumEnd,
    sourceUrl:string(d.sourceUrl,'sourceUrl'),assetUrl:assetUrl as string|null,
    assetFormat:format as ModelFieldAsset['assetFormat'],
    crs:d.crs===null?null:string(d.crs,'crs'),
    sha256:d.sha256 as string|null,firstSeenAt:firstSeen,
    processingState:stage,
    processingVersion:d.processingVersion===null?null:string(d.processingVersion,'processingVersion'),
    missingFraction:missing as number|null
  };
}
export interface ModelComparison {
  validAt:string;model:ModelName;parameter:string;level:string;
  available:ModelFieldAsset[];unavailable:number;
}
/** Same-valid-time comparison: never overwrite run times or silently substitute a cycle. */
export function compareRuns(items:ModelFieldAsset[],query:{model:ModelName;parameter:string;level:string;validAt:string}):ModelComparison {
  const validAt=strictUtc(query.validAt);
  const matching=items.filter(d=>d.model===query.model&&d.parameter===query.parameter&&
    d.level===query.level&&d.validAt===validAt);
  return {
    validAt,model:query.model,parameter:query.parameter,level:query.level,
    available:matching.filter(d=>d.processingState==='validated'&&d.assetUrl!==null)
      .sort((a,b)=>b.runAt.localeCompare(a.runAt)),
    unavailable:matching.filter(d=>d.processingState!=='validated'||d.assetUrl===null).length
  };
}
