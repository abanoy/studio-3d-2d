from pathlib import Path
import copy,hashlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from source_content import assets
from particle_browser import list_systems,execute
from asset_audit import AssetError
from test_source_particles import fixture

class Browser(unittest.TestCase):
    def test_particle_discovery_is_opt_in_and_data_only(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d)
            for name in ['models/test.mdl','maps/test.bsp','particles/test.pcf','particles/ignored.lua']:
                p=root/name;p.parent.mkdir(exist_ok=True);p.write_bytes(b'fixture')
            provider={'path':str(root),'label':'Authored'}
            self.assertEqual({r['kind']for r in assets(provider)['assets']},{'model','map'})
            found=assets(provider,True)['assets'];self.assertEqual(len(found),3);self.assertEqual(next(r for r in found if r['kind']=='particle')['path'],'particles/test.pcf')
    def test_named_whole_system_eligibility_and_source_identity(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);(root/'particles').mkdir();p=root/'particles/test.pcf';p.write_bytes(b'authored raw parser fixture')
            good=fixture();good['name']='Good';bad=copy.deepcopy(good);bad['name']='Parent';bad['groups']['children']=[{'function':'child','parameters':{}}]
            with patch('particle_browser.installed_context'),patch('particle_browser.decoder',return_value=(root,None)),patch('particle_browser.systems',return_value=[good,bad]):
                r=list_systems({'provider':str(root),'member':'particles/test.pcf'})
            self.assertTrue(r['ok']);self.assertEqual([s['candidate']for s in r['systems']],[True,False]);self.assertIn('children',r['systems'][1]['reason']);self.assertIn('material',r['systems'][0]['reason']);self.assertEqual(r['source_sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
    def test_empty_emission_and_unknown_native_operator_are_not_candidates(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);(root/'particles').mkdir();(root/'particles/test.pcf').write_bytes(b'fixture')
            empty=fixture();empty['groups']['emitters'][0]['parameters']['emission_start_time']=10
            unknown=fixture();unknown['groups']['operators']=[{'function':'future native behavior','parameters':{}}]
            with patch('particle_browser.installed_context'),patch('particle_browser.decoder',return_value=(root,None)),patch('particle_browser.systems',return_value=[empty,unknown]):
                r=list_systems({'provider':str(root),'member':'particles/test.pcf'})
            self.assertTrue(all(not s['candidate']for s in r['systems']));self.assertIn('No births',r['systems'][0]['reason'])
    def test_unknown_action_refuses(self):
        with self.assertRaises(AssetError):execute({'action':'run addon'})

if __name__=='__main__':unittest.main()
