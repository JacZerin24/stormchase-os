"""Independent MetPy 1.7.1 comparison on nonuniform prescribed AGL winds.

These are synthetic wind profiles, not observed soundings; passing establishes
formula agreement for these cases, not complete scientific validation.
"""
from __future__ import annotations
import unittest
import numpy as np
from metpy.calc import bulk_shear as metpy_shear
from metpy.calc import storm_relative_helicity as metpy_srh
from metpy.calc import bunkers_storm_motion as metpy_bunkers
from metpy.units import units
from research.wind_profile import Wind, bulk_shear, srh, bunkers_motion

HEIGHT = np.array([0,350,900,1500,2400,3300,4800,5500,6000,7000],dtype=float)
U = np.array([1,4,8,11,12,13,16,19,23,26],dtype=float)
V = np.array([2,3,6,7,5,6,9,11,13,14],dtype=float)
PRESSURE = 1000 * np.exp(-HEIGHT/8000)
WIND = [Wind(float(z),float(u),float(v)) for z,u,v in zip(HEIGHT,U,V)]


class MetPyReferenceTests(unittest.TestCase):
    def test_srh_0_1km_with_explicit_storm_motion(self):
        ours=srh(WIND,0,1000,8,6)
        result=metpy_srh(HEIGHT*units.meter,U*units('m/s'),V*units('m/s'),
                         depth=1000*units.meter,
                         storm_u=8*units('m/s'),storm_v=6*units('m/s'))
        for observed,reference in zip(ours,result):
            self.assertAlmostEqual(observed,float(reference.to('m^2/s^2').magnitude),delta=0.1)

    def test_bulk_0_1km_shear(self):
        ours=bulk_shear(WIND,0,1000)
        u,v=metpy_shear(PRESSURE*units.hPa,U*units('m/s'),V*units('m/s'),
                        height=HEIGHT*units.meter,depth=1000*units.meter)
        self.assertAlmostEqual(ours[0],float(u.to('m/s').magnitude),delta=0.1)
        self.assertAlmostEqual(ours[1],float(v.to('m/s').magnitude),delta=0.1)

    def test_bunkers_mean_right_left(self):
        ours=bunkers_motion(WIND,list(PRESSURE))
        right,left,mean=metpy_bunkers(PRESSURE*units.hPa,U*units('m/s'),
                                      V*units('m/s'),HEIGHT*units.meter)
        for name,ref in (('right',right),('left',left),('mean',mean)):
            self.assertAlmostEqual(ours[name][0],float(ref[0].to('m/s').magnitude),delta=0.1)
            self.assertAlmostEqual(ours[name][1],float(ref[1].to('m/s').magnitude),delta=0.1)


if __name__=="__main__":
    unittest.main()
