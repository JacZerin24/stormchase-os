import unittest
from math import isclose
from research.wind_profile import Wind, bulk_shear, checked, interpolate, srh, bunkers_motion

class WindProfileTests(unittest.TestCase):
    def test_known_linear_interpolation_and_shear(self):
        p=[Wind(0,0,0),Wind(1000,10,0),Wind(6000,20,0)]
        self.assertEqual(interpolate(p,500), Wind(500,5,0))
        du,dv,magnitude=bulk_shear(p,0,1000)
        self.assertEqual((du,dv,magnitude),(10,0,10))
    def test_srh_hodograph_orientation_and_partial_layer(self):
        clockwise=[Wind(0,0,10),Wind(1000,10,0)]
        self.assertEqual(srh(clockwise,0,1000,0,0),(100,0,100))
        self.assertEqual(srh(clockwise,0,500,0,0),(50,0,50))
        anti=[Wind(0,0,10),Wind(1000,-10,0)]
        self.assertEqual(srh(anti,0,1000,0,0),(0,-100,-100))
    def test_srh_storm_motion_affects_result(self):
        p=[Wind(0,0,10),Wind(1000,10,0)]
        self.assertEqual(srh(p,0,1000,5,0),(50,0,50))
    def test_bunkers_uniform_shear_reference(self):
        p=[Wind(z,z/1000.0*2,0) for z in range(0,6001,500)]
        result=bunkers_motion(p)
        self.assertTrue(isclose(result['mean'][0],6))
        self.assertTrue(isclose(result['right'][1],-7.5))
        self.assertTrue(isclose(result['left'][1],7.5))
        self.assertTrue(isclose(result['right'][0],6))
    def test_fail_closed_on_missing_surface_or_top_and_degenerate_shear(self):
        with self.assertRaises(ValueError):checked([Wind(100,0,0),Wind(1000,1,1)])
        p=[Wind(0,1,1),Wind(6000,1,1)]
        with self.assertRaises(ValueError):bunkers_motion(p)
        with self.assertRaises(ValueError):bulk_shear(p,0,6500)
if __name__=='__main__':unittest.main()
