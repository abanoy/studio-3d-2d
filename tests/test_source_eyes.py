from pathlib import Path
import math,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from source_eyes import project

class EyeProjection(unittest.TestCase):
    def test_native_frame_center_and_radius(self):
        self.assertEqual(project([(0,0,0),(-2,0,0),(2,0,0),(0,0,-2),(0,0,2)],2,0),[(.5,.5),(0,.5),(1,.5),(.5,0),(.5,1)])
    def test_source_offset_uses_forward_axis(self):
        a,b=project([(0,1,0),(0,-1,0)],1,math.pi/2)
        self.assertAlmostEqual(a[0],1);self.assertAlmostEqual(b[0],0)
    def test_invalid_parameters_refuse(self):
        for radius,angle in [(0,0),(-1,0),(math.inf,0),(math.nan,0),(1,math.inf),(1,4)]:
            with self.subTest(radius=radius,angle=angle),self.assertRaises(ValueError):project([(0,0,0)],radius,angle)
    def test_invalid_coordinates_refuse(self):
        for point in [(0,0),(0,0,math.nan),(0,math.inf,0),(0,0,1e7)]:
            with self.subTest(point=point),self.assertRaises(ValueError):project([point],1,0)
    def test_texture_edge_clamping_is_not_uv_clamping(self):
        self.assertEqual(project([(-2,0,0),(2,0,0)],1,0),[(-.5,.5),(1.5,.5)])
    def test_no_input_mutation(self):
        points=[[1,0,0],[0,0,1]];project(points,1,0);self.assertEqual(points,[[1,0,0],[0,0,1]])

if __name__=='__main__':unittest.main()
