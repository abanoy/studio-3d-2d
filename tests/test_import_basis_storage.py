"""Production container capability routing, atomic refusal and wrapper ancestry."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import has_project as has
import import_basis as basis
import extended_timing as timing
import sequence_graph
import directory_commit as directory

DIGEST=hashlib.sha256(b'synthetic storage-only asset').hexdigest()


def actor(active=True):
    row=dict(format='studio_model_1',id='human',name='Synthetic human',kind='model',parent_id='',
             start_frame=0,sha256=DIGEST,path='assets/'+DIGEST+'.glb',scale=1,
             position=[0,0,0],rotation_xyzw=[0,0,0,1],visible=True,reference_only=False,
             pose={},pose_keys=[],draft_frame=0,metadata={})
    if active:row['asset_basis']=basis.make_basis(DIGEST,'2')
    return row


def project(row=None,version=4):
    out=dict(schema_version=version,video=dict(width=1920,height=1080,fps_num=24,fps_den=1,duration_frames=48),
             layers=[],camera_keys=[],audio={},editor={'frame':0})
    if version==3:out.update(model=row or {},scene={})
    else:
        out['world']=dict(format='studio_world_2' if version==5 else 'studio_world_1',objects=[row] if row else [])
        if version==5:out['world']['effects']=[]
    return out


def sequences(root,child):
    root=deepcopy(root);root['schema_version']=6
    root['sequence_graph']=dict(format='studio_sequences_1',assets=[dict(id='child',name='Child',scene=child,clips=[])],clips=[])
    return root


class BasisStorageTests(unittest.TestCase):
    def test_directory_commit_preserves_active_basis_and_rotates_checked_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'assets').mkdir()
            (root/('assets/'+DIGEST+'.glb')).write_bytes(b'synthetic storage-only asset')
            scene=basis.encode_capability(project(actor()));blob=has.json_bytes(scene)
            candidate='project.json.prepared.tmp';(root/candidate).write_bytes(blob)
            result=directory.commit(root,candidate,'',has.sha(root/candidate),False)
            self.assertTrue(result['ok']);self.assertEqual((root/'project.json').read_bytes(),blob)
            scene['editor']['frame']=1;updated=has.json_bytes(scene);(root/candidate).write_bytes(updated)
            result=directory.commit(root,candidate,has.sha(root/'project.json'),has.sha(root/candidate),True)
            self.assertTrue(result['ok']);self.assertEqual((root/'project.json').read_bytes(),updated)
            self.assertEqual((root/'project.backup.json').read_bytes(),blob)

    def test_directory_commit_rejects_invalid_size_capability_before_payload_sync(self):
        good=basis.encode_capability(project(actor()));invalid=[]
        for field in ('basis_content_schema_version','import_basis_capability'):
            row=deepcopy(good);row.pop(field);invalid.append(row)
        row=deepcopy(good);row['world']['objects'][0]['asset_basis']['factor']='1';invalid.append(row)
        row=deepcopy(good);row['world']['objects'][0]['path']='assets/../foreign.glb';invalid.append(row)
        for scene in invalid:
            with self.subTest(scene=scene),tempfile.TemporaryDirectory() as d:
                root=Path(d);before=b'{"schema_version":4,"generation":"before"}';backup=b'{"schema_version":4,"generation":"older"}'
                (root/'project.json').write_bytes(before);(root/'project.backup.json').write_bytes(backup)
                candidate='project.json.prepared.tmp';(root/candidate).write_bytes(has.json_bytes(scene))
                with patch.object(directory,'sync_files',side_effect=AssertionError('Payload sync must not run')):
                    with self.assertRaises(directory.HasError):directory.commit(root,candidate,has.sha(root/'project.json'),has.sha(root/candidate),True)
                self.assertEqual((root/'project.json').read_bytes(),before)
                self.assertEqual((root/'project.backup.json').read_bytes(),backup)

    def test_current_reader_admits_supported_capability_without_mutating_it(self):
        for version in (3,4,5):
            scene=basis.encode_capability(project(actor(),version));before=deepcopy(scene)
            self.assertIn('assets/'+DIGEST+'.glb',has.members(scene)[0])
            self.assertEqual(scene,before)
            with self.assertRaises(has.HasError):has._members_without_import_basis(scene)

    def test_missing_invalid_or_forged_readiness_fails_before_legacy_resource_gate(self):
        good=basis.encode_capability(project(actor()))
        invalid=[]
        for field in ('basis_content_schema_version','import_basis_capability'):
            row=deepcopy(good);row.pop(field);invalid.append(row)
        row=project(actor());row['runtime_basis_ready']=True;invalid.append(row)
        row=deepcopy(good);row['world']['objects'][0]['asset_basis']['factor']='1';invalid.append(row)
        with patch.object(has,'_members_without_import_basis',side_effect=AssertionError('Resource reader must not run')):
            for row in invalid:
                with self.subTest(row=row),self.assertRaises(has.HasError):has.members(row)

    def test_parent_cannot_lend_capability_to_child(self):
        wrapped=basis.encode_capability(sequences(project(),project(actor())))
        child=wrapped['sequence_graph']['assets'][0]['scene']
        child['schema_version']=child.pop('basis_content_schema_version');child.pop('import_basis_capability')
        with self.assertRaises(has.HasError):has.members(wrapped)
        self.assertEqual(timing.child_schema(child),4)  # Provisional writer shape only.
        good=basis.encode_capability(sequences(project(),project(actor())))
        self.assertEqual(timing.child_schema(good['sequence_graph']['assets'][0]['scene']),4)

    def test_timing_and_reference_wrappers_keep_original_metadata(self):
        child=project(actor());child['schema_version']=8;child['timing_content_schema_version']=4
        scene=sequences(project(),child)
        self.assertTrue(timing.required(scene))
        scene['schema_version']=7;scene['content_schema_version']=6
        scene['reference_sheet']=dict(format='studio_reference_sheet_1',name='reference.png',sha256='a'*64,path='references/'+'a'*64+'.png')
        scene['timing_content_schema_version']=7;scene['schema_version']=8
        scene['video']['duration_frames']=480
        wrapped=basis.encode_capability(scene);before=deepcopy(wrapped)
        assets,_=has.members(wrapped)
        self.assertIn('references/'+'a'*64+'.png',assets)
        self.assertEqual(wrapped,before)
        self.assertTrue(timing.required(wrapped))
        child=wrapped['sequence_graph']['assets'][0]['scene']
        child['import_basis_capability']='unsupported'
        self.assertEqual(timing.child_schema(child),-1)

    def test_resource_and_graph_limits_still_apply_after_capability_admission(self):
        scene=basis.encode_capability(project(actor()))
        scene['world']['objects'][0]['path']='assets/../foreign.glb'
        with self.assertRaises(has.HasError):has.members(scene)
        empty=project();empty['schema_version']=6;empty['sequence_graph']=dict(format='studio_sequences_1',assets=[],clips=[])
        with self.assertRaises(has.HasError):has.members(empty)
        wrapped=basis.encode_capability(sequences(project(actor()),project(actor(False))))
        wrapped['sequence_graph']['assets'][0]['scene']['world']['objects'][0]['id']='human'
        # Object identity is local, but the shared object budget remains64.
        wrapped['sequence_graph']['assets'][0]['scene']['world']['objects']=[dict(actor(False),id='v'+str(i)) for i in range(64)]
        with self.assertRaises(has.HasError):has.members(wrapped)

    def test_old_informational_import_height_does_not_create_active_basis(self):
        model=actor(False);model['metadata']['import_height']=dict(factor='0.01',target_metres='1.8288')
        scene=project(model);self.assertFalse(basis.inspect_capability(scene)['basis_required'])
        self.assertEqual(has.members(scene),has._members_without_import_basis(scene))
        self.assertEqual(basis.factor(model,capability=False),1)

    def test_packed_and_linked_roundtrip_keep_basis_and_original_manifest_bytes(self):
        for storage in ('packed','linked'):
            with self.subTest(storage=storage),tempfile.TemporaryDirectory() as d:
                root=Path(d);folder=root/'snapshot';(folder/'assets').mkdir(parents=True)
                original=root/'original.glb';original.write_bytes(b'synthetic storage-only asset')
                name='assets/'+DIGEST+'.glb';(folder/name).write_bytes(original.read_bytes())
                scene=basis.encode_capability(project(actor()));blob=has.json_bytes(scene);(folder/'project.json').write_bytes(blob)
                request=dict(folder=str(folder),path=str(root/'film.has'),storage=storage,references={name:str(original)},cache_root=str(root/'cache'))
                has.pack(request);out=has.unpack(dict(path=request['path'],folder=str(root/'opened')))
                self.assertTrue(out['ok']);self.assertEqual((Path(out['folder'])/'project.json').read_bytes(),blob)
                self.assertEqual(json.loads(blob)['world']['objects'][0]['asset_basis'],scene['world']['objects'][0]['asset_basis'])
                before=Path(request['path']).read_bytes();bad=deepcopy(scene);bad.pop('import_basis_capability')
                (folder/'project.json').write_bytes(has.json_bytes(bad))
                with self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)


if __name__=='__main__':unittest.main()
