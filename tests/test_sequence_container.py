"""Container integrity and preservation; GPU/decoded media have separate tests."""
from pathlib import Path
import copy,json,sys,tempfile,unittest,zipfile
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tools'),str(Path(__file__).parent)]
import has_project as has
import test_has_project as fixtures
from test_sequence_graph import good,scene


class SequenceContainerTests(unittest.TestCase):
    def fixture(self,root):
        request,legacy,wave_name,wave=fixtures.HasTests().audio_fixture(root)
        folder=Path(request['folder']);model=legacy['scene']
        child=scene();child['world']['objects']=[dict(id='rig',name='Rig',kind='model',parent_id='',start_frame=0,**model)]
        child['layers']=legacy['layers'];child['audio']=legacy['audio']
        root_doc=scene();root_doc['schema_version']=6;root_doc['sequence_graph']=good();root_doc['sequence_graph']['assets'][0]['scene']=child
        (folder/'project.json').write_bytes(has.json_bytes(root_doc))
        return request,root_doc,wave_name,wave

    def test_packed_and_linked_keep_child_tracks_and_all_assets(self):
        for mode in ['packed','linked']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);request,manifest,wave_name,wave=self.fixture(root);request['storage']=mode
                has.pack(request)
                with zipfile.ZipFile(request['path']) as z:
                    self.assertIn('cels/test.png',z.namelist())
                    self.assertEqual(json.loads(z.read('project.json'))['sequence_graph'],manifest['sequence_graph'])
                    self.assertEqual(wave_name in z.namelist(),mode=='packed')
                result=fixtures.HasTests().unpack(root,request)
                self.assertTrue(result['ok']);opened=Path(result['folder'])
                self.assertEqual(json.loads((opened/'project.json').read_bytes()),manifest)
                self.assertEqual((opened/wave_name).read_bytes(),wave.read_bytes())

    def test_nested_missing_link_reports_and_preserves_current_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,_,name,wave=self.fixture(root);request['storage']='linked';has.pack(request);wave.unlink()
            result=fixtures.HasTests().unpack(root,request)
            self.assertFalse(result['ok']);self.assertIn(name,[x['asset'] for x in result['missing']]);self.assertFalse((root/'opened').exists())

    def test_cycle_and_child_path_escape_preserve_prior_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_,_=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            for kind in ['cycle','path','downgrade','invalid-context']:
                bad=copy.deepcopy(manifest)
                if kind=='cycle':
                    clip=copy.deepcopy(bad['sequence_graph']['clips'][0]);clip['id']='cycle';bad['sequence_graph']['assets'][0]['clips']=[clip]
                elif kind=='path':bad['sequence_graph']['assets'][0]['scene']['layers'][0]['cels'][0]['path']='../outside.png'
                elif kind=='downgrade':bad['schema_version']=4
                else:bad['editor']={'sequence_editor':dict(format='studio_sequence_editor_1',asset_id='missing',frame=0)}
                (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(bad))
                with self.subTest(kind=kind),self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_shared_source_is_embedded_once_and_keeps_reference_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_,_=self.fixture(root)
            duplicate=copy.deepcopy(manifest['sequence_graph']['assets'][0]);duplicate['id']='other';duplicate['name']='Other'
            for row in duplicate['scene']['audio']['clips']:row['id']='other-'+row['id']
            manifest['sequence_graph']['assets'].append(duplicate)
            (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest));has.pack(request)
            with zipfile.ZipFile(request['path']) as z:
                names=z.namelist();self.assertEqual(len(names),len(set(names)))
                self.assertEqual(len([n for n in names if n.endswith('.wav')]),1)
                self.assertEqual(len([n for n in names if n.endswith('.glb')]),1)


if __name__=='__main__':unittest.main()
