"""Authored RAM envelope and scalar fixtures only; no original/native file reads."""
import copy
import gzip
import json
import unittest
import verify_packet as V

REVIEW = r'C:\authored\Review'


def encoded(obj): return (json.dumps(obj, allow_nan=False) + '\n').encode()


def put(raw, path, value): raw['REVIEW:' + path] = encoded(value)


def fixture():
    raw = {}; sources = {'synthetic/f%d.py' % n: '0' * 64 for n in range(1027)}
    sources.update({'tests/verify_shape_catalog.py': '54431c2c486bce9828ec47ebe046da9f413b3854e8c0290829c24183fe72e057', 'tests/verify_character_height.py': 'cccfb7d472b5d552cbd3cfc07dc9058c1789b9c1947f6a1a548c924dd38a3f79'})
    put(raw, V.R + 'source-before.json', sources); put(raw, V.R + 'source-after.json', sources)
    scope = {'format': 'has_root_workspace_scope_observation_1', 'owned_count': 0, 'owned_matches': [], 'termination_issued': False, 'matcher_positive_cases': 4, 'matcher_negative_cases': 3}
    for label in ('before', 'catalogue-after', 'comparison-after', 'height-after', 'after'): put(raw, V.R + label + '-closure.json', scope)
    root = {'format': 'has_root_workspace_followup_1', 'passed': True, 'full_suite_pass_claimed': False, 'all_functional_source_unchanged': True, 'host_scopes_closed': True, 'functional_source_files': 1029, 'rows': []}
    for index, (label, checks, seconds, prefix, jobs) in enumerate(V.CASES):
        child = prefix + 'authored/'; paths = []
        for n in range(jobs):
            path = 'output/private-desktop/%s-%d.json' % (label, n); paths.append(REVIEW + '\\' + path.replace('/', '\\'))
            receipt = {'format': 'studio_private_desktop_1', 'exit': 0, 'private_window_seen': True, 'child_desktop_confirmed': True, 'foreground_child_observed': False, 'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True, 'desktop': 'AUTHORED_%s_%d' % (label, n), 'child_pid': 1000 + index * 10 + n}
            put(raw, path, receipt)
        report = {'checks': checks, 'failures': 0, 'folder': REVIEW + '\\' + child[:-1].replace('/', '\\'), 'private_receipts': paths}
        if label == 'catalogue':
            report.update(plans=['Authored fixture'] + V.LABELS, unit_checks=34, reader={'checks': 5, 'failures': 0})
            raw['REVIEW:' + child + 'shape_catalog_unit.log'] = b'SHAPE_CATALOG_UNIT {"checks":34,"failures":0}\n'; put(raw, child + 'reader-result.json', report['reader'])
        elif label == 'comparison':
            report.update(models=[{'label': x} for x in ['Authored fixture'] + V.LABELS], native_models_tested=6, teardown={'actual_readback_pending': True, 'checks': 2, 'failures': 0, 'released_after_app_free': True}, draft_recovery={'checks': 4, 'failures': 0})
            put(raw, child + 'teardown-result.json', report['teardown']); put(raw, child + 'draft-reader.json', report['draft_recovery'])
        else:
            report.update(models=[{'label': x} for x in ['Authored figure'] + V.LABELS + ['Short legs', 'Long legs', 'Head with full rig']], native_models=6, reader={'checks': 4, 'failures': 0}, native_import={'checks': 9, 'failures': 0})
            raw['REVIEW:' + child + 'reader.log'] = b'CHARACTER_HEIGHT_READER {"checks":4,"failures":0}\n'; raw['REVIEW:' + child + 'native.log'] = b'HEIGHT_IMPORT_NATIVE {"checks":9,"failures":0}\n'
            for name, path in zip(('command.json', 'reader-command.json', 'native-command.json'), paths, strict=True): put(raw, child + name, {'exit': 0, 'args': ['authored_private_driver', '--receipt', path]})
        row = {'label': label, 'exit': 0, 'pid': 100 + index, 'retained_Popen_reaped': True, 'timed_out': False, 'seconds': seconds, 'report': report}
        root['rows'].append(row); put(raw, V.R + label + '-process.json', {k: v for k, v in row.items() if k != 'report'}); put(raw, V.R + label + '-start.json', {'pid': row['pid'], 'retained_Popen': True}); put(raw, V.R + label + '-report.json', report); put(raw, child + 'result.json', {'checks': checks, 'failures': 0})
    put(raw, V.R + 'verification.json', root)
    raw['MAIN:experiments/neon_shape_catalog_fixture_actual_inputs_20261117/PREPARATION.json'] = encoded({'descriptor_sha256': '05bd6d4ba63e481cf3488f9bf0082d662812d3bf8bb861796860f42fcb3e2310', 'scene': {'bytes': 7830992, 'sha256': 'e9b21ab5f1171b21d0a7d3e3f83e5341f6b297516d09582e49c0283dfe10d8da'}, 'prior_plan_exact_current_bundle_path': True, 'historical_b577_glb_substituted_or_recovered': False, 'raw_descriptor_native_arrays_model_or_media_included': False})
    while len(raw) < 69: raw['MAIN:authored/padding-%d.log' % len(raw)] = ('authored scalar padding %d\n' % len(raw)).encode()
    assert len(raw) == 69
    return raw


def envelope(raw):
    rows = []
    for key, data in sorted(raw.items()):
        root, path = key.split(':', 1); rows.append({'root': root, 'path': path, 'bytes': len(data), 'mtime_ns': 0, 'sha256': V.sha(data)})
    summary = {'full_suite_pass_claimed': False, 'native_roundtrip_fidelity_or_main_merge_claimed': False, 'model_media_original_native_arrays_or_generated_fixture_payloads_included': False, 'scope': 'AUTHORED_RAM_ONLY'}
    spec = {'format': 'has_catalogue_00bf_closed_text_archive_recipe_1', 'roots': {'MAIN': r'C:\authored\Main', 'REVIEW': REVIEW}, 'inputs': rows, 'expected_summary': summary}; spec_raw = encoded(spec)
    files = {'BINDINGS.json': encoded({'format': 'has_catalogue_00bf_original_text_bindings_1', 'roots': spec['roots'], 'bindings': rows}), 'ACTUAL_RESULT.json': encoded(summary), 'README.md': b'Authored RAM test only.\n'}
    objects = []
    for digest, data in sorted({V.sha(data): data for data in raw.values()}.items()):
        name = 'objects/' + digest + '.gz'; packed = gzip.compress(data, mtime=0); files[name] = packed; objects.append({'path': name, 'bytes': len(packed), 'sha256': V.sha(packed), 'decoded_bytes': len(data), 'decoded_sha256': digest})
    pins = {'builder_sha256': 'a' * 64, 'verifier_sha256': 'b' * 64, 'check_source_sha256': 'c' * 64}
    idx = {'format': 'has_catalogue_00bf_compact_exact_actual_packet_1', 'recipe_inputs_sha256': V.sha(spec_raw), 'objects': objects, 'files': [{'path': name, 'bytes': len(files[name]), 'sha256': V.sha(files[name])} for name in ('BINDINGS.json', 'ACTUAL_RESULT.json', 'README.md')], 'original_bindings': 69, 'unique_decoded_objects': len(objects), 'uncompressed_original_bytes': sum(len(data) for data in raw.values()), 'real_private_jobs': 8, 'full_suite_pass_claimed': False, 'native_fidelity_claimed': False, 'upcoming_full_output_read': False, 'decoded_art_models_media_native_arrays_included': False, **pins}
    files['INDEX.json'] = encoded(idx)
    return files, spec_raw, V.sha(spec_raw), pins


class Artifact(unittest.TestCase):
    def setUp(self): self.raw = fixture()
    def synchronize(self, root):
        put(self.raw, V.R + 'verification.json', root)
        for row in root['rows']:
            label = row['label']; put(self.raw, V.R + label + '-report.json', row['report'])
    def reject(self):
        with self.assertRaises(ValueError): V.semantics(self.raw, REVIEW)
    def test_authored_RAM_complete_envelope_and_all_constituents_pass(self):
        report = V.verify_envelope(*envelope(self.raw)); self.assertEqual((report['catalogue'], report['comparison'], report['height'], report['private_jobs'], report['raw_VRM']), (130, 94, 105, 8, 9))
    def test_coherent_constituent_failures_or_float_counts_refused(self):
        for case in range(3):
            for key, value in [('failures', 1), ('checks', float(V.CASES[case][1]))]:
                with self.subTest(case=case, key=key):
                    self.setUp(); root = V.parse(self.raw['REVIEW:' + V.R + 'verification.json']); root['rows'][case]['report'][key] = value; self.synchronize(root); self.reject()
    def test_catalogue_membership_and_unit_marker_cannot_omit_cases(self):
        root = V.parse(self.raw['REVIEW:' + V.R + 'verification.json']); root['rows'][0]['report']['plans'].pop(); self.synchronize(root); self.reject()
        self.setUp(); self.raw['REVIEW:output/shape-catalog/authored/shape_catalog_unit.log'] = b'SHAPE_CATALOG_UNIT {"checks":34,"failures":1}\n'; self.reject()
    def test_comparison_native_membership_and_pending_teardown_preserved(self):
        root = V.parse(self.raw['REVIEW:' + V.R + 'verification.json']); report = root['rows'][1]['report']; report['teardown']['actual_readback_pending'] = False; put(self.raw, 'output/shape-comparison-tests/authored/teardown-result.json', report['teardown']); self.synchronize(root); self.reject()
        self.setUp(); root = V.parse(self.raw['REVIEW:' + V.R + 'verification.json']); root['rows'][1]['report']['native_models_tested'] = 5; self.synchronize(root); self.reject()
    def test_cold_reader_and_draft_recovery_direct_raw_joins_refused(self):
        for path in ['output/shape-catalog/authored/reader-result.json', 'output/shape-comparison-tests/authored/draft-reader.json']:
            with self.subTest(path=path):
                self.setUp(); put(self.raw, path, {'checks': 4, 'failures': 1}); self.reject()
    def test_height_rawVRM9_and_native_six_cannot_be_omitted(self):
        root = V.parse(self.raw['REVIEW:' + V.R + 'verification.json']); root['rows'][2]['report']['native_import']['checks'] = 8; self.synchronize(root); self.raw['REVIEW:output/character-height/authored/native.log'] = b'HEIGHT_IMPORT_NATIVE {"checks":8,"failures":0}\n'; self.reject()
    def test_typed_physical_false_exit_and_open_desktop_refused(self):
        for key, value in [('exit', False), ('desktop_closed', False), ('foreground_child_observed', True)]:
            with self.subTest(key=key):
                self.setUp(); path = 'output/private-desktop/height-0.json'; receipt = V.parse(self.raw['REVIEW:' + path]); receipt[key] = value; put(self.raw, path, receipt); self.reject()
    def test_duplicate_physical_job_or_missing_receipt_refused(self):
        first = V.parse(self.raw['REVIEW:output/private-desktop/catalogue-0.json']); put(self.raw, 'output/private-desktop/catalogue-1.json', first); self.reject()
    def test_height_available_command_receipt_join_refused(self):
        path = 'output/character-height/authored/native-command.json'; saved = V.parse(self.raw['REVIEW:' + path]); saved['args'][-1] = REVIEW + r'\output\private-desktop\wrong.json'; put(self.raw, path, saved); self.reject()
    def test_scope_and_source_map_drift_refused(self):
        scope = V.parse(self.raw['REVIEW:' + V.R + 'after-closure.json']); scope['owned_count'] = 1; put(self.raw, V.R + 'after-closure.json', scope); self.reject()
        self.setUp(); self.raw['REVIEW:' + V.R + 'source-after.json'] = b'{}'; self.reject()
    def test_current_input_scalar_provenance_cannot_claim_historical_substitution(self):
        key = 'MAIN:experiments/neon_shape_catalog_fixture_actual_inputs_20261117/PREPARATION.json'; proof = V.parse(self.raw[key]); proof['historical_b577_glb_substituted_or_recovered'] = True; self.raw[key] = encoded(proof); self.reject()
    def test_frozen_spec_and_code_pins_are_required(self):
        args = list(envelope(self.raw)); args[2] = '0' * 64
        with self.assertRaises(ValueError): V.verify_envelope(*args)
        args = list(envelope(self.raw)); args[3]['builder_sha256'] = '0' * 64
        with self.assertRaises(ValueError): V.verify_envelope(*args)
    def test_extra_members_and_object_path_escape_refused(self):
        args = list(envelope(self.raw)); args[0]['unbound.txt'] = b'extra'
        with self.assertRaises(ValueError): V.verify_envelope(*args)
        args = list(envelope(self.raw)); idx = V.parse(args[0]['INDEX.json']); idx['objects'][0]['path'] = '../original.glb'; args[0]['INDEX.json'] = encoded(idx)
        with self.assertRaises(ValueError): V.verify_envelope(*args)
    def test_compressed_corruption_and_coherent_decoded_size_bomb_refused(self):
        args = list(envelope(self.raw)); idx = V.parse(args[0]['INDEX.json']); name = idx['objects'][0]['path']; args[0][name] += b'x'
        with self.assertRaises(ValueError): V.verify_envelope(*args)
        args = list(envelope(self.raw)); idx = V.parse(args[0]['INDEX.json']); idx['objects'][0]['decoded_bytes'] = 2 * 1024 * 1024 + 1; args[0]['INDEX.json'] = encoded(idx)
        with self.assertRaises(ValueError): V.verify_envelope(*args)
    def test_coherent_bindings_original_path_rewrite_refused(self):
        args = list(envelope(self.raw)); binding = V.parse(args[0]['BINDINGS.json']); binding['bindings'][0]['path'] = 'output/other.json'; data = encoded(binding); args[0]['BINDINGS.json'] = data; idx = V.parse(args[0]['INDEX.json']); row = next(x for x in idx['files'] if x['path'] == 'BINDINGS.json'); row.update(bytes=len(data), sha256=V.sha(data)); args[0]['INDEX.json'] = encoded(idx)
        with self.assertRaises(ValueError): V.verify_envelope(*args)
    def test_summary_cannot_be_changed_into_full_or_native_qualification(self):
        args = list(envelope(self.raw)); idx = V.parse(args[0]['INDEX.json']); idx['full_suite_pass_claimed'] = True; args[0]['INDEX.json'] = encoded(idx)
        with self.assertRaises(ValueError): V.verify_envelope(*args)


if __name__ == '__main__': unittest.main(verbosity=2)
