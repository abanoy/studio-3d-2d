"""CPU/source and authored synthetic metadata only; no real native/private IO."""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
import types
import unittest
import baseline_predicate as B
import current_context as C
import known_handler_policy as H
import source_successor as D

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent


def descriptor():
    return {'capture': {'path': 'C:/SYNTHETIC/output/private-capture.json', 'bytes': H.CAPTURE_BYTES,
                        'mtime_ns': 1, 'sha256': H.CAPTURE_SHA256},
            'public_sources': {role: {'path': 'C:/SYNTHETIC/scripts/' + H.PUBLIC_RELATIVE[role],
                                     'mtime_ns': 1, **value} for role, value in B.SOURCES.items()}}


def authority():
    now = datetime.datetime(2026, 11, 17, 20, 0, tzinfo=datetime.timezone.utc)
    value = json.loads((HERE / 'ADMISSION.template.json').read_bytes())
    value.update(root_native_lane_exclusive=True, expected_metadata_head='a' * 40,
                 candidate_commit=C.EXPECTED_REVIEW_COMMIT, cold187_disposition='NOT_STARTED_CURRENT_CONTEXT',
                 issued_utc=now.isoformat(), expires_utc=(now + datetime.timedelta(minutes=5)).isoformat())
    for number, row in enumerate(value['proofs'].values()):
        row.update(path='C:/SYNTHETIC/output/proof.json', bytes=1, mtime_ns=1, sha256=str(number + 1) * 64)
    value['factory_baseline'] = descriptor()
    record = {'format': 'has_root_known_factory_resource_current_closed_lane_1',
              'observed_utc': (now - datetime.timedelta(seconds=5)).isoformat(),
              **{key: True for key in ('root_native_lane_exclusive', 'ui_lane_closed', 'all_owned_jobs_desktops_closed', 'source_unchanged')},
              **{key: False for key in ('current_full_run_active', 'current_targeted_run_active', 'cold187_launched', 'termination_issued', 'full_suite_pass_claimed')},
              **{key: 0 for key in ('owned_count', 'main_count', 'neon_count')},
              'root_metadata_head': value['expected_metadata_head'], 'root_functional_commit': value['functional_commit'],
              'root_functional_count': 1019, 'review_commit': value['candidate_commit'], 'review_functional_count': 1029,
              'root_snapshot_sha256': value['proofs']['functional_snapshot']['sha256'],
              'review_snapshot_sha256': value['proofs']['review_functional_snapshot']['sha256'],
              'cold187_disposition': value['cold187_disposition']}
    return now, value, record


def function_source(raw, name):
    tree = ast.parse(raw.decode('utf-8'))
    node, = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    return ast.dump(node, include_attributes=False)


