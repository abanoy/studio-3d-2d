"""Atomic multi-part composition, original review identity and conflict guards."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_secondary_helpers import H, fixture, request, two_panel_fixture, write_glb
from test_secondary_existing_joints import existing_fixture
from test_helper_morphs import shape_fixture
import secondary_helpers_batch as batch


class HelperBatch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root/'source.glb'; self.g = two_panel_fixture(self.source)
    def tearDown(self): self.temp.cleanup()
    def plans(self):
        first = request(self.g); second = dict(first, component=1)
        return {'format': batch.FORMAT, 'source_sha256': self.g.sha, 'reviewed': True, 'items': [first, second]}
    def assert_original(self, raw, stamp):
        self.assertEqual(self.source.read_bytes(), raw); self.assertEqual(self.source.stat().st_mtime_ns, stamp)
    def test_two_parts_compose_and_rebase_actual_sources_without_changing_the_original(self):
        raw=self.source.read_bytes(); stamp=self.source.stat().st_mtime_ns; plans=self.plans(); unchanged=copy.deepcopy(plans)
        value=batch.build(self.source,self.root/'out',plans); final=H.GLB(value['glb'])
        self.assertEqual(plans,unchanged); self.assert_original(raw,stamp)
        self.assertEqual(len(final.springs()),2); self.assertEqual(len(value['reports']),2)
        self.assertEqual(value['reports'][0]['source_sha256'],self.g.sha)
        self.assertNotEqual(value['reports'][1]['source_sha256'],self.g.sha)
        self.assertEqual(value['batch']['source_sha256'],self.g.sha)
        self.assertEqual(value['batch']['final_sha256'],final.sha)
        self.assertEqual(json.loads((self.root/'out/helpers.json').read_bytes()),json.loads(json.dumps(value['report'])))
        # Each independent strip keeps the other one's original POSITION/morph/material contract.
        self.assertEqual(final.doc['meshes'][0]['primitives'][1]['attributes']['POSITION'],self.g.doc['meshes'][0]['primitives'][1]['attributes']['POSITION'])
        self.assertEqual(final.doc['materials'],self.g.doc['materials'])
        self.assertEqual(final.doc['meshes'][0]['primitives'][1]['targets'],self.g.doc['meshes'][0]['primitives'][1]['targets'])
        self.assertEqual(final.skin(3,0)[6],self.g.skin(3,0)[6])
        self.assertFalse(list(self.root.glob('.has-secondary-batch-*')))
    def test_imported_vrm_chains_and_settings_survive_the_complete_batch(self):
        for family in ('v0','v1'):
            with self.subTest(family=family):
                self.g=two_panel_fixture(self.source,family)
                value=batch.build(self.source,self.root/family,self.plans()); final=H.GLB(value['glb'])
                self.assertEqual(final.doc['extensions'],self.g.doc['extensions'])
                self.assertEqual(len(final.springs()),3)
                self.assertTrue(bytes(final.binary).startswith(self.g.binary))
    def test_disjoint_patches_in_one_connected_part_compose(self):
        self.g=fixture(self.source); plans=self.plans()
        plans['items'][0]['vertex_mask']=list(range(8)); plans['items'][1].update(component=0,vertex_mask=list(range(12,20)))
        value=batch.build(self.source,self.root/'out',plans)
        self.assertEqual(len(H.GLB(value['glb']).springs()),2)
    def test_whole_and_overlapping_patch_refuse_before_output(self):
        self.g=fixture(self.source); plans=self.plans(); plans['items'][1].update(component=0,vertex_mask=list(range(8,20)))
        with self.assertRaisesRegex(ValueError,'overlap'): batch.build(self.source,self.root/'out',plans)
        self.assertFalse((self.root/'out').exists())
    def test_overlapping_source_patch_vertices_are_refused(self):
        self.g=fixture(self.source); plans=self.plans(); plans['items'][0]['vertex_mask']=list(range(8,16)); plans['items'][1].update(component=0,vertex_mask=list(range(14,20)),segments=2)
        with self.assertRaisesRegex(ValueError,'overlap'): batch.plan(self.source,plans)
    def test_stale_or_unreviewed_item_never_publishes(self):
        for changes in ({'source_sha256':'0'*64},{'reviewed':False},{'anchor_node':999}):
            plans=self.plans(); plans['items'][1].update(changes)
            with self.assertRaises(ValueError): batch.build(self.source,self.root/'out',plans)
            self.assertFalse((self.root/'out').exists())
    def test_one_original_shape_snapshot_is_required(self):
        plans=self.plans(); plans['items'][1]['morph_weights']={'different':[.5]}
        with self.assertRaisesRegex(ValueError,'shape snapshot'): batch.plan(self.source,plans)
    def test_nonzero_authored_shape_defaults_cannot_drift_between_items(self):
        self.g=shape_fixture(self.source); first=dict(request(self.g),source_morph_defaults=True)
        second=dict(first,component=1,source_morph_defaults=False)
        plans={'format':batch.FORMAT,'source_sha256':self.g.sha,'reviewed':True,'items':[first,second]}
        self.assertNotEqual(H.preview(self.source,first)['points_in_anchor'],H.preview(self.source,dict(first,source_morph_defaults=False))['points_in_anchor'])
        with self.assertRaisesRegex(ValueError,'shape snapshot'): batch.build(self.source,self.root/'out',plans)
        self.assertFalse((self.root/'out').exists())
    def test_neutral_default_settings_normalize_absent_and_false(self):
        plans=self.plans(); plans['items'][1].update(source_morph_defaults=False,morph_weights={})
        self.assertEqual(batch.plan(self.source,plans)['added_chains'],2)
    def test_inspection_stamp_is_checked_before_composition(self):
        plans=self.plans(); plans['source_stamp_ns']=str(self.source.stat().st_mtime_ns+1)
        with self.assertRaisesRegex(ValueError,'since inspection'): batch.build(self.source,self.root/'out',plans)
        self.assertFalse((self.root/'out').exists())
    def test_second_builder_failure_keeps_original_and_publishes_nothing(self):
        original_build=H.build; calls=[]; raw=self.source.read_bytes(); stamp=self.source.stat().st_mtime_ns
        def fail_second(*args):
            calls.append(args)
            if len(calls)==2: raise ValueError('second candidate refused')
            return original_build(*args)
        with patch.object(H,'build',side_effect=fail_second):
            with self.assertRaisesRegex(ValueError,'second candidate'): batch.build(self.source,self.root/'out',self.plans())
        self.assertEqual(len(calls),2); self.assertFalse((self.root/'out').exists()); self.assertFalse(list(self.root.glob('.has-secondary-batch-*'))); self.assert_original(raw,stamp)
    def test_real_second_item_instancing_failure_does_not_install_the_first_part(self):
        self.g.doc['meshes'].append({'primitives':[copy.deepcopy(self.g.doc['meshes'][0]['primitives'][1])]})
        first=len(self.g.doc['nodes']); self.g.doc['nodes'] += [{'name':'SharedA','mesh':1,'skin':0},{'name':'SharedB','mesh':1,'skin':0}]
        self.g.doc['nodes'][0]['children'] += [first,first+1]
        write_glb(self.source,self.g.doc,bytes(self.g.binary)); self.g=H.GLB(self.source)
        plans=self.plans(); plans['items'][1].update(node=first,primitive=0,component=0)
        raw=self.source.read_bytes(); stamp=self.source.stat().st_mtime_ns
        with patch.object(H,'build',wraps=H.build) as builder:
            with self.assertRaisesRegex(ValueError,'shared by multiple source nodes'): batch.build(self.source,self.root/'out',plans)
            self.assertEqual(builder.call_count,2)
        self.assertFalse((self.root/'out').exists()); self.assertFalse(list(self.root.glob('.has-secondary-batch-*'))); self.assert_original(raw,stamp)
    def test_existing_output_is_not_replaced(self):
        target=self.root/'out'; target.mkdir(); (target/'keep').write_text('original')
        with self.assertRaisesRegex(ValueError,'never replaced'): batch.build(self.source,target,self.plans())
        self.assertEqual((target/'keep').read_text(),'original'); self.assertEqual(list(target.iterdir()),[target/'keep'])
    def test_combined_skin_budget_refuses_two_individually_fitting_parts(self):
        skin=self.g.doc['skins'][0]
        for i in range(503):
            skin['joints'].append(len(self.g.doc['nodes'])); self.g.doc['nodes'].append({'name':f'Unused{i}'})
        skin['inverseBindMatrices']=self.g.append([H.IDENTITY,H.translation((0,-2,0))]+[H.IDENTITY]*503,'MAT4')
        write_glb(self.source,self.g.doc,bytes(self.g.binary)); self.g=H.GLB(self.source)
        with self.assertRaisesRegex(ValueError,'512skin-bone'): batch.build(self.source,self.root/'out',self.plans())
        self.assertFalse((self.root/'out').exists())
    def test_combined_spring_budget_refuses_batch_before_building(self):
        start=len(self.g.doc['nodes']); self.g.doc['nodes'] += [{'name':'OtherSpringA'},{'name':'OtherSpringB'}]
        self.g.doc['extras']={'has_secondary_helpers_1':{'specVersion':'1.0','springs':[{'joints':[{'node':start},{'node':start+1}]} for _ in range(127)]}}
        write_glb(self.source,self.g.doc,bytes(self.g.binary)); self.g=H.GLB(self.source)
        with self.assertRaisesRegex(ValueError,'128spring'): batch.build(self.source,self.root/'out',self.plans())
        self.assertFalse((self.root/'out').exists())
    def test_combined_source_node_budget_refuses_before_building(self):
        self.g.doc['nodes'] += [{} for _ in range(99993-len(self.g.doc['nodes']))]
        write_glb(self.source,self.g.doc,bytes(self.g.binary)); self.g=H.GLB(self.source)
        with self.assertRaisesRegex(ValueError,'100000source-node'): batch.build(self.source,self.root/'out',self.plans())
        self.assertFalse((self.root/'out').exists())
    def test_combined_spring_node_budget_includes_native_and_generated_joints(self):
        self.g=existing_fixture(self.source); start=len(self.g.doc['nodes'])
        self.g.doc['nodes'] += [{'name':f'OtherSpring{i}'} for i in range(507)]
        self.g.doc['extras']={'has_secondary_helpers_1':{'specVersion':'1.0','springs':[{'joints':[{'node':start+i} for i in range(507)]}]}}
        write_glb(self.source,self.g.doc,bytes(self.g.binary)); self.g=H.GLB(self.source)
        first=dict(request(self.g),anchor_node=4,use_existing_joints=True)
        second=dict(request(self.g),primitive=0,component=0,anchor_node=1)
        plans={'format':batch.FORMAT,'source_sha256':self.g.sha,'reviewed':True,'items':[first,second]}
        with self.assertRaisesRegex(ValueError,'512spring-node'): batch.build(self.source,self.root/'out',plans)
        self.assertFalse((self.root/'out').exists())
    def test_invalid_corrected_controls_refuse_without_publishing(self):
        plans=self.plans(); plans['items'][1]['points_in_anchor']=[[0,0,0]]*4
        raw=self.source.read_bytes(); stamp=self.source.stat().st_mtime_ns
        with self.assertRaisesRegex(ValueError,'zero-length'): batch.build(self.source,self.root/'out',plans)
        self.assertFalse((self.root/'out').exists()); self.assertFalse(list(self.root.glob('.has-secondary-batch-*'))); self.assert_original(raw,stamp)
    def test_review_and_build_retain_each_individual_joint_correction(self):
        plans=self.plans(); corrections=[]
        for index,item in enumerate(plans['items']):
            controls=H.preview(self.source,item)['points_in_anchor']
            item['points_in_anchor']=[[p[0]+(.03 if index==0 else -.04),p[1],p[2]] for p in controls]
            corrections.append(item['points_in_anchor'])
            self.assertEqual(batch.review(self.source,item)['points_in_anchor'],item['points_in_anchor'])
        result=batch.build(self.source,self.root/'out',plans)
        self.assertEqual([json.loads(json.dumps(r['points_in_anchor'])) for r in result['reports']],corrections)
    def test_worker_review_retains_actual_corrections_in_its_atomic_receipt(self):
        item=self.plans()['items'][0]; item['points_in_anchor']=[[p[0]+.03,p[1],p[2]] for p in H.preview(self.source,item)['points_in_anchor']]
        folder=self.root/'worker-review';folder.mkdir();(folder/'request.json').write_text(json.dumps(item))
        subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'tools/secondary_helper_worker.py'),str(self.source),'review',str(folder)],check=True,capture_output=True)
        result=json.loads((folder/'result.json').read_bytes());self.assertTrue(result['ok']);self.assertEqual(result['value']['points_in_anchor'],item['points_in_anchor']);self.assertFalse((folder/'result.json.tmp').exists())
    def test_final_worker_source_check_uses_the_exact_nanosecond_stamp(self):
        stamp=self.source.stat().st_mtime_ns
        for delta in (0,1):
            folder=self.root/f'worker-check-{delta}';folder.mkdir();(folder/'request.json').write_text(json.dumps({'source_sha256':self.g.sha,'source_stamp_ns':str(stamp+delta)}))
            subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'tools/secondary_helper_worker.py'),str(self.source),'source_check',str(folder)],check=True,capture_output=True)
            result=json.loads((folder/'result.json').read_bytes());self.assertEqual(result['ok'],delta==0)
            if delta==0:self.assertEqual(result['value']['source_stamp_ns'],str(stamp))
            else:self.assertIn('Original source changed',result['error'])
    def test_candidate_publish_failure_removes_only_new_owned_output(self):
        original_write=batch._new_json; keep=self.root/'keep.txt'; keep.write_text('untouched')
        def fail_manifest(path,value):
            if path.name=='batch.json': raise OSError('manifest write failed')
            return original_write(path,value)
        raw=self.source.read_bytes(); stamp=self.source.stat().st_mtime_ns
        with patch.object(batch,'_new_json',side_effect=fail_manifest):
            with self.assertRaisesRegex(OSError,'manifest write failed'): batch.build(self.source,self.root/'out',self.plans())
        self.assertFalse((self.root/'out').exists()); self.assertFalse(list(self.root.glob('.has-secondary-batch-*'))); self.assertEqual(keep.read_text(),'untouched'); self.assert_original(raw,stamp)
    def test_source_change_during_publication_rejects_and_removes_candidate(self):
        original_write=batch._new_json; raw=self.source.read_bytes()
        def change_during_publication(path,value):
            result=original_write(path,value)
            if path.name=='batch.json': self.source.write_bytes(raw+b'X')
            return result
        with patch.object(batch,'_new_json',side_effect=change_during_publication):
            with self.assertRaisesRegex(ValueError,'during batch publication'): batch.build(self.source,self.root/'out',self.plans())
        self.assertEqual(self.source.read_bytes(),raw+b'X'); self.assertFalse((self.root/'out').exists()); self.assertFalse(list(self.root.glob('.has-secondary-batch-*')))
    def test_external_source_change_is_kept_and_rejects_the_whole_candidate(self):
        original_build=H.build; calls=[]; raw=self.source.read_bytes()
        def change_original(*args):
            calls.append(args); value=original_build(*args)
            if len(calls)==2: self.source.write_bytes(raw+b'X')
            return value
        with patch.object(H,'build',side_effect=change_original):
            with self.assertRaisesRegex(ValueError,'Original source changed'): batch.build(self.source,self.root/'out',self.plans())
        self.assertEqual(self.source.read_bytes(),raw+b'X'); self.assertFalse((self.root/'out').exists()); self.assertFalse(list(self.root.glob('.has-secondary-batch-*')))
    def test_shared_existing_chain_deduplicates_regions_and_preserves_all_skin(self):
        self.g=existing_fixture(self.source); primitive=self.g.doc['meshes'][0]['primitives'][1]
        js=self.g.accessor(primitive['attributes']['JOINTS_0'],'VEC4'); js[-4:]=[(1,0,0,0),(2,0,0,0),(3,0,0,0),(4,0,0,0)]
        primitive['attributes']['JOINTS_0']=self.g.append(js,'VEC4',5121); write_glb(self.source,self.g.doc,bytes(self.g.binary)); self.g=H.GLB(self.source)
        first=dict(request(self.g),anchor_node=4,use_existing_joints=True); second=dict(first,component=1)
        plans={'format':batch.FORMAT,'source_sha256':self.g.sha,'reviewed':True,'items':[first,second]}
        value=batch.build(self.source,self.root/'out',plans); final=H.GLB(value['glb'])
        self.assertEqual(len(final.springs()),1); self.assertEqual(len(value['reports']),1)
        self.assertEqual(value['batch']['operations'][0]['source_regions'],[[3,1,0],[3,1,1]])
        self.assertEqual(len(value['batch']['operations'][0]['affected_regions']),2)
        for key in ('meshes','skins','accessors','materials'): self.assertEqual(final.doc[key],self.g.doc[key])
        self.assertEqual(final.binary,self.g.binary)
    def test_native_chain_and_weighted_selection_cannot_claim_independent_exclusion(self):
        self.g=existing_fixture(self.source)
        first=dict(request(self.g),anchor_node=4,use_existing_joints=True)
        second=dict(request(self.g),anchor_node=6,vertex_mask=list(range(12,20)))
        plans={'format':batch.FORMAT,'source_sha256':self.g.sha,'reviewed':True,'items':[first,second]}
        with self.assertRaisesRegex(ValueError,'shares moving native joints'): batch.build(self.source,self.root/'out',plans)
        self.assertFalse((self.root/'out').exists())


if __name__=='__main__': unittest.main(verbosity=2)
