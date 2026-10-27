import unittest
import numpy as np
from pipelines.hrrr_georeg import nearest_regrid, raster_grid, png_rgba, unit_sphere

class SpatialQATests(unittest.TestCase):
    def test_corner_pixel_center_and_north_up(self):
        x,y=raster_grid((-100,34,-99,35),0.25)
        self.assertEqual(x.shape,(4,4))
        self.assertAlmostEqual(x[0,0],-99.875)
        self.assertAlmostEqual(y[0,0],34.875)
        self.assertAlmostEqual(y[-1,0],34.125)
    def test_sphere_handles_longitude_360_wrap(self):
        self.assertTrue(np.allclose(unit_sphere(np.array([-100]),np.array([35])),
                                    unit_sphere(np.array([260]),np.array([35]))))
    def test_nearest_matches_actual_grid_not_synthetic_smooth_field(self):
        x,y=raster_grid((-100,34,-99,35),0.125)
        grid_values=260+np.arange(x.size,dtype=float)
        result,qa=nearest_regrid(y.ravel(),(x.ravel()%360),grid_values,
                                 bounds=(-100,34,-99,35),step=0.125,max_km=0.01)
        np.testing.assert_allclose(result.ravel(),grid_values)
        self.assertAlmostEqual(qa["coverage_fraction"],1.0)
    def test_missing_regional_coverage_fails_closed(self):
        x,y=raster_grid((-100,34,-99,35),0.05)
        with self.assertRaises(ValueError):
            nearest_regrid(y.ravel(),x.ravel(),np.full(x.size,np.nan),
                           bounds=(-100,34,-99,35),step=0.05)
    def test_png_does_not_paint_missing_values(self):
        data=np.array([[270.0,np.nan]],dtype=np.float32)
        rgba=png_rgba(data,"temperature")
        self.assertEqual(int(rgba[0,0,3]),185)
        self.assertEqual(int(rgba[0,1,3]),0)
    def test_delta_uses_actual_zero_change_neutral(self):
        rgba=png_rgba(np.array([[0.0,1.0]],dtype=np.float32),"trend")
        self.assertTrue(np.all(rgba[0,0,:3]==np.array([236,233,226])))

if __name__=="__main__":
    unittest.main()
