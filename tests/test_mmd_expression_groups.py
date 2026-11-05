import copy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from mmd_expression_groups import normalize

def group(name,binds,english=''):
    return {'name':name,'english_name':english,'binds':[{'kind':kind,'name':target,'weight':weight}for kind,target,weight in binds]}
def doc():
    return {'nodes':[{'mesh':0},{'mesh':0}],'meshes':[{'extras':{'targetNames':['Eye','Mouth']}}]}
class Groups(unittest.TestCase):
    def test_nested_repeated_signed_and_multiple_instances(self):
        groups=[group('JP',[('vertex_morphs','Eye',.6),('vertex_morphs','Mouth',.4)],'Friendly'),group('Nested',[('group_morphs','JP',.5),('vertex_morphs','Eye',-.2)])]
        before=copy.deepcopy(groups);r=normalize(groups,doc());self.assertFalse(r['error']);self.assertEqual(r['entries'][0]['label'],'Friendly')
        binds=r['entries'][1]['binds'];self.assertEqual(len(binds),4);self.assertAlmostEqual(binds[0]['weight'],.1);self.assertAlmostEqual(binds[1]['weight'],.2);self.assertEqual(groups,before)
    def test_unsupported_whole_pose(self):
        for kind in ['bone_morphs','uv_morphs','material_morphs','future']:
            with self.subTest(kind=kind):
                r=normalize([group('Mixed',[('vertex_morphs','Eye',1),(kind,'unknown',1)])],doc())['entries'][0]
                self.assertTrue(r['error']);self.assertEqual(r['binds'],[])
    def test_missing_and_duplicate_group(self):
        for rows in [[group('A',[('group_morphs','B',1)])],[group('A',[]),group('A',[])]]:
            self.assertTrue(all(r['error']for r in normalize(rows,doc())['entries']))
    def test_cycle(self):
        rows=[group('A',[('group_morphs','B',1)]),group('B',[('group_morphs','A',1)])]
        self.assertTrue(all(r['error']for r in normalize(rows,doc())['entries']))
    def test_zero_unsupported_branch_is_inert(self):
        self.assertFalse(normalize([group('A',[('vertex_morphs','Eye',1),('uv_morphs','future',0)])],doc())['entries'][0]['error'])
    def test_invalid_weights(self):
        for weight in [math.nan,math.inf,True,101,'1']:
            with self.subTest(weight=weight):self.assertTrue(normalize([group('A',[('vertex_morphs','Eye',weight)])],doc())['entries'][0]['error'])
    def test_missing_leaf(self):
        self.assertTrue(normalize([group('A',[('vertex_morphs','Foreign',1)])],doc())['entries'][0]['error'])
    def test_group_budget(self):
        self.assertTrue(normalize([group(str(i),[])for i in range(257)],doc())['error'])
    def test_no_invented_groups(self):self.assertEqual(normalize([],doc())['entries'],[])
    def test_duplicate_mesh_names_refuse(self):
        value=doc();value['meshes'][0]['extras']['targetNames']=['Eye','Eye'];self.assertTrue(normalize([],value)['error'])
    def test_resolved_binding_budget(self):
        value=doc();value['nodes']=[{'mesh':0}for _ in range(2049)];self.assertTrue(normalize([group('A',[('vertex_morphs','Eye',1)])],value)['error'])
    def test_depth_budget(self):
        rows=[group(str(i),[('group_morphs',str(i+1),1)])for i in range(33)]+[group('33',[('vertex_morphs','Eye',1)])]
        self.assertTrue(normalize(rows,doc())['entries'][0]['error'])
if __name__=='__main__':unittest.main()
