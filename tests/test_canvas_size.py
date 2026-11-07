"""Native canvas/sequence-mask metadata rejects unsupported and mistyped dimensions."""
import unittest
from tools import canvas_size as canvas
from tools.sequence_graph import mask_error
class NativeCanvasTests(unittest.TestCase):
    def test_profiles_and_masks(self):
        for key,(width,height) in canvas.PROFILES.items():
            with self.subTest(key=key):
                self.assertEqual(canvas.profile(dict(width=width,height=height)),key)
                self.assertFalse(mask_error(dict(rect=[0,0,width,height],invert=False),(width,height)))
                self.assertTrue(mask_error(dict(rect=[width-1,height-1,2,2],invert=False),(width,height)))
    def test_invalid_dimensions(self):
        for value in [None,[],{},True,dict(width=True,height=720),dict(width='1280',height=720),dict(width=1280,height=1080),dict(width=640,height=360),dict(width=3840,height=2160),dict(width=float('nan'),height=720),dict(width=float('inf'),height=720)]:
            with self.subTest(value=value):self.assertTrue(canvas.error(value))
    def test_integral_json_numbers(self):self.assertEqual(canvas.profile(dict(width=1280.0,height=720.0)),'720p')
if __name__=='__main__':unittest.main()
