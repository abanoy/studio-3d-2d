"""Run metadata-only controls; no engine, parser, geometry, process, or Git API."""
from pathlib import Path
import copy
import datetime
import hashlib
import json
import struct
import sys

sys.dont_write_bytecode = True
import admission as A

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
INPUT = ROOT / 'output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685/parameters.json'
EXPECTED = 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def set_at(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


def main():
    raw = INPUT.read_bytes()
    assert digest(raw) == EXPECTED
    report = json.loads(raw)
    binding = {'status': 'bound_inactive', 'source_sha256': A.GLB,
               'jiggle_wire_sha256': A.WIRE, 'bindings': 69, 'rule_owner_ids': 49,
               'selected_native8_is_leaf': True, 'import_context_current': True}
    baseline = copy.deepcopy(report)
    baseline_binding = copy.deepcopy(binding)
    rows = []

    def check(name, value, summary=None, expected='generic', selected=(8,), override=False):
        before = copy.deepcopy(value)
        summary = binding if summary is None else summary
        summary_before = copy.deepcopy(summary)
        result = A.route(value, summary, selected_native=selected, generic_override=override)
        assert result['route'] == expected, (name, result)
        assert result['native_metadata_modified'] is False
        assert result['full_native_rule_layout_verified'] is False
        assert result['runtime_admission_proven'] is False
        # NaNs are used in negative controls; compare a non-strict JSON encoding
        # only for test nonmutation, never as a product metadata serialization.
        assert json.dumps(value, sort_keys=True) == json.dumps(before, sort_keys=True)
        assert summary == summary_before
        rows.append({'name': name, 'passed': True, 'route': result['route'], 'reason': result.get('reason', 'necessary_metadata_gates_only')})

    check('actual_pinned_metadata_necessary_gates', report, expected='eligible_for_native8_live_checks')
    for name, value in [('no_report', None), ('ordinary_model', {}), ('unrelated_report', {'source_sha256': '0' * 64})]:
        check(name, value)
    check('explicit_generic_override_wins', report, override=True)
    for selected in [(), (7,), (8, 9), (8, 8), (8.0,), (True,), list(range(49))]:
        check('selected_rule_domain_' + repr(selected), report, selected=selected)
    mutations = [
        (['scale'], .02), (['scale'], True), (['scale'], float('nan')),
        (['source_sha256'], '0' * 64), (['sourceio_revision'], '0' * 40),
        (['native_parameters', 'source_export_crosswalk', 'profile'], 'other'),
        (['native_parameters', 'source_export_crosswalk', 'glb_sha256'], '0' * 64),
        (['native_parameters', 'source_export_crosswalk', 'source_scale'], 1.0),
        (['native_parameters', 'source_export_crosswalk', 'applied'], True),
        (['native_parameters', 'source_export_crosswalk', 'applied'], 0),
        (['native_parameters', 'source_jiggle', 'applied'], True),
        (['native_parameters', 'source_jiggle', 'full_native_rule_layout_verified'], True),
        (['native_parameters', 'source_jiggle', 'full_native_rule_layout_verified'], 0),
        (['native_parameters', 'source_jiggle', 'runtime_support'], 'implemented'),
        (['native_parameters', 'source_jiggle', 'native_bone_count'], True),
        (['native_parameters', 'source_jiggle', 'declared_jiggle_rule_count'], 48),
        (['native_parameters', 'bones', 8, 'parent'], True),
        (['native_parameters', 'bones', 8, 'parent'], 6),
        (['native_parameters', 'bones', 9, 'parent'], 8),
        (['native_parameters', 'bones', 7, 'parent'], 8),
    ]
    for index, (path, replacement) in enumerate(mutations):
        changed = copy.deepcopy(report)
        set_at(changed, path, replacement)
        check('metadata_mutation_%02d_' % index + '.'.join(map(str, path)), changed)
    rules_path = ['native_parameters', 'source_jiggle', 'rules']
    original_rules = report['native_parameters']['source_jiggle']['rules']
    for count in [0, 48, 50]:
        changed = copy.deepcopy(report)
        set_at(changed, rules_path, (original_rules + [original_rules[0]])[:count])
        check('rule_count_' + str(count), changed)
    leaf_offset = next(i for i, row in enumerate(original_rules) if row['native_bone_index'] == 8)
    for field in A.ACTIVE8:
        for label, value in [('bool', True), ('nan', float('nan')), ('positive_infinity', float('inf')), ('negative_infinity', float('-inf')), ('wrong_finite', A.ACTIVE8[field] + 1)]:
            changed = copy.deepcopy(report)
            set_at(changed, rules_path + [leaf_offset, 'parameters', field], value)
            check('leaf_' + field + '_' + label, changed)
    for offset in range(49):
        changed = copy.deepcopy(report)
        set_at(changed, rules_path + [offset, 'raw_rule_flags'], 0x35)
        check('unknown_flags_owner_' + str(offset), changed)
        changed = copy.deepcopy(report)
        row = changed['native_parameters']['source_jiggle']['rules'][offset]
        row['parameters']['length'] += 1.0
        row['binary_provenance']['float32_words_uint32'][0] = struct.unpack('<I', struct.pack('<f', row['parameters']['length']))[0]
        prefix = struct.pack('<I29I', 49, *row['binary_provenance']['float32_words_uint32'])
        row['binary_provenance']['prefix_sha256'] = digest(prefix)
        check('self_consistent_altered_rule_rejected_by_wire_' + str(offset), changed)
    for key, value in [('status', 'unavailable'), ('source_sha256', '0' * 64), ('jiggle_wire_sha256', '0' * 64),
                       ('bindings', True), ('rule_owner_ids', 48), ('selected_native8_is_leaf', False),
                       ('import_context_current', False), ('import_context_current', 1)]:
        summary = copy.deepcopy(binding)
        summary[key] = value
        check('live_summary_' + key + '_' + str(value), report, summary=summary)
    assert report == baseline and binding == baseline_binding
    assert INPUT.read_bytes() == raw
    result = {'format': 'has_source_native_metadata_admission_CPU_controls_1', 'passed': True,
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'checks': len(rows), 'failed': 0, 'case_rows': rows,
              'input': {'path': str(INPUT), 'bytes': len(raw), 'sha256': EXPECTED},
              'source_sha256': {name: digest((HERE / name).read_bytes()) for name in ['admission.py', 'controls.py']},
              'metadata_or_binding_arguments_modified': False,
              'raw_input_metadata_native_arrays_geometry_media_copied': False,
              'production_tests_or_application_modified_by_controls': False,
              'engine_parser_or_process_queries_or_Git_or_network': False,
              'runtime_admission_or_production_integration_proven': False,
              'limits': 'Necessary metadata gates only, using a CPU synthetic summary for a previously proven live resolver. Actual source-file bytes, crosswalk graph/skin membership, skeleton/import context, timing, state ownership and lifecycle still require production Godot tests. Generic fallback remains a routing request, not an executed generic regression test.'}
    with (HERE / 'CPU_CONTROLS.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'passed': True, 'checks': len(rows), 'failed': 0, 'result_sha256': digest((HERE / 'CPU_CONTROLS.json').read_bytes())}))


if __name__ == '__main__':
    main()
