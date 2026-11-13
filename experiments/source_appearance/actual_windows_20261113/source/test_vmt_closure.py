"""CPU-only parser/path/closure controls; retain synthetic artifacts."""
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest

sys.dont_write_bytecode = True
import vmt_closure as closure

ARTIFACTS = closure.stage.TASK / ("vmt-cpu-tests-" + str(time.time_ns()))
ARTIFACTS.mkdir(exist_ok=False)


class ClosureTests(unittest.TestCase):
    def build(self, files):
        folder = ARTIFACTS / self._testMethodName
        folder.mkdir(exist_ok=False)
        index = {}
        for member, raw in files.items():
            target = folder / member
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            index[member.casefold()] = {"member": member, "path": str(target), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        return index

    def test_real_style_adjacent_quotes_comments_and_backslashes(self):
        root = closure.parse('"VertexlitGeneric" { "$basetexture" "models\\touhou\\glove" "$color2""[0.9 0.9 0.9]" // ignored $bumpmap bad\n $phong 1 }')
        self.assertEqual(root["children"][0]["value"], r"models\touhou\glove")
        self.assertEqual(len(root["children"]), 3)

    def test_quotes_and_block_comments(self):
        root = closure.parse('shader { /* skip braces {} */ key "a//b" escaped "a\\\"b" }')
        self.assertEqual(root["children"][0]["value"], "a//b")
        self.assertEqual(root["children"][1]["value"], 'a"b')

    def test_malformed_text_refuses(self):
        for text in ['shader { key value', 'shader { key }', 'shader { key "unterminated }', 'shader {} }', 'shader {} shader2 {}', 'shader { /*unclosed', 'shader { key [unclosed', '\x00']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                closure.parse(text)

    def test_reference_canonicalization_and_runtime_resources(self):
        self.assertEqual(closure.reference(r'models\touhou\a', '.vtf'), 'materials/models/touhou/a.vtf')
        self.assertEqual(closure.reference('materials/a.vtf', '.vtf'), 'materials/a.vtf')
        self.assertIsNone(closure.reference('env_cubemap', '.vtf'))
        self.assertIsNone(closure.reference('_rt_test', '.vtf'))

    def test_unsafe_and_wrong_extension_reference_refuses(self):
        for value in ['../a', '/a', 'C:/a', 'a:stream', 'NUL', 'a.lua', 'a?.vtf', 'a//b']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                closure.reference(value, '.vtf')

    def test_present_base_and_missing_native_map_are_separate(self):
        index = self.build({'pkg/materials/a.vmt': b'shader { $basetexture "base" $bumpmap "missing" }', 'pkg/materials/base.vtf': b'fake'})
        result = closure.collect(['pkg/materials/a.vmt'], index)
        self.assertTrue(result['supported_bridge_base_inputs_complete'])
        self.assertFalse(result['native_observed_file_references_complete'])
        self.assertEqual(result['missing_native_references'][0]['reference'], 'materials/missing.vtf')

    def test_missing_base_rejects_supported_closure(self):
        index = self.build({'pkg/materials/a.vmt': b'shader { $basetexture "missing" }'})
        result = closure.collect(['pkg/materials/a.vmt'], index)
        self.assertFalse(result['supported_bridge_base_inputs_complete'])
        self.assertFalse(result['native_observed_file_references_complete'])

    def test_patch_include_union_stays_owned_and_case_insensitive(self):
        index = self.build({'pkg/materials/a.vmt': b'patch { include "B.vmt" replace { $basetexture "base" } }',
                            'pkg/materials/b.vmt': b'shader { $basetexture "base" }', 'pkg/materials/base.vtf': b'fake'})
        result = closure.collect(['pkg/materials/a.vmt'], index)
        self.assertEqual(len(result['vmts']), 2)
        self.assertTrue(result['native_observed_file_references_complete'])

    def test_include_cycle_prevents_complete_claim(self):
        index = self.build({'pkg/materials/a.vmt': b'patch { include "b.vmt" }', 'pkg/materials/b.vmt': b'patch { include "a.vmt" }'})
        result = closure.collect(['pkg/materials/a.vmt'], index)
        self.assertFalse(result['native_observed_file_references_complete'])
        self.assertEqual(result['diagnostics'][0]['kind'], 'include_cycle')

    def test_unknown_path_or_block_prevents_complete_claim(self):
        index = self.build({'pkg/materials/a.vmt': b'shader { $unrecognized "models/path" Proxies { value "a" } }'})
        result = closure.collect(['pkg/materials/a.vmt'], index)
        self.assertFalse(result['native_observed_file_references_complete'])
        self.assertEqual({row['kind'] for row in result['diagnostics']}, {'unclassified_path_value', 'unevaluated_block'})

    def test_conditional_branch_is_not_evaluated(self):
        index = self.build({'pkg/materials/a.vmt': b'shader { $basetexture "base" [$WIN32] }', 'pkg/materials/base.vtf': b'fake'})
        result = closure.collect(['pkg/materials/a.vmt'], index)
        self.assertFalse(result['native_observed_file_references_complete'])
        self.assertEqual(result['diagnostics'][0]['kind'], 'conditional_reference_union')

    def test_changed_vmt_after_manifest_refuses(self):
        index = self.build({'pkg/materials/a.vmt': b'shader { $basetexture "base" }'})
        Path(index['pkg/materials/a.vmt']['path']).write_bytes(b'shader {}')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            closure.collect(['pkg/materials/a.vmt'], index)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ClosureTests))
    report = {'format':'has_vmt_closure_cpu_safety_1','checks':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'artifact_folder':str(ARTIFACTS),'real_native_files_read':False,'blender_gpu_extraction_network':False}
    closure.stage.save(ARTIFACTS/'verification.json',report)
    print(json.dumps(report),flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
