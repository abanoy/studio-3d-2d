from pathlib import Path
import base64
import json
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import generic_assets as assets


class GenericTests(unittest.TestCase):
    def gltf(self,root,uri):
        source=root/'test.gltf';source.write_text(json.dumps({'asset':{'version':'2.0'},'buffers':[{'uri':uri,'byteLength':4}]}));return source

    def test_gltf_percent_encoded_dependencies(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'buffer data.bin').write_bytes(b'data');source=self.gltf(root,'buffer%20data.bin')
            self.assertEqual(len(assets.dependencies(source,root)),2)

    def test_gltf_data_uri(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=self.gltf(root,'data:application/octet-stream;base64,'+base64.b64encode(b'data').decode())
            self.assertEqual(len(assets.dependencies(source,root)),1)

    def test_gltf_url_and_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for uri in ('https://host/a.bin','//server/a.bin','../outside.bin','%2foutside.bin','file:///C:/a.bin','buffer.bin?x=1'):
                with self.assertRaises(ValueError):assets.dependencies(self.gltf(root,uri),root)

    def test_wider_explicit_asset_root(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);sub=root/'models';sub.mkdir();(root/'buffer.bin').write_bytes(b'data');source=self.gltf(sub,'../buffer.bin')
            with self.assertRaises(ValueError):assets.dependencies(source,sub)
            self.assertEqual(len(assets.dependencies(source,root)),2)

    def test_missing_buffer(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaisesRegex(ValueError,'Missing dependency'):assets.dependencies(self.gltf(root,'missing.bin'),root)

    def test_obj_mtl_map_options_and_spaces(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'color image.png').write_bytes(b'PNG');(root/'my material.mtl').write_text('newmtl a\nmap_Kd -s 1 2 1 color image.png\n')
            source=root/'mesh.obj';source.write_text('mtllib "my material.mtl"\nv 0 0 0\n')
            result=assets.dependencies(source,root)
            self.assertEqual(len(result),3);self.assertTrue(all('sha256' in r for r in result))

    def test_obj_missing_or_unsafe_material(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'test.obj'
            for name in ('missing.mtl','../outside.mtl','C:/outside.mtl'):
                source.write_text('mtllib '+name)
                with self.assertRaises(ValueError):assets.dependencies(source,root)

    def test_size_and_root_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=self.gltf(root,'missing.bin')
            with patch.object(assets,'MAX_FILE',1):
                with self.assertRaises(ValueError):assets.dependencies(source,root)
            other=root/'other';other.mkdir()
            with self.assertRaises(ValueError):assets.dependencies(source,other)

    def test_ascii_fbx_rejected_before_staging_or_blender(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'ascii.fbx';source.write_text('; FBX ASCII 7.4')
            output=root/'prepared';status=root/'status.json'
            script=Path(__file__).resolve().parents[1]/'tools/prepare_generic.py'
            result=subprocess.run([sys.executable,str(script),str(source),'--output',str(output),'--status-file',str(status),'--blender',str(root/'nonexistent-blender.exe')],capture_output=True)
            self.assertEqual(result.returncode,1);self.assertIn('binary FBX',json.loads(status.read_text())['error']);self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
