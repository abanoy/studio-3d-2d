from pathlib import Path
import sys,tempfile,unittest,zipfile
from tools.blender_addon_runtime import add_bundled_wheels

class WheelRuntimeTests(unittest.TestCase):
    def fixture(self,root,members):
        addon=root/'addon';addon.mkdir();(addon/'blender_manifest.toml').write_text('wheels=["data-1-py3-none-any.whl"]')
        with zipfile.ZipFile(addon/'data-1-py3-none-any.whl','w') as z:
            for name,data in members:z.writestr(name,data)
        return addon
    def test_real_files_are_available_to_filesystem_based_packages(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);addon=self.fixture(root,[('native_dep/__init__.py',''),('native_dep/dict/data.txt','original')]);old=sys.path[:]
            try:
                report=add_bundled_wheels(addon,root/'job');self.assertEqual(len(report),1);self.assertEqual((Path(sys.path[0])/'native_dep/dict/data.txt').read_text(),'original')
            finally:sys.path[:]=old
    def test_archive_escape_and_duplicate_paths_are_refused(self):
        for names in [['../escape'],['/absolute'],['C:/absolute'],['package\\escape'],['package/./escape'],['package//escape'],['same','SAME']]:
            with self.subTest(names=names),tempfile.TemporaryDirectory() as d:
                root=Path(d);addon=self.fixture(root,[(x,'x') for x in names])
                with self.assertRaises(ValueError):add_bundled_wheels(addon,root/'job')
                self.assertFalse((root/'escape').exists())
    def test_external_dependency_declaration_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);addon=self.fixture(root,[]);(addon/'blender_manifest.toml').write_text('wheels=["../outside.whl"]');(root/'outside.whl').write_bytes(b'x')
            with self.assertRaises(ValueError):add_bundled_wheels(addon,root/'job')
    def test_addon_without_wheels_needs_no_staging(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);addon=root/'addon';addon.mkdir();(addon/'blender_manifest.toml').write_text('id="mmd_tools"')
            self.assertEqual(add_bundled_wheels(addon,root/'job'),[]);self.assertFalse((root/'job').exists())
if __name__=='__main__':unittest.main()
