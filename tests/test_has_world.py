"""Schema4 inventory/ZIP tests. Opaque payloads here do not prove GLB decoding."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import has_project as has


class WorldContainerTests(unittest.TestCase):
    def fixture(self,root):
        snapshot=root/'snapshot';(snapshot/'assets').mkdir(parents=True)
        sources=[]
        for i in range(2):
            path=root/f'original {i}.glb';path.write_bytes((f'opaque inventory fixture {i}'*100).encode())
            digest=has.sha(path);name=f'assets/{digest}.glb';(snapshot/name).write_bytes(path.read_bytes())
            sources.append((path,name,digest))
        rows=[]
        for i,kind in enumerate(['group','environment','model','model']):
            path,name,digest=sources[i%2]
            rows.append({'id':f'object-{i}','kind':kind,'parent_id':'' if i==0 else 'object-0',
                         'start_frame':0 if i!=3 else 24,'path':name,'sha256':digest,
                         'pose_keys':[{'frame':0,'fixture_value':i}], 'metadata':{'native_unknown':i}})
        manifest={'schema_version':4,'video':{'duration_frames':48},'world':{'format':'studio_world_1','objects':rows},'audio':{},'layers':[{'cels':[]}]}
        (snapshot/'project.json').write_bytes(has.json_bytes(manifest))
        request={'folder':str(snapshot),'path':str(root/'world.has'),'storage':'packed',
                 'references':{name:str(path) for path,name,_ in sources},'cache_root':str(root/'cache')}
        return request,manifest,sources

    def write(self,request,manifest):
        (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest))

    def test_packed_world_roundtrip_preserves_instances_and_shared_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,sources=self.fixture(root);has.pack(request)
            with zipfile.ZipFile(request['path']) as archive:
                header=json.loads(archive.read('has.json'));self.assertEqual(len(header['assets']),2)
                self.assertEqual(json.loads(archive.read('project.json')),manifest)
            for path,_,_ in sources:path.unlink()
            result=has.unpack({'path':request['path'],'folder':str(root/'opened')})
            self.assertTrue(result['ok']);self.assertEqual(json.loads((root/'opened/project.json').read_bytes()),manifest)

    def test_linked_shared_asset_relinks_once_for_all_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,sources=self.fixture(root);request['storage']='linked';has.pack(request)
            original,name,_=sources[0];moved=root/'moved.glb';original.rename(moved)
            read={'path':request['path'],'folder':str(root/'opened')}
            missing=has.unpack(read);self.assertEqual(len(missing['missing']),1)
            result=has.unpack({**read,'relinks':{name:str(moved)}})
            self.assertTrue(result['ok']);self.assertEqual(len(result['origins']),2)
            self.assertEqual(json.loads((root/'opened/project.json').read_bytes()),manifest)

    def test_empty_world_needs_only_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_=self.fixture(root);manifest['world']['objects']=[]
            self.write(request,manifest);has.pack(request)
            with zipfile.ZipFile(request['path']) as archive:self.assertEqual(set(archive.namelist()),{'has.json','project.json'})
            self.assertTrue(has.unpack({'path':request['path'],'folder':str(root/'opened')})['ok'])

    def test_invalid_parent_graph_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            _,manifest,_=self.fixture(Path(directory))
            for kind in ['self','cycle','missing','duplicate','bad_id']:
                bad=copy.deepcopy(manifest);rows=bad['world']['objects']
                if kind=='self':rows[0]['parent_id']=rows[0]['id']
                if kind=='cycle':rows[0]['parent_id']=rows[1]['id']
                if kind=='missing':rows[0]['parent_id']='missing'
                if kind=='duplicate':rows[1]['id']=rows[0]['id']
                if kind=='bad_id':rows[0]['id']='../bad'
                with self.subTest(kind=kind),self.assertRaises(has.HasError):has.members(bad)

    def test_presence_and_world_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            _,manifest,_=self.fixture(Path(directory))
            for start in [-1,49,1.5,True,float('inf'),float('nan'),10**1000]:
                bad=copy.deepcopy(manifest);bad['world']['objects'][0]['start_frame']=start
                with self.subTest(start=str(start)[:30]),self.assertRaises(has.HasError):has.members(bad)
            bad=copy.deepcopy(manifest);bad['world']['objects']*=17
            with self.assertRaises(has.HasError):has.members(bad)
            bad=copy.deepcopy(manifest);bad['video']['duration_frames']=10**1000
            with self.assertRaises(has.HasError):has.members(bad)

    def test_ambiguous_slots_unknown_versions_and_unsafe_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            _,manifest,_=self.fixture(Path(directory))
            for kind in ['slot','schema','format','path','source','checksum']:
                bad=copy.deepcopy(manifest);row=bad['world']['objects'][0]
                if kind=='slot':bad['model']={}
                if kind=='schema':bad['schema_version']=5
                if kind=='format':bad['world']['format']='unknown'
                if kind=='path':row['path']='../outside.glb'
                if kind=='source':row['source']='C:/outside.glb'
                if kind=='checksum':row['sha256']='z'*64;row['path']='assets/'+row['sha256']+'.glb'
                with self.subTest(kind=kind),self.assertRaises(has.HasError):has.members(bad)

    def test_failed_world_save_preserves_complete_container(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_=self.fixture(root);has.pack(request)
            before=Path(request['path']).read_bytes();manifest['world']['objects'][0]['parent_id']='missing'
            self.write(request,manifest)
            with self.assertRaises(has.HasError):has.pack(request)
            self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_changed_shared_asset_fails_before_replacing_container(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,sources=self.fixture(root);has.pack(request)
            before=Path(request['path']).read_bytes();(Path(request['folder'])/sources[0][1]).write_bytes(b'changed')
            with self.assertRaises(has.HasError):has.pack(request)
            self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_corrupt_current_world_keeps_previous_good_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_=self.fixture(root);has.pack(request);has.pack(request)
            backup=Path(request['path']+'.backup');before=backup.read_bytes()
            with zipfile.ZipFile(request['path']) as archive:entries={name:archive.read(name) for name in archive.namelist()}
            broken=copy.deepcopy(manifest);broken['world']['objects'][0]['parent_id']='missing'
            entries['project.json']=has.json_bytes(broken)
            header=json.loads(entries['has.json'])
            for row in header['payload']:
                if row['path']=='project.json':
                    import hashlib
                    row['sha256']=hashlib.sha256(entries['project.json']).hexdigest();row['bytes']=len(entries['project.json'])
            entries['has.json']=has.json_bytes(header)
            with zipfile.ZipFile(request['path'],'w') as archive:
                for name,data in entries.items():archive.writestr(name,data)
            has.pack(request)
            self.assertEqual(backup.read_bytes(),before)


if __name__=='__main__':unittest.main()
