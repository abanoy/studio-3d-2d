"""Render reviewable patches only. Never writes Main or Review product sources."""
from pathlib import Path
import copy
import difflib
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
APP_SHA = '88871ebd831d5a466b31336282a9bb53f264653dd5ff299fb10dc90a3080dd67'
APP_LF_SHA = '0eb4a61fe031652ac70562126114172fe5d1df6559c58156a1aed18b13e89307'
MANIFESTS = {
    'tests/helper_preview_port_files.json': ('2c9e483649108b9760aeb96e20c8ac95025a4b595fa0cfbb730308247fb7a8f0', 25),
    'tests/wind_review_port_files.json': ('4cb3709064b668e63b25cb9576a69992495c5707ed5ec2dba291c0768852e79d', 16),
}
BEFORE = b'\tif pose_editor:pose_editor.refresh_values()\r\n\tif scene_view:scene_view.sync()\r\n\trefresh_view_row()\r\n'
AFTER = b'\tif pose_editor:pose_editor.refresh_values()\r\n\tif scene_view:scene_view.sync()\r\n\trefresh_camera_inspector()\r\n\trefresh_view_row()\r\n'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def render_app(raw):
    assert sha(raw) == APP_SHA and sha(raw.replace(b'\r\n', b'\n')) == APP_LF_SHA
    assert raw.count(BEFORE) == 1 and AFTER not in raw
    result = raw.replace(BEFORE, AFTER, 1)
    assert result.replace(AFTER, BEFORE, 1) == raw
    assert len(result) - len(raw) == len(b'\trefresh_camera_inspector()\r\n')
    return result


def render_manifest(name, raw, app_before, app_after):
    """Two app hash fields in one exact existing row; every other byte stays exact."""
    assert name in MANIFESTS and sha(raw) == MANIFESTS[name][0]
    assert sha(app_before) == APP_SHA and sha(app_before.replace(b'\r\n', b'\n')) == APP_LF_SHA
    assert app_after == render_app(app_before)
    original = json.loads(raw)
    assert len(original['files']) == MANIFESTS[name][1]
    rows = [row for row in original['files'] if row.get('path') == 'src/app.gd']
    assert len(rows) == 1 and rows[0] == {'path': 'src/app.gd', 'sha256': APP_SHA, 'lf_sha256': APP_LF_SHA, 'category': 'runtime'}
    expected = copy.deepcopy(original)
    target, = [row for row in expected['files'] if row.get('path') == 'src/app.gd']
    target['sha256'] = sha(app_after)
    target['lf_sha256'] = sha(app_after.replace(b'\r\n', b'\n'))
    result = raw
    replacements = []
    for field, before, after in [('sha256', APP_SHA, target['sha256']), ('lf_sha256', APP_LF_SHA, target['lf_sha256'])]:
        old = ('"' + field + '": "' + before + '"').encode('ascii')
        new = ('"' + field + '": "' + after + '"').encode('ascii')
        assert result.count(old) == 1 and new not in result
        result = result.replace(old, new, 1); replacements.append((old, new))
    assert json.loads(result) == expected
    inverse = result
    for before, after in reversed(replacements):
        assert inverse.count(after) == 1
        inverse = inverse.replace(after, before, 1)
    assert inverse == raw
    assert [row for row in json.loads(result)['files'] if row.get('path') == 'src/pose_editor.gd'] == [row for row in original['files'] if row.get('path') == 'src/pose_editor.gd']
    return result


def patch(name, before, after):
    lines = difflib.unified_diff(before.decode('utf-8').splitlines(), after.decode('utf-8').splitlines(),
                                 fromfile='a/' + name, tofile='b/' + name, n=4, lineterm='')
    return ('\n'.join(lines) + '\n').encode('utf-8')


def main():
    names = ['src/app.gd', *MANIFESTS, 'tests/camera_range_smoke.gd']
    originals = {name: (REVIEW / name).read_bytes() for name in names}
    proposed = {'src/app.gd': render_app(originals['src/app.gd'])}
    for name in MANIFESTS:
        proposed[name] = render_manifest(name, originals[name], originals['src/app.gd'], proposed['src/app.gd'])
    files = {
        'app.gd.proposed.patch': patch('src/app.gd', originals['src/app.gd'], proposed['src/app.gd']),
        'manifest-app-hashes.proposed.patch': b''.join(patch(name, originals[name], proposed[name]) for name in MANIFESTS),
    }
    record = {'format': 'has_camera_details_visibility_source_proposal_1', 'status': 'PROPOSED_NOT_APPLIED_ROOT_REVIEW_AND_ACTUAL_FOCUSED_TEST_REQUIRED',
        'baseline_candidate': '00bf0f916a549f5e858cb39dd91a149071fd5181',
        'diagnosis': 'Neon Camera details parent visibility is refreshed only during _process; refresh_workspace flips Advanced child visibility synchronously but leaves that parent stale for immediate camera-mode queries.',
        'change': 'Call the existing refresh_camera_inspector once in refresh_workspace after Advanced and camera section visibility updates.',
        'product_added_lines': 1, 'product_removed_lines': 0, 'app_raw_byte_inverse': True,
        'original_CRLF_preserved': True, 'classic_empty_inspector_guard_unchanged': True,
        'camera_values_handlers_signals_modes_and_shortcuts_unchanged': True,
        'existing_camera_range_assertions_unchanged': True,
        'camera_range_smoke_sha256': sha(originals['tests/camera_range_smoke.gd']),
        'manifest_app_rows_changed': 2, 'manifest_hash_fields_per_app_row': 2,
        'all_other_manifest_bytes_members_and_pose_rows_exact': True,
        'manifest_row_counts': {name: MANIFESTS[name][1] for name in MANIFESTS},
        'source_hashes': {name: {'before_sha256': sha(originals[name]), 'proposed_sha256': sha(raw)} for name, raw in proposed.items()},
        'app_before_LF_sha256': APP_LF_SHA,
        'app_proposed_LF_sha256': sha(proposed['src/app.gd'].replace(b'\r\n', b'\n')),
        'product_or_manifest_writes': False, 'engine_or_GPU_or_CIM_or_Git_execution': False,
        'actual_post_fix_result': 'UNRUN', 'root_native_lane_remains_exclusive': True}
    assert all((REVIEW / name).read_bytes() == raw for name, raw in originals.items())
    files['PROPOSAL.json'] = (json.dumps(record, indent=2) + '\n').encode('utf-8')
    for name, raw in files.items():
        with (HERE / name).open('xb') as stream: stream.write(raw)
    print(json.dumps(record))


if __name__ == '__main__': main()
