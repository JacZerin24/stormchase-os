/** Preset extents are viewing aids, not forecast targets or jurisdiction boundaries. */
export type RegionKey = 'conus' | 'southern-plains' | 'central-plains' | 'lower-mississippi';
export const REGION_OPTIONS: ReadonlyArray<{value: RegionKey; label: string}> = [
  {value:'conus',label:'Contiguous United States'},
  {value:'southern-plains',label:'Southern Plains'},
  {value:'central-plains',label:'Central Plains'},
  {value:'lower-mississippi',label:'Lower Mississippi Valley'}
];
export const REGION_BOUNDS: Record<RegionKey, [[number,number],[number,number]]> = {
  conus: [[-125,24],[-66,50]],
  'southern-plains': [[-106,29],[-92,38]],
  'central-plains': [[-105,36],[-92,45]],
  'lower-mississippi': [[-95,28],[-86,37]]
};