class SourceTests(unittest.TestCase):
    def test_six_exact_derivations_inverses_and_original_resource_ownership_guards(self):
        for name, (relative, pin) in D.PARENTS.items():
            parent = (EXPERIMENTS / relative).read_bytes()
            self.assertEqual(hashlib.sha256(parent).hexdigest(), pin)
            self.assertEqual(D.render(name, parent), (HERE / name).read_bytes())
            with self.assertRaises(ValueError): D.render(name, parent + b'\n')
        old_runner = (EXPERIMENTS / D.PARENTS['root_runner.py'][0]).read_bytes()
        new_runner = (HERE / 'root_runner.py').read_bytes()
        for name in ('typed_equal', 'receipt_ok', 'closure', 'invoke'):
            self.assertEqual(function_source(old_runner, name), function_source(new_runner, name))
        old_support = (EXPERIMENTS / D.PARENTS['diagnostic_support.py'][0]).read_bytes()
        new_support = (HERE / 'diagnostic_support.py').read_bytes()
        for name in ('validate_identity', 'safe', 'read_json', 'packet', 'reader', 'check_snapshot'):
            self.assertEqual(function_source(old_support, name), function_source(new_support, name))
        old_guard = old_support[old_support.index(b'    r = reader();'):old_support.index(b'    proof_data = {}')]
        self.assertIn(old_guard, new_support)  # six tools/574+copy/120/B originals intact.

    def test_unbound_templates_old_context_and_active_stale_or_mismatched_lane_refuse(self):
        now, value, record = authority()
        C.validate_admission(value, now); C.validate_current_closed_lane(value, {'closed_lane_root_record': record})
        with self.assertRaises(ValueError): C.validate_admission(json.loads((HERE / 'ADMISSION.template.json').read_bytes()), now)
        for key, replacement in (('candidate_commit', '00bf0f916a549f5e858cb39dd91a149071fd5181'),
                                 ('profile', 'SESSION_B_READONLY_RESOURCE_DIAGNOSTIC_AFTER_FAILED_FULL')):
            changed = copy.deepcopy(value); changed[key] = replacement
            with self.assertRaises(ValueError): C.validate_admission(changed, now)
        for key, replacement in (('current_targeted_run_active', True), ('owned_count', False),
                                 ('review_snapshot_sha256', 'f' * 64), ('full_suite_pass_claimed', True),
                                 ('observed_utc', (now - datetime.timedelta(seconds=121)).isoformat())):
            changed = copy.deepcopy(record); changed[key] = replacement
            with self.assertRaises(ValueError): C.validate_current_closed_lane(value, {'closed_lane_root_record': changed})

    def test_exact_capture_and_two_explicit_public_source_descriptors(self):
        H.validate_descriptor(descriptor())
        changed = descriptor(); changed['capture']['sha256'] = 'f' * 64
        with self.assertRaises(ValueError): H.validate_descriptor(changed)
        for key, replacement in (('sha256', 'f' * 64), ('path', 'C:/SYNTHETIC/unknown.py'), ('mtime_ns', False)):
            changed = descriptor(); changed['public_sources']['POSE_LIBRARY_GUI'][key] = replacement
            with self.assertRaises(ValueError): H.validate_descriptor(changed)
        changed = descriptor(); changed['public_sources']['UNKNOWN'] = changed['public_sources']['POSE_LIBRARY_GUI']
        with self.assertRaises(ValueError): H.validate_descriptor(changed)

    def test_recorded_fields_reject_extra_changed_and_reordered_handlers(self):
        # Synthetic field-equality exercise only, never a positive real baseline.
        expected = {'handler_list_counts': dict(B.COUNTS), 'callbacks': [
            {'handler_list': slot['handler_list'], 'index': slot['index'], 'synthetic_name': str(number)}
            for number, slot in enumerate(B.SLOTS)]}
        H.assert_same_handler_fields(copy.deepcopy(expected), expected)
        changes = [copy.deepcopy(expected) for _ in range(4)]
        changes[0]['callbacks'].append(changes[0]['callbacks'][0])
        changes[1]['callbacks'].reverse()
        changes[2]['callbacks'][0]['synthetic_name'] = 'different'
        changes[3]['handler_list_counts']['save_post'] = 1
        for changed in changes:
            with self.assertRaises(ValueError): H.assert_same_handler_fields(changed, expected)

    def test_metadata_collection_never_calls_authored_callbacks_unknown_metadata_refuses(self):
        calls = []
        def authored_callback(*args): calls.append(args)
        handlers = types.SimpleNamespace(**{name: [] for name in B.COUNTS})
        handlers.load_pre = [authored_callback]; handlers.load_post = [authored_callback, authored_callback]
        raw, _ = H.capture_handlers(handlers); observed = json.loads(raw)
        self.assertEqual(calls, [])
        paths = {'POSE_LIBRARY_GUI': observed['callbacks'][0]['code_filename'],
                 'COPY_GLOBAL_TRANSFORM': 'C:/SYNTHETIC/other.py'}
        with self.assertRaises(ValueError): B.validate_baseline(observed, paths, copy.deepcopy(B.SOURCES))
        self.assertEqual(calls, [])

    def test_public_projection_has_limited_claims_and_no_private_callback_fields(self):
        value = H.public_summary(); text = json.dumps(value)
        self.assertIs(value['loader_callbacks_may_have_run'], True)
        for key in ('runtime_globals_observed', 'callback_behavior_or_global_safety_proved', 'IO_confinement_proved', 'old_strict31_native_pass'):
            self.assertIs(value[key], False)
        for term in ('code_filename', 'qualname', 'bytecode_sha256', 'C:\\', 'callbacks_called'):
            self.assertNotIn(term, text)
        self.assertEqual(value['callbacks'], 3); self.assertEqual(value['handler_lists'], 11)


if __name__ == '__main__':
    unittest.main(verbosity=2)
