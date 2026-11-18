"""Exact independent GitHub byte readback of the public179-file checkpoint."""
from pathlib import Path
import base64
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '973039e40622ac20600e6d297d712de419877eda'
manifest = json.loads((ROOT / 'output/neon-qualified-merge-source-checkpoint-20261117-manifest.json').read_bytes())
paths = [row['path'] for row in manifest['files']] + ['experiments/neon_qualified_merge_source_checkpoint_catalogue_20261117/PUBLIC_MANIFEST.json']
assert len(paths) == len(set(paths)) == 132

# Immutable qualified-merge paths, independently joined to the frozen132 catalogue.
MERGE_COMMIT = 'c4126dec6083e52fb856e5cad5442227133b3c05'
MERGE_FIRST_PARENT = 'f21b9ec85ae63006d036ca7a21c5c82e53fda019'
MERGE_SECOND_PARENT = '3a3701ab6edfa81dc883759403c170b8555aab07'
EXPECTED_MERGE_EXTRAS = ('docs/REDESIGN-PORT.md', 'docs/redesign-mock/app-advanced.png', 'docs/redesign-mock/app-camera.png', 'docs/redesign-mock/app-draw.png', 'docs/redesign-mock/app-pose.png', 'docs/redesign-mock/mock-camera.png', 'docs/redesign-mock/mock-draw.png', 'docs/redesign-mock/mock-pose.png', 'src/app.gd', 'src/canvas_view.gd', 'src/dock_tree.gd', 'src/home_screen.gd', 'src/movement_path_editor.gd', 'src/movement_path_view.gd', 'src/pose_editor.gd', 'src/reference_sheet_view.gd', 'src/scene_view.gd', 'src/sequence_editor.gd', 'src/sequence_timeline.gd', 'src/studio_theme.gd', 'src/timeline_navigation.gd', 'src/timeline_view.gd', 'src/workspace_layout.gd', 'src/world_selection.gd', 'tests/animated_channels_smoke.gd', 'tests/color_sampler_smoke.gd', 'tests/helper_preview_port_files.json', 'tests/movement_path_smoke.gd', 'tests/neon_behavior_regression.gd', 'tests/neon_compact_timeline_reveal_smoke.gd', 'tests/neon_inset_scene_regression.gd', 'tests/neon_rail_placement_smoke.gd', 'tests/neon_world_rail_lifecycle.gd', 'tests/object_timing_smoke.gd', 'tests/scene_view_smoke.gd', 'tests/source_bone_bindings_unit.gd', 'tests/verify.py', 'tests/verify_character_height.py', 'tests/verify_neon_workspace.py', 'tests/verify_scene_view.py', 'tests/verify_shape_catalog.py', 'tests/waveform_levels_smoke.gd', 'tests/wind_review_port_files.json', 'tools/linux/liveness_shim.sh', 'tools/linux/run_test.sh', 'tools/linux/shoot.gd', 'tools/linux/shoot.sh')
MERGE_PNG_PATHS = ('docs/redesign-mock/app-advanced.png', 'docs/redesign-mock/app-camera.png', 'docs/redesign-mock/app-draw.png', 'docs/redesign-mock/app-pose.png', 'docs/redesign-mock/mock-camera.png', 'docs/redesign-mock/mock-draw.png', 'docs/redesign-mock/mock-pose.png')
merge_header = subprocess.check_output(['git', 'cat-file', 'commit', MERGE_COMMIT], cwd=ROOT).split(b'\n\n', 1)[0]
assert [line.split()[1].decode() for line in merge_header.splitlines() if line.startswith(b'parent ')] == [MERGE_FIRST_PARENT, MERGE_SECOND_PARENT]
checkpoint_header = subprocess.check_output(['git', 'cat-file', 'commit', COMMIT], cwd=ROOT).split(b'\n\n', 1)[0]
assert [line.split()[1].decode() for line in checkpoint_header.splitlines() if line.startswith(b'parent ')] == [MERGE_COMMIT]
merge_diff = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', '-z', MERGE_FIRST_PARENT, MERGE_COMMIT], cwd=ROOT)
assert merge_diff.endswith(b'\0')
merge_paths = [name.decode('utf-8') for name in merge_diff[:-1].split(b'\0')]
assert len(merge_paths) == len(set(merge_paths)) == 48
assert set(merge_paths) & set(paths) == {'LLM.md'}
merge_extras = [name for name in merge_paths if name not in paths]
assert tuple(merge_extras) == EXPECTED_MERGE_EXTRAS and len(merge_extras) == 47
for name in merge_extras:
    assert name and '\\' not in name and ':' not in name and not Path(name).is_absolute()
    parts = Path(name).parts
    assert not any(part in ('.', '..', 'output', '.git', '.godot', '__pycache__') or part.casefold().startswith('private') or 'remote-batch' in part for part in parts), name
    assert not name.endswith('.pyc'), name
