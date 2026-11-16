"""Independent metadata/source/privacy verifier; no models, engines, Git or network."""
from pathlib import Path
import gzip
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
MEDIA = {'.png', '.jpg', '.jpeg', '.webp', '.has', '.glb', '.gltf', '.vrm', '.mdl',
         '.vvd', '.vtx', '.vtf', '.wav', '.mp3', '.ogg', '.mp4', '.kra', '.blend'}
PRIVATE = {'pcm', 'points', 'mask', 'vertices', 'indices', 'weights', 'bone_matrices',
           'expected_world_bones', 'expected_native_Z_tips', 'matrix_world', 'raw_native_bytes'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name):
    return json.loads((HERE / name).read_bytes())


def scan(value):
    if isinstance(value, dict):
        assert not PRIVATE.intersection(value)
        for item in value.values():
            scan(item)
    elif isinstance(value, list):
        for item in value:
            scan(item)


def main():
    index = load('INDEX.json')
    assert len({row['path'] for row in index['files']}) == len(index['files'])
    actual = {path.relative_to(HERE).as_posix() for path in HERE.rglob('*') if path.is_file()}
    assert actual == {row['path'] for row in index['files']} | {'INDEX.json'}
    json_files = 0
    for row in index['files']:
        path = HERE / row['path']
        assert path.resolve().is_relative_to(HERE) and '..' not in Path(row['path']).parts
        assert path.suffix not in MEDIA and not any(part.endswith('.assets') for part in path.parts)
        assert path.name not in ('job.json', 'request.json', 'expected.json', 'PRIVATE_ORACLE.json', 'INPUT_LOCK.json')
        raw = path.read_bytes()
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        if path.name.endswith('.json.gz'):
            raw = gzip.decompress(raw)
        if path.suffix == '.json' or path.name.endswith('.json.gz'):
            scan(json.loads(raw)); json_files += 1
        elif path.suffix == '.log':
            assert not re.search(rb'"(?:pcm|points|mask|vertices|indices|weights|expected_world_bones)"\s*:', raw)
    aliases = load('PAYLOAD_INDEX.json')
    for row in aliases['sources']:
        path = HERE / row['stored']
        raw = path.read_bytes()
        assert len(raw) == row['stored_bytes'] and sha(raw) == row['stored_sha256']
        if row['compression'] == 'gzip':
            raw = gzip.decompress(raw)
        else:
            assert row['compression'] == 'none'
        assert len(raw) == row['source_bytes'] and sha(raw) == row['source_sha256']
        # Exact original read is limited to completed logs/metadata/frozen code
        # explicitly copied by the allowlisted producer, never native assets.
        source = Path(row['source'])
        assert source.suffix in ('.json', '.log', '.gd', '.py', '.cfg')
        assert source.read_bytes() == raw
    for row in aliases['stored_payloads']:
        raw = (HERE / row['path']).read_bytes()
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    benchmark = load('BENCHMARK.json')
    assert benchmark['passed'] and benchmark['checks'] == 96
    assert (benchmark['writer_checks'], benchmark['packed_reader_checks'], benchmark['linked_reader_checks']) == (77, 11, 8)
    assert benchmark['closed_private_jobs'] == 3 and all(benchmark['preservation_gates'].values())
    names = []
    for phase, count in [('writer', 77), ('reader-packed', 11), ('reader-linked', 8)]:
        result = load('actual2/' + phase + '/result.json')
        process = load('actual2/' + phase + '/process-verification.json')
        receipt = load('actual2/' + phase + '/private-receipt.json')
        assert result['checks'] == len(result['named_checks']) == count and result['failures'] == 0
        assert all(result['named_checks'].values()) and result['complete_assertion_set']
        assert result['private_native_arrays_serialized'] is False
        assert process['passed'] and process['result_binding'] and process['domain_checks_passed']
        assert process['checks'] == count and process['domain_failure_count'] == 0 and process['exit'] == 0
        assert process['retained_Popen_reaped'] and process['private_receipt_passed']
        assert receipt['exit'] == 0 and receipt['job_closed'] and receipt['desktop_closed']
        assert receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and not receipt['desktop_switch_requested']
        names += [phase + '/' + name for name in result['named_checks']]
    assert len(names) == len(set(names)) == 96
    actual = load('actual2/verification.json')
    assert len(actual['results']) == 3 and [row['checks'] for row in actual['results']] == [77, 11, 8]
    assert actual['checks_observed'] == actual['checks_expected'] == 96
    closure = load('actual2/authoritative-closure.json')
    assert closure['validation_passed'] and closure['owned_private_jobs_closed'] == 3
    assert closure['verification_sha256'] == sha((HERE / 'actual2/verification.json').read_bytes())
    assert closure['runtime_lease_released'] and closure['owned_runtime_commands_absent'] and closure['no_process_killed']
    old = load('actual1/writer/result.json')
    assert old['checks'] == 74 and old['failures'] == 2
    assert {name for name, ok in old['named_checks'].items() if not ok} == {
        'body.actual_primary_started', 'body.native_refusal_preserves_primary'}
    assert load('actual1/verification.json')['passed'] is False
    assert load('actual1/verification.json')['checks_observed'] == 0
    assert load('actual1/authoritative-closure.json')['validation_passed'] is False
    proof = load('SOURCE_PROOF.json')
    source_map = json.loads(gzip.decompress((HERE / 'actual2/source-before-and-after.json.gz').read_bytes()))
    assert len(source_map) == 1013
    for row in proof['actual2_sources']:
        raw = (HERE / row['stored']).read_bytes()
        assert sha(raw) == row['sha256'] == source_map[row['functional_path']]['sha256']
        assert len(raw) == row['bytes'] == source_map[row['functional_path']]['bytes']
    assert len(proof['actual2_sources']) == 8 and len(proof['actual1_test_sources']) == 2
    print(json.dumps({'passed': True, 'indexed_payloads': len(index['files']),
                      'json_documents_privacy_checked': json_files, 'exact_source_aliases': len(aliases['sources']),
                      'checks': 96, 'preserved_first_failure_checks': 74,
                      'INDEX_sha256': sha((HERE / 'INDEX.json').read_bytes())}))


if __name__ == '__main__':
    main()
