from pathlib import Path
import hashlib
import importlib.util
import math
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from mmd_motion import read_motion,Sampler,bezier,slerp


def interpolation():
    values=bytearray(64)
    for base,points in zip((0,16,32,48),((0,127,127,127),(20,20,107,107),(127,0,127,0),(0,127,127,127))):
        for index,value in zip((0,4,8,12),points):values[base+index]=value
    return values


def fixture():
    sign=b"Vocaloid Motion Data 0002".ljust(30,b"\0")+"Miku".encode().ljust(20,b"\0")
    def bone(frame,pos,rot):
        return "左腕".encode("cp932").ljust(15,b"\0")+struct.pack("<I7f",frame,*pos,*rot)+interpolation()
    def morph(frame,weight):
        return "まばたき".encode("cp932").ljust(15,b"\0")+struct.pack("<If",frame,weight)
    return sign+struct.pack("<I",2)+bone(30,[10,20,30],[0,0,math.sqrt(.5),math.sqrt(.5)])+bone(0,[0,0,0],[0,0,0,1])+struct.pack("<I",2)+morph(30,1)+morph(0,0)+struct.pack("<4I",0,0,0,0)


def camera_fixture():
    return fixture()[:50]+struct.pack("<3I",0,0,1)+struct.pack("<I7f",0,2,0,0,0,0,0,0)+bytes([20]*24)+struct.pack("<IB3I",45,0,0,0,0)


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"original.vmd"
        self.path.write_bytes(fixture())

    def test_order_and_japanese_names(self):
        motion=read_motion(self.path)
        self.assertEqual([k["frame"] for k in motion["bones"]["左腕"]],[0,30])
        self.assertEqual(motion["morphs"]["まばたき"][1]["weight"],1)
        self.assertEqual(motion["source_sha256"],hashlib.sha256(fixture()).hexdigest())
        self.assertEqual(self.path.read_bytes(),fixture())

    def test_nonlinear_axes_and_rotation(self):
        sampler=Sampler(read_motion(self.path))
        sample=sampler.sample(15)
        bone=sample["bones"][0]
        self.assertAlmostEqual(bone["position"][0],8.75,places=10)
        self.assertAlmostEqual(bone["position"][1],10,places=10)
        self.assertNotAlmostEqual(bone["position"][2],15,places=2)
        self.assertAlmostEqual(bone["rotation_xyzw"][2],math.sin(math.pi*.875/4),places=7)
        self.assertEqual(sample["morphs"][0]["weight"],.5)
        self.assertAlmostEqual(bezier(.15625,(0,127,127,127)),.578125,places=12)

    def test_frame_rate_mapping(self):
        sampler=Sampler(read_motion(self.path))
        self.assertEqual(sampler.sample_project_frame(24,24),sampler.sample(30))
        self.assertEqual(sampler.sample_project_frame(12,30000,1001),sampler.sample(12.012))
        self.assertEqual(sampler.sample_project_frame(8,24,1,5),sampler.sample(15))

    def test_outside_keys_holds_endpoints(self):
        sampler=Sampler(read_motion(self.path))
        self.assertEqual(sampler.sample(0)["bones"][0]["position"],[0,0,0])
        self.assertEqual(sampler.sample(100)["bones"][0]["position"],[10,20,30])

    def test_shortest_quaternion_path(self):
        self.assertEqual(slerp([0,0,0,1],[0,0,0,-1],.5),(0,0,0,1))
        self.assertEqual(slerp([0,0,0,0],[0,0,0,0],.5),(0,0,0,1))

    def test_non_model_sections_are_inventoried(self):
        self.path.write_bytes(camera_fixture())
        motion=read_motion(self.path)
        self.assertEqual(motion["bones"],{})
        self.assertEqual(motion["other_sections"]["camera"],1)
        data=fixture()[:-4]+struct.pack("<IIBI",1,7,1,1)+"左足ＩＫ".encode("cp932").ljust(20,b"\0")+b"\x00"
        self.path.write_bytes(data)
        motion=read_motion(self.path)
        self.assertEqual(motion["other_sections"]["ik_switches"],1)
        sampler=Sampler(motion)
        self.assertEqual(sampler.sample(6)["ik_enabled"],{})
        self.assertEqual(sampler.sample(7)["ik_enabled"],{"左足ＩＫ":False})
        self.assertEqual(sampler.sample(40)["ik_enabled"],{"左足ＩＫ":False})

    def test_truncation_and_bad_counts(self):
        data=fixture()
        for end in (0,29,49,53,100,len(data)-1):
            self.path.write_bytes(data[:end])
            with self.assertRaises(ValueError):read_motion(self.path)
        self.path.write_bytes(data[:50]+struct.pack("<I",200001)+data[54:])
        with self.assertRaises(ValueError):read_motion(self.path)

    def test_bad_values_duplicate_keys_and_tail(self):
        data=fixture()
        variants=[data+b"unknown",data[:73]+struct.pack("<f",float("nan"))+data[77:],
                  data[:180]+struct.pack("<I",30)+data[184:]]
        for variant in variants:
            self.path.write_bytes(variant)
            with self.assertRaises(ValueError):read_motion(self.path)

    def test_independent_installed_writer_reader(self):
        path=Path.home()/"AppData/Roaming/Blender Foundation/Blender/5.1/extensions/user_default/mmd_tools/core/vmd/__init__.py"
        if not path.is_file():self.skipTest("Installed independent MMD Tools reader unavailable")
        spec=importlib.util.spec_from_file_location("independent_vmd",path)
        reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
        original=reference.File();original.load(filepath=str(self.path))
        rewritten=Path(self.temp.name)/"independent.vmd";original.save(filepath=str(rewritten))
        parsed=read_motion(rewritten)
        for native,keys in original.boneAnimation.items():
            expected=sorted(keys,key=lambda key:key.frame_number)
            for actual,key in zip(parsed["bones"][native],expected):
                self.assertEqual(actual["position"],list(key.location))
                self.assertEqual(actual["rotation_xyzw"],list(key.rotation))
        self.assertEqual(parsed["morphs"]["まばたき"],[{"frame":0,"weight":0.},{"frame":30,"weight":1.}])


if __name__=="__main__":unittest.main()