functional_extra = [name for name in merge_extras if name.split('/')[0] in ('src', 'tests', 'tools', 'data', 'examples') or name in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
assert len(functional_extra) == 39
assert set(merge_extras) - set(functional_extra) == {'docs/REDESIGN-PORT.md', *MERGE_PNG_PATHS}
paths.extend(merge_extras)
assert len(paths) == len(set(paths)) == 179
query = ''.join(COMMIT + ':' + name + '\n' for name in paths).encode()
raw_git = subprocess.check_output(['git', 'cat-file', '--batch'], input=query, cwd=ROOT)
expected = {}
offset = 0
for name in paths:
    end = raw_git.index(b'\n', offset)
    blob, kind, size = raw_git[offset:end].decode().split(' ')
    assert kind == 'blob'
    size = int(size)
    body = raw_git[end + 1:end + 1 + size]
    assert len(body) == size and raw_git[end + 1 + size:end + 2 + size] == b'\n'
    expected[name] = (blob, body)
    offset = end + size + 2
assert offset == len(raw_git)
seen = set()
verified = []
for start in range(0, 179, 20):
    batch = json.loads((ROOT / f'output/9730-all-remote-batch-{start:03}.json').read_bytes())
    assert batch['commit'] == COMMIT and batch['start'] == start
    assert [row['path'] for row in batch['files']] == paths[start:start + 20]
    for row in batch['files']:
        name = row['path']
        assert name not in seen
        seen.add(name)
        response = row['response']
        assert response['encoding'] == 'base64'
        remote = base64.b64decode(response['content'])
        method = 'contents_base64'
        if not remote and 'fallback_utf8' in row:
            remote = row['fallback_utf8'].encode('utf-8')
            method = 'blob_sha_utf8_contents_api_oversize_fallback'
        blob = hashlib.sha1(b'blob ' + str(len(remote)).encode() + b'\0' + remote).hexdigest()
        wanted_blob, wanted_bytes = expected[name]
        assert blob == response['sha'] == wanted_blob and remote == wanted_bytes, name
        working = (ROOT / name).read_bytes()
        if name in MERGE_PNG_PATHS:
            assert working == remote, 'Approved PNG requires exact binary bytes: ' + name
        if working == remote:
            recipe = {'kind': 'exact'}
        else:
            assert b'\r' not in remote and working.replace(b'\r\n', b'\n') == remote
            endings = [i for i, line in enumerate(working.splitlines(keepends=True)) if line.endswith(b'\r\n')]
            selected = set(endings)
            rebuilt = b''.join(line[:-1] + b'\r\n' if i in selected and line.endswith(b'\n') else line for i, line in enumerate(remote.splitlines(keepends=True)))
            assert rebuilt == working
            recipe = {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': endings}
        verified.append({'path': name, 'bytes': len(remote), 'sha256': hashlib.sha256(remote).hexdigest(),
            'git_blob': blob, 'independent_remote_bytes_exact': True, 'remote_method': method,
            'working_sha256': hashlib.sha256(working).hexdigest(), 'working_recipe': recipe})
assert seen == set(paths)
public = expected['experiments/neon_qualified_merge_source_checkpoint_catalogue_20261117/PUBLIC_MANIFEST.json'][1]
assert hashlib.sha256(public).hexdigest() == '3659c0b73f22100f9eb1fd458e07afcd150cd1cfdf1f7051d34881044567c3d9'
target = ROOT / 'experiments/neon_qualified_merge_source_checkpoint_remote_20261117/COMPLETE_READBACK.json'
target.parent.mkdir(exist_ok=False)
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_complete_independent_remote_readback_1', 'commit': COMMIT,
        'immutable_qualified_merge_commit': MERGE_COMMIT, 'checkpoint_catalogue_files': 132,
        'merged_source_and_art_extra_files': 47, 'copy_or_cold187_claimed': False,
        'files': verified, 'file_count': len(verified), 'bytes': sum(row['bytes'] for row in verified),
        'redesign_merge_claimed': True, 'review_branch375_pushed': False, 'cleanup_performed': False}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'commit': COMMIT, 'independent_exact_files': len(verified), 'bytes': sum(row['bytes'] for row in verified),
    'working_byte_recipes': sum(row['working_recipe']['kind'] != 'exact' for row in verified), 'redesign_merged': True, 'cleanup_performed': False}))
