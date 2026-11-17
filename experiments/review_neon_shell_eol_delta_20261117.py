"""Root review of the exact three-path text canonicalization metadata successor."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parent_folder = ROOT / 'experiments/neon_source52_to_3a_root_review_20261117'
    parent_path = next(parent_folder.glob('REVIEWED*.json'))
    assert sha(parent_path.read_bytes()) == '9cbb7d3be7745eafff9e5417d455230a811c9ebfb1f3a78cb5cbd34f0822c817'
    parent = json.loads(parent_path.read_bytes())
    folder = ROOT / 'experiments/neon_3a_shell_eol_delta_proposal_20261117'
    raw = (folder / 'PROPOSED52_TO_CANDIDATE_DELTA.json').read_bytes()
    assert sha(raw) == '38f9cf4ffd3b82e64cf8f26c6f83c75f02aedf28c204fba826db18311f34798d'
    value = json.loads(raw)
    assert value['review_status'] == 'PROPOSED_EXACT_THREE_SCRIPT_EOL_CANONICALIZATION_ROOT_REVIEW_REQUIRED'
    assert value['reasons'] == parent['reasons'] and value['counts'] == parent['counts']
    assert value['raw_EOL_only_differences_excluded_from_delta_rows'] == parent['raw_EOL_only_differences_excluded_from_delta_rows']
    old_rows = {row['path']: row for row in parent['rows']}
    new_rows = {row['path']: row for row in value['rows']}
    names = {'tools/linux/liveness_shim.sh', 'tools/linux/run_test.sh', 'tools/linux/shoot.sh'}
    assert len(new_rows) == len(old_rows) == 39 and set(new_rows) == set(old_rows)
    changed = set()
    for name, row in new_rows.items():
        old = old_rows[name]
        if name not in names:
            assert row == old
            continue
        assert {k: v for k, v in row.items() if k != 'new_content_sha256'} == {k: v for k, v in old.items() if k != 'new_content_sha256'}
        tested = (ROOT / name).read_bytes()
        index = subprocess.check_output(['git', 'show', ':' + name], cwd=ROOT)
        assert sha(tested) == row['new_raw_sha256'] == old['new_raw_sha256']
        assert tested.replace(b'\r\n', b'\n') == index
        assert sha(index) == row['new_content_sha256'] and row['new_content_sha256'] != old['new_content_sha256']
        changed.add(name)
    assert changed == names
    assert value['sealed_admission_core_sha256'] == 'c6ebc4b6e3999fbdecf13697a2ccb0ca9f0cafe3368beaf9767bd5f247247f76'
    assert value['exact_delta_schema_and_byte_map_join']['new_content_source_map_sha256'] == '8bd2bf19ddfc4d51644924e60ca6446db252c6928ba91427653652d0508cf7ea'
    value['review_status'] = 'ROOT_REVIEWED_EXPLICIT_SOURCE_DELTA'
    value['reasons_status'] = 'ROOT_REVIEWED_ALL39_REASONS_PRESERVED'
    value['full_run_status'] = 'ACTUAL_RESTORED_MMD_FULL_PASSED158_36_21_AND_CLOSED'
    value['full_run_status_source'] = 'ROOT_ACTUAL_STRICT_F223_AUDIT_2026_11_17'
    value['root_review'] = {'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'parent_review_sha256': sha(parent_path.read_bytes()), 'proposal_sha256': sha(raw),
        'reviewed_exact_text_paths': sorted(names), 'all39_raw_rows_and_reasons_preserved': True,
        'all_other36_rows_exact': True, 'old52_native_bridge_and_107_EOL_records_preserved': True,
        'each_new_content_hash_equals_actual_Git_LF_blob': True,
        'all1029_tested_raw_bytes_and_Git_shell_LF_blobs_unchanged': True,
        'studio_test_or_native_numeric_threshold_changed': False,
        'full_terminal_inventory_sha256': 'a4b47b3bd0582e62f9466648cce07a25e8828656a9458262eac1d6e4eac84a23',
        'copy_activation_or_cold187_approval': False}
    output = ROOT / 'experiments/neon_3a_shell_eol_root_review_20261117'
    output.mkdir(exist_ok=False)
    target = output / 'REVIEWED52_TO_CANDIDATE_DELTA.json'
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    index = {'format': 'has_root_exact_three_shell_delta_review_1', 'files': [
        {'path': target.name, 'bytes': target.stat().st_size, 'sha256': sha(target.read_bytes())}],
        'parent_proposal_INDEX_sha256': '36b5c4c6ccee9a3f783864b7648a2dba708f6d91189ee996228748392125ffd8'}
    with (output / 'INDEX.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(index, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'reviewed_delta_sha256': sha(target.read_bytes()),
                     'INDEX_sha256': sha((output / 'INDEX.json').read_bytes()), 'reviewed_rows': 39,
                     'changed_canonical_hashes': 3, 'copy_or187_activated': False}))


if __name__ == '__main__': main()
