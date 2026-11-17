"""Reproduce draft source metadata only; never qualifies a full, merge or copy."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import stat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
CORE = ROOT / 'experiments/neon_owner_review_executor_20261117/admission_core.py'
CORE_SHA = 'cdad5359f6fe6bf63d93bd95845680dec7f6eb2d041b265d05b05efe3ce1096f'
OLD_MAP = ROOT / 'output/windows-canonical-bone-binding-20261116T041518335/source-before.json'
NEW_MAP = REVIEW / 'output/windows-neon-00bf0f9-replay2-20261117T155709412051/source-before.json'
OLD_PIN = '4b1eb25e1da8e510106fe3dd01c4b5014c7cc719133f18e1bbccd386ec9deae7'
NEW_PIN = '5064dc9e7932cfb05360e3df974dbbeb56cae682bfade6cb286e3040302ab67f'
OUTPUT = HERE / 'DRAFT52_TO_00BF_DELTA.json'
SCOPE = ('src', 'tests', 'tools', 'data', 'examples')
TOP = ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')
CORES = ('src/model.gd', 'src/source_bone_bindings.gd', 'src/scene3d.gd')
REASONS = {
    'src/app.gd': 'Neon workspace integration: header, mode/tool controls, camera/drawing inspectors, stage/footer/insets, compact timeline, display preferences and live status presentation.',
    'src/canvas_view.gd': 'Neon editor surround, joint/frame overlays and fit insets; inset frame sizing and explicit 0.01-pixel scene-edge hit tolerance.',
    'src/dock_tree.gd': 'Theme notebook tabs and dock styling through the new style_book path.',
    'src/home_screen.gd': 'Use the Neon background palette when that display style is selected.',
    'src/movement_path_editor.gd': 'Describe Neon movement keys as violet while retaining black-key guidance for classic styles.',
    'src/movement_path_view.gd': 'Theme the movement-path drawing and key markers for Neon.',
    'src/pose_editor.gd': 'Add Neon pose-inspector blocks, operation/space controls and contact/key/status presentation.',
    'src/reference_sheet_view.gd': 'Theme reference-sheet drawing colors for the selected workspace style.',
    'src/scene_view.gd': 'Compact guide menu and inset-aware Setup camera overscan, with layout synchronization for the inset frame.',
    'src/sequence_editor.gd': 'Hide the root breadcrumb in Neon Simple mode while retaining nested and Advanced breadcrumbs.',
    'src/sequence_timeline.gd': 'Theme sequence timeline drawing and selected/key presentation for Neon.',
    'src/studio_theme.gd': 'Expand the style system with Neon palette, icons, fonts and control/StyleBox helpers alongside existing display styles.',
    'src/timeline_navigation.gd': 'Add Neon navigation-control styling and updated transport presentation.',
    'src/timeline_view.gd': 'Add Neon lane/key/clip/waveform/playhead rendering and shared content-padding coordinate helpers.',
    'src/workspace_layout.gd': 'Add Neon panel headers/nesting, left-rail unfold placement, style/resize synchronization and lifecycle teardown.',
    'src/world_selection.gd': 'Add Neon entity rail tiles/actions, selected-state synchronization and guarded signal/font/lifecycle handling.',
    'tests/animated_channels_smoke.gd': 'Reveal the exact requested native channel before routed input and assert it lies in the bounded visible track viewport.',
    'tests/helper_preview_port_files.json': 'Refresh the explicit app and pose-editor raw/canonical source pins for the Neon source successor; other reviewed roles remain enumerated.',
    'tests/movement_path_smoke.gd': 'Reveal each requested compact timeline channel before input and edit drawing pixels through the existing edit_image helper.',
    'tests/neon_behavior_regression.gd': 'Add isolated Neon behavior coverage for controls, fullscreen/input routing, toasts and settled live layout.',
    'tests/neon_compact_timeline_reveal_smoke.gd': 'Add compact timeline reveal/input coverage including a generated silent audio fixture.',
    'tests/neon_inset_scene_regression.gd': 'Add inset-frame scene/ray geometry regression coverage.',
    'tests/neon_rail_placement_smoke.gd': 'Add rail/list arrangement, panel width and retained-view placement coverage.',
    'tests/neon_world_rail_lifecycle.gd': 'Add live world-rail lifecycle, ownership, reentry, signal and font-profile checks.',
    'tests/object_timing_smoke.gd': 'Reveal the exact last model row instead of scrolling to content end before compact timeline input.',
    'tests/scene_view_smoke.gd': 'Add a source-pinned independent scene/readback composition oracle for the Neon editor mask; retain the original recovered base-color predicate.',
    'tests/source_bone_bindings_unit.gd': 'Strip CR as well as LF from the authored base64 GLB text before decoding the same fixture.',
    'tests/verify.py': 'Register the five-part Neon workspace verifier and require its fresh 12504-check/source/private-closure result in the full suite.',
    'tests/verify_character_height.py': 'Select the retained raw-VRM descriptor through fixture_output so copied fixtures remain part of the existing native height cases.',
    'tests/verify_neon_workspace.py': 'Add the bounded five-part Neon verifier with fresh reports, exact source snapshots, strict private receipts and expected 12504-check scope.',
    'tests/verify_scene_view.py': 'Require all106 scene-view checks, four cases and supported successful display-composition metadata for each graphical case.',
    'tests/verify_shape_catalog.py': 'Select the existing supplied-Mima descriptor through fixture_output rather than a checkout-local output-only path.',
    'tests/waveform_levels_smoke.gd': 'Reveal the actual Audio row and use the declared Neon RGBA/straight-edge raster oracle with explicit source conditions and sample bounds.',
    'tests/wind_review_port_files.json': 'Refresh the explicit app/pose-editor source pins and add the Neon source-successor provenance reference.',
    'tools/linux/liveness_shim.sh': 'Add the retained legacy Linux /proc liveness stand-in; it is source tooling and is not executed here.',
    'tools/linux/run_test.sh': 'Add a Linux Xvfb smoke wrapper with generated audio fixtures, bounded execution and explicit result/error markers.',
    'tools/linux/shoot.gd': 'Add a source screenshot driver using scratch recovery/display preferences and authored scene/drawing fixtures.',
    'tools/linux/shoot.sh': 'Add the isolated-XDG Linux screenshot wrapper, timeout, output markers and cleanup of its own temporary directory.',
}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def read(path):
    for item in (path, *path.parents):
        info = item.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
    before = path.stat(); raw = path.read_bytes(); after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    return raw


def inventory(folder):
    names = {path.relative_to(folder).as_posix() for part in SCOPE for path in (folder / part).rglob('*')
             if path.is_file() and path.suffix != '.pyc' and '__pycache__' not in path.parts}
    return names | set(TOP)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='compare with the existing draft without writing')
    args = parser.parse_args()
    assert sha(read(CORE)) == CORE_SHA
    spec = importlib.util.spec_from_file_location('unchanged_draft_delta_core', CORE)
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    old_raw, new_raw = read(OLD_MAP), read(NEW_MAP)
    assert sha(old_raw) == OLD_PIN == A.SOURCE52_SHA and sha(new_raw) == NEW_PIN
    old_doc, new_doc = A.parse(old_raw), A.parse(new_raw)
    assert old_doc['commit'] == '52f63c944ded7a651da871524d23a345b606424d'
    assert new_doc['commit'] == '00bf0f916a549f5e858cb39dd91a149071fd5181'
    tables = []
    for folder, doc, count in ((ROOT, old_doc, 1019), (REVIEW, new_doc, 1029)):
        manifest = doc['source_sha256']; assert len(manifest) == count and inventory(folder) == set(manifest)
        table = {}
        for name, expected in sorted(manifest.items()):
            assert not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name and ':' not in name
            raw = read(folder / name); assert sha(raw) == expected, name
            table[name] = {'raw_sha256': expected, 'content_sha256': sha(A.canonical(raw, name))}
        tables.append(table)
    old, new = tables; assert set(old) <= set(new)
    rows = []; eol = []
    for name, value in sorted(new.items()):
        previous = old.get(name)
        if previous is not None and previous['content_sha256'] == value['content_sha256']:
            if previous['raw_sha256'] != value['raw_sha256']:
                eol.append({'path': name, 'old_raw_sha256': previous['raw_sha256'], 'new_raw_sha256': value['raw_sha256'], 'content_sha256': value['content_sha256']})
            continue
        rows.append({'path': name, 'classification': 'added' if previous is None else 'modified',
                     'old_raw_sha256': previous['raw_sha256'] if previous else None,
                     'old_content_sha256': previous['content_sha256'] if previous else None,
                     'new_raw_sha256': value['raw_sha256'], 'new_content_sha256': value['content_sha256']})
    assert set(REASONS) == {row['path'] for row in rows}
    summary = A.check_reviewed_delta(old, new, rows)
    core = {name: {'old_raw_sha256': old[name]['raw_sha256'], 'new_raw_sha256': new[name]['raw_sha256'],
                   'canonical_content_sha256': new[name]['content_sha256'],
                   'raw_byte_exact': old[name]['raw_sha256'] == new[name]['raw_sha256'],
                   'canonical_content_exact': old[name]['content_sha256'] == new[name]['content_sha256']} for name in CORES}
    assert all(value['canonical_content_exact'] for value in core.values())
    assert core['src/model.gd']['raw_byte_exact'] and core['src/scene3d.gd']['raw_byte_exact']
    assert not core['src/source_bone_bindings.gd']['raw_byte_exact']
    result = {'format': 'has_reviewed52_to_qualified_Neon_delta_1', 'review_status': 'DRAFT_NOT_ROOT_REVIEWED',
        'activation_status': 'NOFULL_OR_MERGE_ACTIVATION', 'reasons_status': 'DRAFT_EACH_REASON_REQUIRES_ROOT_CONTENT_REVIEW',
        'old_manifest_commit': old_doc['commit'], 'candidate_manifest_commit': new_doc['commit'],
        'future_merged_main_revision': None, 'old_manifest_path': str(OLD_MAP), 'old_manifest_sha256': OLD_PIN,
        'candidate_immutable_before_path': str(NEW_MAP), 'candidate_immutable_before_sha256': NEW_PIN,
        'sealed_admission_core_sha256': CORE_SHA, 'canonicalization': 'unchanged admission_core.canonical',
        'rows': rows, 'reasons': {name: 'DRAFT: ' + reason for name, reason in sorted(REASONS.items())},
        'exact_delta_schema_and_byte_map_join': summary, 'raw_EOL_only_differences_excluded_from_delta_rows': eol,
        'counts': {'added': sum(row['classification'] == 'added' for row in rows), 'modified_content': sum(row['classification'] == 'modified' for row in rows),
                   'raw_EOL_only': len(eol), 'unchanged_raw': len(old) - sum(row['classification'] == 'modified' for row in rows) - len(eol)},
        'old52_to_candidate_core_status': core, 'native_to52_exact_core_guard_separate_and_not_reopened_here': True,
        'current_main_functional_bytes_join_actual52_manifest': True, 'candidate_bytes_join_active_immutable_before_only': True,
        'full_result_release_merge_copy_or187_qualified': False, 'original_source_or_guard_mutated': False,
        'other_active_outputs_native_originals_Git_or_processes_read': False, 'reproducer_sha256': sha(read(Path(__file__)))}
    for folder, doc in ((ROOT, old_doc), (REVIEW, new_doc)):
        assert inventory(folder) == set(doc['source_sha256'])
        assert all(sha(read(folder / name)) == expected for name, expected in doc['source_sha256'].items())
    assert sha(read(CORE)) == CORE_SHA and sha(read(OLD_MAP)) == OLD_PIN and sha(read(NEW_MAP)) == NEW_PIN
    if args.check:
        assert A.parse(read(OUTPUT)) == result, 'Draft differs from exact reproduction'
    else:
        with OUTPUT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'draft': str(OUTPUT), 'sha256': sha(read(OUTPUT)), 'counts': result['counts'],
                      'delta_rows': len(rows), 'sealed_checker_accepted_exact_schema': True,
                      'review_status': result['review_status'], 'activation_status': result['activation_status']}))


if __name__ == '__main__': main()
