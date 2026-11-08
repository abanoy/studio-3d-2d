from pathlib import Path
import sys, tempfile, unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from source_installation import installed_context, sfm_installation, conversion_context


class InstalledSource(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.steam = Path(self.tmp.name) / 'Steam'
        self.gmod = self.steam / 'steamapps/common/GarrysMod'
        self.sfm = self.steam / 'steamapps/common/SourceFilmmaker'
        patcher = patch('source_content.libraries', return_value=[str(self.steam)])
        patcher.start(); self.addCleanup(patcher.stop)
    def install_sfm(self, root=None):
        root = root or self.sfm
        (root / 'game/usermod').mkdir(parents=True)
        (root / 'game/usermod/gameinfo.txt').write_text('"GameInfo" { FileSystem { SteamAppId 1840 SearchPaths { Game usermod Game tf_movies } } }')
        (root / 'game/sfm.exe').write_bytes(b'presence fixture; never execute')
        source = root / 'game/tf_movies/models/scout.mdl'
        source.parent.mkdir(parents=True); source.write_bytes(b'IDST authored fixture')
        return source
    def context(self, source=None, extra=()):
        return installed_context(self.gmod, self.steam/'steamapps/workshop/content/4000', extra, source)
    def test_sfm_only_browse_and_native_source(self):
        source = self.install_sfm(); result = self.context(source)
        self.assertEqual(result['gmod_installation'], '')
        self.assertEqual(result['source_profile'], 'sfm')
        self.assertEqual(result['sfm_installations'], [str(self.sfm.resolve())])
        self.assertTrue(self.context()['discovery']['providers'])
        self.assertTrue(all(p['origin'] not in {'game','addon','workshop'} for p in result['discovery']['providers']))
    def test_sfm_workshop_without_gmod(self):
        self.install_sfm(); source=self.steam/'steamapps/workshop/content/1840/123/models/a.mdl'
        source.parent.mkdir(parents=True); source.write_bytes(b'fixture')
        self.assertEqual(self.context(source)['source_profile'], 'sfm')
    def test_installed_context_rejects_unrelated_location(self):
        self.install_sfm(); source=Path(self.tmp.name)/'arbitrary/models/a.mdl'
        source.parent.mkdir(parents=True);source.write_bytes(b'fixture')
        with self.assertRaisesRegex(ValueError, 'must already be installed'):self.context(source, [str(source.parents[1])])
    def test_gmod_workshop_still_requires_gmod(self):
        self.install_sfm(); source=self.steam/'steamapps/workshop/content/4000/123/pack.gma'
        source.parent.mkdir(parents=True);source.write_bytes(b'fixture')
        with self.assertRaisesRegex(ValueError, 'must already be installed'):self.context(source)
    def test_installed_browser_requires_host(self):
        with self.assertRaisesRegex(ValueError, 'Alternatively install Source Filmmaker'):self.context()
    def test_incomplete_or_wrong_sfm_marker_rejected(self):
        source=self.install_sfm(); exe=self.sfm/'game/sfm.exe';data=exe.read_bytes();exe.unlink()
        with self.assertRaises(ValueError):self.context(source)
        exe.write_bytes(data);(self.sfm/'game/usermod/gameinfo.txt').write_text('"GameInfo" { FileSystem { // SteamAppId 1840\n SteamAppId 440 } }')
        with self.assertRaises(ValueError):sfm_installation(self.sfm)
    def test_unvalidated_second_sfm_location_cannot_admit_assets(self):
        self.install_sfm(); other=Path(self.tmp.name)/'OtherSteam'
        source=self.install_sfm(other/'steamapps/common/SourceFilmmaker');(source.parents[2]/'sfm.exe').unlink()
        with patch('source_content.libraries', return_value=[str(self.steam),str(other)]):
            with self.assertRaisesRegex(ValueError, 'must already be installed'):self.context(source)
    def test_gmod_existing_preflight_still_works(self):
        (self.gmod/'garrysmod').mkdir(parents=True)
        (self.gmod/'garrysmod/gameinfo.txt').write_text('"GameInfo" { FileSystem { SteamAppId 4000 } }')
        (self.gmod/'garrysmod/garrysmod_dir.vpk').write_bytes(b'presence fixture')
        result=self.context(self.gmod/'garrysmod/models/test.mdl')
        self.assertEqual(result['gmod_installation'], str(self.gmod.resolve()))
        self.assertEqual(result['source_profile'], 'gmod')

class StandaloneSource(unittest.TestCase):
    setUp = InstalledSource.setUp
    install_sfm = InstalledSource.install_sfm
    def standalone(self):
        source=Path(self.tmp.name)/'own-model/models/character.mdl'
        source.parent.mkdir(parents=True);source.write_bytes(b'IDST own fixture')
        return source
    def convert(self, source, extra=()):
        return conversion_context(self.gmod,self.steam/'steamapps/workshop/content/4000',extra,source)
    def test_standalone_without_either_host(self):
        source=self.standalone();r=self.convert(source,[str(source.parents[1])])
        self.assertEqual(r['source_profile'],'standalone');self.assertEqual(r['gmod_installation'],'')
        self.assertEqual(r['sfm_installations'],[])
        self.assertTrue(any(p['origin']=='manual' for p in r['discovery']['providers']))
        self.assertFalse(any(p['origin'] in {'game','addon','workshop'} for p in r['discovery']['providers']))
    def test_broken_optional_game_config_does_not_reject_own_asset(self):
        config=self.gmod/'garrysmod/cfg/mount.cfg';config.parent.mkdir(parents=True)
        config.write_text('"mountcfg" { broken')
        source=self.standalone();r=self.convert(source,[str(source.parents[1])])
        self.assertEqual(r['source_profile'],'standalone')
        self.assertTrue(r['discovery']['warnings'])
        self.assertTrue(all(p['origin']=='manual' for p in r['discovery']['providers']))
    def test_standalone_with_optional_sfm(self):
        self.install_sfm();r=self.convert(self.standalone())
        self.assertEqual(r['source_profile'],'standalone');self.assertEqual(r['sfm_installations'],[str(self.sfm.resolve())])
    def test_direct_file_in_former_workshop_does_not_need_host(self):
        source=self.steam/'steamapps/workshop/content/4000/123/models/a.mdl'
        source.parent.mkdir(parents=True);source.write_bytes(b'fixture')
        self.assertEqual(self.convert(source)['source_profile'],'standalone')
    def test_direct_sfm_file_keeps_working_if_installation_is_removed(self):
        source=self.install_sfm();self.assertEqual(self.convert(source)['source_profile'],'sfm')
        (self.sfm/'game/sfm.exe').unlink()
        result=self.convert(source);self.assertEqual(result['source_profile'],'standalone');self.assertEqual(result['sfm_installations'],[])

if __name__ == '__main__':unittest.main()
