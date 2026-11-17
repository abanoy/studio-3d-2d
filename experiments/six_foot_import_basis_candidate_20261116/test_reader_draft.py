"""Execute isolated reader facade with synthetic metadata and unchanged gates."""
from copy import deepcopy
import ast
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from test_import_basis_candidate import model,normalized,project,sequences,add_timing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
old=importlib.import_module('tools.has_project')


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


basis=load('tools.import_basis',HERE/'draft/tools/import_basis.py')
draft=load('tools._six_foot_reader_candidate',HERE/'draft/tools/has_project.py')


class ReaderDraft(unittest.TestCase):
    def test_all_original_python_ast_is_preserved_after_exact_facade_recipe(self):
        original=ast.parse((ROOT/'tools/has_project.py').read_text(encoding='utf-8'))
        proposed=ast.parse((HERE/'draft/tools/has_project.py').read_text(encoding='utf-8'))
        proposed.body=[node for node in proposed.body if not (
            isinstance(node,ast.Try)and 'import_basis'in ast.dump(node) or
            isinstance(node,ast.FunctionDef)and node.name=='members')]
        class Restore(ast.NodeTransformer):
            def visit_FunctionDef(self,node):
                if node.name=='_members_without_import_basis':node.name='members'
                return self.generic_visit(node)
            def visit_Name(self,node):
                if node.id=='_members_without_import_basis':node.id='members'
                return node
        restored=Restore().visit(proposed)
        self.assertEqual(ast.dump(restored,include_attributes=False),ast.dump(original,include_attributes=False))

    def test_legacy_metadata_resource_inventory_matches_original(self):
        for scene in [project(model(),3),project(model()),project(model(),5),add_timing(project(model()))]:
            self.assertEqual(draft.members(scene),old.members(scene))

    def test_active_capability_resource_inventory_matches_original_asset(self):
        scene=basis.encode_capability(project(normalized()));before=deepcopy(scene)
        self.assertEqual(draft.members(scene),old.members(project(model())))
        self.assertEqual(scene,before)

    def test_timing_recursion_remains_inside_private_unchanged_body(self):
        scene=add_timing(project(normalized()));wrapped=basis.encode_capability(scene)
        plain=add_timing(project(model()))
        self.assertEqual(draft.members(wrapped),old.members(plain))

    def test_nested_child_and_parent_capabilities_inventory_same_native_asset(self):
        wrapped=basis.encode_capability(sequences(project(),[project(normalized())]))
        legacy=sequences(project(),[project(model())])
        self.assertEqual(draft.members(wrapped),old.members(legacy))
        child=wrapped['sequence_graph']['assets'][0]['scene']
        self.assertEqual(child['schema_version'],9)

    def test_missing_capability_is_rejected_even_when_old_reader_ignores_it(self):
        scene=project(normalized())
        self.assertTrue(old.members(scene)[0])
        with self.assertRaises(basis.BasisError):draft.members(scene)

    def test_resource_path_and_duplicate_identity_gates_remain(self):
        bad=project(normalized());bad['world']['objects'][0]['path']='assets/../bad.glb'
        with self.assertRaises(draft.HasError):draft.members(basis.encode_capability(bad))
        bad=project(normalized());bad['world']['objects'].append(deepcopy(bad['world']['objects'][0]))
        with self.assertRaises(draft.HasError):draft.members(basis.encode_capability(bad))

    def test_invalid_sequence_duration_stays_refused_by_old_gate(self):
        bad=sequences(project(),[add_timing(project(normalized()))])
        with self.assertRaises(draft.HasError):draft.members(basis.encode_capability(bad))

    def test_derivative_and_unknown_basis_data_refuse_before_resource_resolution(self):
        scene=basis.encode_capability(project(normalized()))
        for field,value in [('sha256','a'*64),('asset_basis',{'format':'future_unknown'})]:
            bad=deepcopy(scene);bad['world']['objects'][0][field]=value
            with self.assertRaises(basis.BasisError):draft.members(bad)

    def test_json_round_trip_keeps_factor_artist_scale_and_source_identity(self):
        scene=basis.encode_capability(project(normalized()));before=deepcopy(scene)
        for _ in range(10):
            scene=json.loads(json.dumps(scene));draft.members(scene)
        self.assertEqual(scene,before)


def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReaderDraft)
    names=[case.id().split('.')[-1]for case in suite]
    result=unittest.TestResult();suite.run(result)
    report={'format':'has_basis_reader_draft_cpu_1','passed':result.wasSuccessful(),
        'test_methods':result.testsRun,'named_tests':names,
        'failures':[{'test':str(t),'error':e}for t,e in result.failures],
        'errors':[{'test':str(t),'error':e}for t,e in result.errors],
        'actual_original_reader_used_on_synthetic_metadata':True,
        'actual_isolated_successor_reader_used_on_synthetic_metadata':True,
        'file_unpack_model_geometry_or_engine_runs':0,'main_changes':False}
    with(HERE/'READER_CPU_RESULT.json').open('x',encoding='utf-8')as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in report.items()if k not in('named_tests','failures','errors')}))
    for t,e in result.failures+result.errors:print(str(t)+'\n'+e)
    return 0 if result.wasSuccessful()else 1


if __name__=='__main__':raise SystemExit(main())
