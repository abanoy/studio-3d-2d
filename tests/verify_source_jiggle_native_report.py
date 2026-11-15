"""Independently join an actual converter report to selected native MDL bytes.

No production parser imports. This validates inactive retention, not simulation.
The Junko 49-rule case additionally joins the previously audited raw extraction.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct

ROOT = Path(__file__).resolve().parents[1]
JUNKO_SHA = '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'
REFERENCE_SHA = 'e9665ad604b10932ea6ea7398acafe39ed224dc3be8e37ff287be3786a06dfc6'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(request_path, parameters_path, expected_rules):
    request_raw = request_path.read_bytes()
    report_raw = parameters_path.read_bytes()
    request = json.loads(request_raw)
    report = json.loads(report_raw)
    source = Path(request['source']).resolve(strict=True)
    original = Path(request['original_source']).resolve(strict=True)
    before = {p: (p.stat().st_size, p.stat().st_mtime_ns, digest(p.read_bytes()))
              for p in {source, original, request_path, parameters_path}}
    raw = source.read_bytes()
    assert raw[:4] == b'IDST' and struct.unpack_from('<i', raw, 4)[0] == 49
    assert struct.unpack_from('<I', raw, 76)[0] == len(raw)
    assert before[original][2] == request['sha256']
    count, start = struct.unpack_from('<II', raw, 156)
    assert 1 <= count <= 4096 and 408 <= start <= len(raw)-count*216
    native = report['native_parameters']
    bones = []
    declared = []
    for index in range(count):
        at = start + index*216
        relative_name, parent = struct.unpack_from('<ii', raw, at)
        name_at = at+relative_name
        name_end = raw.index(b'\0', name_at)
        name = raw[name_at:name_end].decode('latin-1')
        bones.append({'name':name, 'parent':parent})
        if struct.unpack_from('<I', raw, at+164)[0] == 5:
            declared.append(index)
    assert native['bones'] == bones and len(declared) == expected_rules
    assert len(report_raw) <= 256*1024
    joins = 0
    if expected_rules == 0:
        assert 'source_jiggle' not in native
        status = 'none'
        metadata_bytes = 0
    else:
        assert expected_rules == 49 and digest(raw) == JUNKO_SHA
        reference_raw = (ROOT/'experiments/source_appearance/native_jiggle_values_20261113/actual/RAW_VALUES.json').read_bytes()
        assert digest(reference_raw) == REFERENCE_SHA
        reference = json.loads(reference_raw)
        fields = reference['wire_field_order']
        meta = native['source_jiggle']
        assert meta['format'] == 'studio_source_jiggle_metadata_1'
        assert meta['status'] == 'retained_inert' and meta['runtime_support'] == 'not_implemented'
        assert meta['applied'] is False and meta['binding_status'] == 'unattempted'
        assert meta['full_native_rule_layout_verified'] is False
        assert meta['original_source_sha256'] == request['sha256']
        assert meta['native_mdl_sha256'] == digest(raw) and meta['native_bone_count'] == count
        assert type(meta['source_scale']) in (int,float) and math.isfinite(meta['source_scale']) and meta['source_scale'] == request['scale']
        assert [r['native_bone_index'] for r in meta['rules']] == declared
        assert len(fields) == 29 and len(reference['rules']) == 49
        for row, frozen in zip(meta['rules'], reference['rules']):
            index = row['native_bone_index']
            at = start+index*216
            flags, kind, relative = struct.unpack_from('<III', raw, at+160)
            payload = at+relative
            prefix = raw[payload:payload+120]
            wire_flags, *words = struct.unpack('<30I', prefix)
            values = struct.unpack_from('<29f', prefix, 4)
            proof = row['binary_provenance']
            assert index == frozen['index'] and row['native_bone_name'] == frozen['name'] == bones[index]['name']
            assert row['native_parent_index'] == frozen['parent'] == bones[index]['parent']
            assert row['native_bone_flags'] == flags and row['native_procedure_type'] == kind == 5
            assert row['raw_rule_flags'] == wire_flags == frozen['flags_uint32'] == 0x31
            assert row['known_rule_flags'] == frozen['known_flags'] and row['unknown_rule_flag_bits'] == 0
            assert proof['bone_record_offset'] == at and proof['bone_relative_rule_offset'] == relative
            assert proof['rule_absolute_offset'] == payload and proof['prefix_bytes'] == 120
            assert proof['prefix_sha256'] == digest(prefix) == frozen['prefix_sha256']
            assert proof['float32_words_uint32'] == words == frozen['float32_words_uint32']
            assert row['parameters'] == dict(zip(fields, values)) == frozen['parameters']
            assert all(math.isfinite(value) for value in values)
            assert row['applied'] is False and row['binding_status'] == 'unattempted'
            joins += len(values)
        metadata_bytes = len(json.dumps(meta, ensure_ascii=True, separators=(',',':'), allow_nan=False).encode()+b'\n')
        assert metadata_bytes <= 128*1024
        status = 'retained_inert'
    after = {p: (p.stat().st_size, p.stat().st_mtime_ns, digest(p.read_bytes())) for p in before}
    assert before == after
    return {'format':'has_source_jiggle_native_report_join_1', 'passed':True,
            'status':status, 'rules':expected_rules, 'native_bones':count,
            'exact_numeric_float32_joins':joins, 'metadata_compact_bytes':metadata_bytes,
            'actual_report_bytes':len(report_raw), 'native_mdl_sha256':digest(raw),
            'original_source_sha256':request['sha256'], 'report_sha256':digest(report_raw),
            'inputs_preserved':True, 'native_simulation':False,
            'scope':'Actual report joined to immutable native prefixes and prior independent extraction; no runtime binding, solver or artist-fidelity claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--parameters', required=True, type=Path)
    parser.add_argument('--expected-rules', required=True, type=int, choices=[0,49])
    parser.add_argument('--output', required=True, type=Path)
    options = parser.parse_args()
    output = options.output.resolve()
    assert output.is_relative_to((ROOT/'output').resolve()) and not output.exists()
    result = verify(options.request.resolve(strict=True), options.parameters.resolve(strict=True), options.expected_rules)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
