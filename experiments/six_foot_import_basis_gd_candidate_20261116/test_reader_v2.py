"""Execute fail-closed copied worker reader; internal ready paths remain tests only."""
from copy import deepcopy
import ast
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from test_python_v2 import model,normalized,project,sequences,add_timing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
old=importlib.import_module('tools.has_project')


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


basis=load('tools.import_basis',HERE/'draft/tools/import_basis.py')
draft=load('tools._six_foot_v2_reader',HERE/'draft/tools/has_project.py')


class ReaderV2(unittest.TestCase):
    def test_legacy_worker_inventory_is_exact(self):
        for scene in [project(model(),3),project(model()),project(model(),5),add_timing(project(model()))]:
            self.assertEqual(draft.members(scene),old.members(scene))

    def test_active_worker_refuses_before_old_resource_reader(self):
        wrapped=basis.encode_capability(project(normalized()))
        with patch.object(draft,'_members_without_import_basis',side_effect=AssertionError('Must not reach old body')):
            with self.assertRaises(basis.BasisError):draft.members(wrapped)

    def test_ungated_legacy_basis_also_refuses(self):
        scene=project(normalized());self.assertTrue(old.members(scene)[0])
        with self.assertRaises(basis.BasisError):draft.members(scene)

    def test_internal_contract_only_ready_path_preserves_timing_recursion(self):
        wrapped=basis.encode_capability(add_timing(project(normalized())))
        self.assertEqual(basis.members_with_capability(wrapped,draft._members_without_import_basis,runtime_basis_ready=True),old.members(add_timing(project(model()))))

    def test_internal_contract_only_ready_path_preserves_child_recursion(self):
        wrapped=basis.encode_capability(sequences(project(),[project(normalized())]))
        expected=old.members(sequences(project(),[project(model())]))
        self.assertEqual(basis.members_with_capability(wrapped,draft._members_without_import_basis,runtime_basis_ready=True),expected)

    def test_resource_path_gate_remains_under_internal_ready_path(self):
        row=normalized();row['path']='assets/../wrong.glb';wrapped=basis.encode_capability(project(row))
        with self.assertRaises(draft.HasError):basis.members_with_capability(wrapped,draft._members_without_import_basis,runtime_basis_ready=True)

    def test_parent_cannot_lend_permission_to_child(self):
        wrapped=basis.encode_capability(sequences(project(),[project(normalized())]))
        child=wrapped['sequence_graph']['assets'][0]['scene'];child['schema_version']=child.pop('basis_content_schema_version');child.pop('import_basis_capability')
        with self.assertRaises(basis.BasisError):basis.members_with_capability(wrapped,draft._members_without_import_basis,runtime_basis_ready=True)

    def test_prior_original_ast_is_still_exact(self):
        original=ast.parse((ROOT/'tools/has_project.py').read_text(encoding='utf-8'))
        proposed=ast.parse((HERE/'draft/tools/has_project.py').read_text(encoding='utf-8'))
        proposed.body=[n for n in proposed.body if not (isinstance(n,ast.Try)and'import_basis'in ast.dump(n)or isinstance(n,ast.FunctionDef)and n.name=='members')]
        class Restore(ast.NodeTransformer):
            def visit_FunctionDef(self,n):
                if n.name=='_members_without_import_basis':n.name='members'
                return self.generic_visit(n)
            def visit_Name(self,n):
                if n.id=='_members_without_import_basis':n.id='members'
                return n
        self.assertEqual(ast.dump(Restore().visit(proposed),include_attributes=False),ast.dump(original,include_attributes=False))

    def test_source_and_basis_remain_exact_after_refusal(self):
        wrapped=basis.encode_capability(project(normalized()));before=deepcopy(wrapped)
        with self.assertRaises(basis.BasisError):draft.members(wrapped)
        self.assertEqual(wrapped,before)


def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReaderV2);names=[x.id().split('.')[-1]for x in suite]
    result=unittest.TestResult();suite.run(result)
    report={'format':'has_six_foot_v2_reader_cpu_1','passed':result.wasSuccessful(),'test_methods':result.testsRun,
        'named_tests':names,'failures':[{'test':str(t),'error':e}for t,e in result.failures],
        'errors':[{'test':str(t),'error':e}for t,e in result.errors],'default_worker_active_basis_admission':False,
        'internal_ready_positive_paths':'Synthetic contract-only explicit boolean, never a worker request switch',
        'model_or_media_file_io':0,'engines_CIM_Git_network':0}
    with(HERE/'READER_V2_CPU_RESULT.json').open('x',encoding='utf-8')as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in report.items()if k not in('named_tests','failures','errors')}))
    for t,e in result.failures+result.errors:print(str(t)+'\n'+e)
    return 0 if result.wasSuccessful()else 1


if __name__=='__main__':raise SystemExit(main())
