import copy
import unittest
import compare_mesh as C
import compare_cases as R


def records():
    return {0:{'position':(0.,0.,0.),'uv':(0.,0.),'weights':{'root':1.},'normal':(0.,0.,1.)},
            1:{'position':(1.,0.,0.),'uv':(1.,0.),'weights':{'root':.25,'hand':.75},'normal':(0.,0.,1.)},
            2:{'position':(0.,1.,0.),'uv':(0.,1.),'weights':{'hand':1.},'normal':(0.,0.,1.)}}


class CompareTests(unittest.TestCase):
    def test_handcomputed_reindex_winding_and_duplicate_triangles(self):
        n=records();d={10:copy.deepcopy(n[0]),11:copy.deepcopy(n[1]),12:copy.deepcopy(n[2])}
        result=C.compare(n,[(0,1,2),(0,1,2)],d,[(12,11,10),(11,10,12)])
        self.assertTrue(result['position_uv_vvd_named_weights_match']);self.assertEqual(result['triangles'],'ATTRIBUTED_ORIENTED_MULTIPLICITY_MATCH')
    def test_opposite_winding_not_fitted(self):
        n=records();r=C.compare(n,[(0,1,2)],n,[(0,1,2)])
        self.assertEqual(r['triangles'],'MISMATCH')
    def test_uv_seam_mismatch_not_collapsed(self):
        n=records();d=copy.deepcopy(n);d[1]['uv']=(0.,0.)
        self.assertFalse(C.compare(n,[(0,1,2)],d,[(2,1,0)])['position_uv_vvd_named_weights_match'])
    def test_joint_identity_and_weight_mismatch_not_hidden(self):
        n=records();d=copy.deepcopy(n);d[1]['weights']={'wrong':.25,'hand':.75}
        self.assertFalse(C.compare(n,None,d,[])['position_uv_vvd_named_weights_match'])
    def test_absent_vtx_is_not_triangle_pass(self):
        n=records();r=C.compare(n,None,n,[])
        self.assertTrue(r['position_uv_vvd_named_weights_match']);self.assertEqual(r['triangles'],'UNRUN_NO_SUPPORTED_NATIVE_VTX')
    def test_preservation_gate_refuses_each_changed_or_missing_state(self):
        good={'all_archives_stage_bundles_and_reports_preserved':True,'source_unchanged':True,'root_head_before':'a'*40,'root_head_after':'a'*40}
        self.assertTrue(R.preservation_ok(good))
        for key in good:
            missing=good.copy();missing.pop(key);self.assertFalse(R.preservation_ok(missing))
        for key in ['all_archives_stage_bundles_and_reports_preserved','source_unchanged']:
            changed=good.copy();changed[key]=False;self.assertFalse(R.preservation_ok(changed))
        changed=good.copy();changed['root_head_after']='b'*40;self.assertFalse(R.preservation_ok(changed))


if __name__=='__main__':unittest.main(verbosity=2)
