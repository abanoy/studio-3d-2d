"""Synthetic fifth-case negatives; original twenty test methods are copied unchanged."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import re
import unittest

import test_verify_neon_workspace as Original

W=Original.W
HERE=Path(__file__).resolve().parents[1]
CASE_NAMES=['theme-detach-reentry-reparent-free','queued-owner','immediate-free-resize']


def report():
    return {'format':'has_neon_world_rail_lifecycle_1','checks':29,'failures':0,'cases':CASE_NAMES.copy(),'source_only_fixture_uses_native_models':False}


def marker(value):return W.MARKERS['lifecycle']+json.dumps(value)


class LifecycleIntegration(unittest.TestCase):
    def test_complete_lifecycle_report_passes(self):
        value=report();W.validate_report('lifecycle',value,marker(value))

    def test_original_four_rows_limits_and_full_aggregate(self):
        self.assertEqual(W.CASES[:4],(('inset','tests/neon_inset_scene_regression.gd',True,12384,90),('behavior','tests/neon_behavior_regression.gd',False,32,150),('compact','tests/neon_compact_timeline_reveal_smoke.gd',False,14,150),('rail','tests/neon_rail_placement_smoke.gd',False,45,150)))
        self.assertEqual(W.CASES[4],('lifecycle','tests/neon_world_rail_lifecycle.gd',False,29,130))
        self.assertEqual(len(W.CASES),5);self.assertEqual(sum(row[3] for row in W.CASES),12504)

    def test_format_count_failures_types_and_native_scope_refused(self):
        for key,value in [('format','wrong'),('checks',28),('checks',29.0),('checks',True),('failures',1),('failures',False),('source_only_fixture_uses_native_models',True),('source_only_fixture_uses_native_models',0),('cases',CASE_NAMES[:-1]),('cases',CASE_NAMES[::-1]),('cases',True)]:
            changed=report();changed[key]=value
            with self.subTest(key=key,value=value):
                with self.assertRaises(ValueError):W.validate_report('lifecycle',changed,marker(changed))

    def test_missing_or_extra_scope_field_refused(self):
        for mutate in (lambda v:v.pop('source_only_fixture_uses_native_models'),lambda v:v.update(native_payload=[1,2,3])):
            value=report();mutate(value)
            with self.assertRaises(ValueError):W.validate_report('lifecycle',value,marker(value))

    def test_marker_missing_duplicate_or_wrong_report_refused(self):
        value=report()
        for log in ('',marker(value)+'\n'+marker(value),W.MARKERS['lifecycle']+'{}'):
            with self.assertRaises(ValueError):W.validate_report('lifecycle',value,log)

    def test_marker_boolean_integer_and_float_aliases_refused(self):
        value=report()
        for key,alias in [('checks',29.0),('failures',False),('source_only_fixture_uses_native_models',0)]:
            emitted=copy.deepcopy(value);emitted[key]=alias
            self.assertEqual(value,emitted)  # Demonstrate the Python-equality trap actually applies.
            with self.assertRaises(ValueError):W.validate_report('lifecycle',value,marker(emitted))

    def test_all_original_engine_error_markers_still_fail_lifecycle(self):
        value=report()
        for bad in W.BAD_LOG:
            with self.subTest(marker=bad):
                with self.assertRaises(ValueError):W.validate_report('lifecycle',value,marker(value)+'\n'+bad)

    def test_original_twenty_test_methods_are_byte_exact(self):
        original=(HERE/'cpu_tests/test_verify_neon_workspace.py').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),'f8901be8720a73a7dfebff01fa38d22e163bd7d59b104e3871238dcda69e3cfd')

    def test_aggregate_deadline_covers_all_sequential_bounds(self):
        tree=ast.parse((HERE/'tests/verify.py').read_bytes())
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='run' and node.args and isinstance(node.args[0],ast.List) and any(isinstance(value,ast.Constant) and value.value=='tests/verify_neon_workspace.py' for value in node.args[0].elts)]
        self.assertEqual(len(calls),1)
        deadline=next(node.value.value for node in calls[0].keywords if node.arg=='timeout')
        self.assertEqual(deadline,1200)
        self.assertEqual(sum(row[4]+20+75 for row in W.CASES),1145)
        self.assertGreater(deadline,1145)

    def test_full_precision_marker_mismatch_is_still_refused(self):
        value=Original.report('inset');value['maximum_projection_error_pixels']=0.0007905710372142494
        emitted=copy.deepcopy(value);emitted['maximum_projection_error_pixels']=0.000790571037214249
        self.assertNotEqual(value,emitted)
        W.validate_report('inset',value,Original.log('inset',value))
        with self.assertRaises(ValueError):W.validate_report('inset',value,Original.log('inset',emitted))

    def test_inset_compact_transport_reuses_one_encoding_and_old_oracles(self):
        review=HERE.parents[1].parent/'has-neon-review-20261116-c2d52ff'
        for name,variable,marker_name in [('neon_inset_scene_regression.gd','report','INSET_SCENE_REGRESSION'),('neon_compact_timeline_reveal_smoke.gd','result','COMPACT_TIMELINE_REVEAL')]:
            proposed=(HERE/'tests'/name).read_text()
            before=(review/'tests'/name).read_text()
            self.assertEqual(proposed.count('var encoded := JSON.stringify('+variable+',"",true,true)'),1)
            self.assertEqual(proposed.count('store_string(encoded)'),1)
            self.assertEqual(proposed.count('print("'+marker_name+' " + encoded)'),1)
            checks=lambda text:[line for line in text.splitlines() if re.search(r'\bcheck\(',line)]
            self.assertEqual(checks(before),checks(proposed))

    def test_lifecycle_typing_successor_changes_only_six_annotations(self):
        typed=(HERE/'tests/neon_world_rail_lifecycle.gd').read_bytes()
        self.assertEqual(hashlib.sha256(typed).hexdigest(),'f033f975735efe5089dbadb478661f620dceeca4a1328ce090638747c03df202')
        self.assertEqual(typed.count(b': WeakRef=weakref('),6)
        restored=typed.replace(b': WeakRef=weakref(',b':=weakref(')
        self.assertEqual(hashlib.sha256(restored).hexdigest(),'f43e60a6e1c6a6c23b7f3bef0efe43fc1849e24e0f093b1b8fb6628e5474770f')


if __name__=='__main__':unittest.main()
