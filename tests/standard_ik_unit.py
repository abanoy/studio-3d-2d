"""Standard constraint-domain cases; run with Blender's mathutils Python."""
from pathlib import Path
from types import SimpleNamespace
import copy
import json
import math
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"tools"))
from standard_ik import Solver


def fixture():
    return {"asset":{"extras":{"studio_ik_constraints":{"format":"studio_ik_constraints_1","chains":[{"name":"Target","controller":3,"effector":2,"iterations":40,"angle_limit":2.,"links":[{"node":1,"minimum":[.0001,0,0],"maximum":[math.pi,0,0]},{"node":0}]}],"skipped":[]}}},
            "nodes":[{"name":"Root","children":[1]},{"name":"Knee","translation":[0,-1,0],"children":[2]},{"name":"End","translation":[0,-1,0]},{"name":"Target","translation":[0,-2,0]},{"name":"Other"}],"skins":[{"joints":[0,1,2,3,4]}]}


def control(name="Target",translation=(0,.5,0),rotation=(0,0,0,1)):
    return dict(name=name,translation=list(translation),rotation_xyzw=list(rotation))


class Tests(unittest.TestCase):
    def test_hinge_reaches_and_inputs_are_immutable(self):
        data=fixture();before=copy.deepcopy(data);records=[control()]
        result=Solver(SimpleNamespace(doc=data)).apply(records)
        self.assertLess(result["chains"][0]["residual"],1e-5)
        self.assertEqual(data,before);self.assertEqual(records,[control()])
        knee=next(row for row in result["bones"] if row["name"]=="Knee")
        self.assertGreater(knee["rotation_xyzw"][0],0)
        self.assertEqual(knee["rotation_xyzw"][1:3],[0.,0.])

    def test_disabled_chain_restores_fk_base(self):
        result=Solver(SimpleNamespace(doc=fixture())).apply([control()],base=[control("Knee",(0,0,0),(.1,0,0,math.sqrt(.99)))],enabled={"Target":False})
        self.assertFalse(result["chains"][0]["enabled"])
        self.assertAlmostEqual(next(row for row in result["bones"] if row["name"]=="Knee")["rotation_xyzw"][0],.1,places=7)

    def test_unrelated_source_does_not_solve_other_chains(self):
        result=Solver(SimpleNamespace(doc=fixture())).apply([control("Other")],base=[control("Knee",(0,0,0),(.2,0,0,math.sqrt(.96)))])
        self.assertEqual(result["chains"],[]);self.assertEqual(result["bones"],[control("Other")])

    def test_unreachable_target_stays_finite_and_within_limits(self):
        result=Solver(SimpleNamespace(doc=fixture())).apply([control(translation=(0,-2,0))])
        self.assertGreater(result["chains"][0]["residual"],1.99)
        self.assertTrue(all(math.isfinite(v) for row in result["bones"] for v in row["rotation_xyzw"]+row["translation"]))

    def test_bad_link_ancestry(self):
        data=fixture();data["asset"]["extras"]["studio_ik_constraints"]["chains"][0]["links"][0]["node"]=4
        with self.assertRaises(ValueError):Solver(SimpleNamespace(doc=data))

    def test_duplicate_link(self):
        data=fixture();chain=data["asset"]["extras"]["studio_ik_constraints"]["chains"][0];chain["links"].append(chain["links"][0])
        with self.assertRaises(ValueError):Solver(SimpleNamespace(doc=data))

    def test_self_dependent_target(self):
        data=fixture();data["nodes"][0]["children"].append(3)
        with self.assertRaises(ValueError):Solver(SimpleNamespace(doc=data))

    def test_reversed_limits(self):
        data=fixture();data["asset"]["extras"]["studio_ik_constraints"]["chains"][0]["links"][0]["minimum"]=[4,0,0]
        with self.assertRaises(ValueError):Solver(SimpleNamespace(doc=data))

    def test_excess_iterations(self):
        data=fixture();data["asset"]["extras"]["studio_ik_constraints"]["chains"][0]["iterations"]=257
        with self.assertRaises(ValueError):Solver(SimpleNamespace(doc=data))


if __name__=="__main__":
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():raise RuntimeError("Standard IK domain checks failed")
    print("STANDARD_IK_UNIT",result.testsRun,"passed")
