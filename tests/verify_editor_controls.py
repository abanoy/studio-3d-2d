"""Current-checkout editor geometry, face-window and handle regressions.
The existing rotation verifier remains a separate canonical Full group.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import stat
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Shared ordinary current-checkout command/receipt/source-preservation protocol.
# No experimental coordinator, historical receipt or immutable baseline is used.
from verify_camera_interactions import need, identity, source_inputs, sources_unchanged, run_case
from run import configure_private_display
from test_helper_morphs import shape_fixture


def check_report(case, result, filename):
    value = json.loads((case/filename).read_bytes())
    need(value == result['report'], 'Editor marker and saved result differ')
    return value


def face_contract(value):
    rows = value.get('resize_cases')
    need(value.get('checks') == 36 and value.get('lifecycle_checks') == 6
         and type(rows) is list and len(rows) == 2
         and [row.get('interface_scale') for row in rows] == [1.0, 1.5]
         and all(row.get('controlled_late_size_signal') is True for row in rows),
         'Face resize/DPI/lifecycle scope mismatch')


def handle_contract(value):
    rows = value.get('cases')
    need(value.get('checks') == 38 and value.get('historical_assertions') == 27
         and value.get('visible_geometry_assertions') == 8 and value.get('clipped_arc_assertions') == 3
         and value.get('pixel_requirement') == 'six_visible_white180_zero_white205'
         and type(rows) is list and len(rows) == 4
         and [(row.get('window'), row.get('interface_scale')) for row in rows]
         == [('(1600, 1000)', 1.0), ('(1600, 1000)', 1.5), ('(3440, 1440)', 1.0), ('(3440, 1440)', 1.5)]
         and all(row.get('ring_pixel_hits') == 6 and row.get('wrong_band_hits') == 0 for row in rows),
         'Four exact visible-arc handle cases required')
    for row in rows:
        sample = row['measurement']
        need(sample.get('metric_view_screen_pixels') == 180 and sample.get('metric_hit_pixels') == 20
             and sample.get('near_scene_contains') is True and sample.get('near_started_drag') is True
             and sample.get('far_scene_contains') is True, 'Physical handle/pick contract failed')
    clipped = rows[1]['measurement']['clipped_test']
    need(clipped.get('assertions') == 3 and clipped.get('white_at_180') is False
         and clipped.get('scene_contains') is False and clipped.get('started_drag') is False
         and clipped.get('minimum_ring_distance_screen', 999) < 20,
         'Compact clipped-arc absence/refusal controls required')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', choices=('geometry', 'face', 'handles', 'all'), default='all')
    parser.add_argument('--isolated-display')
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    if os.name != 'nt' and options.scope != 'geometry':
        if sys.platform != 'linux' or not options.isolated_display:
            parser.error('Graphical checks require an explicitly provisioned private --isolated-display; no shared fallback')
        configure_private_display(options.isolated_display)
    folder = (options.output or ROOT/'output/editor-controls'/str(time.time_ns())).resolve()
    need(folder.is_relative_to((ROOT/'output').resolve()) and not folder.exists(), 'Choose a new directory inside output')
    for parent in folder.parents:
        if parent.exists():
            info = parent.lstat()
            need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0)&0x400, 'Output alias refused')
    folder.mkdir(parents=True, exist_ok=False)
    frozen = source_inputs()
    result = {'format': 'has_current_editor_controls_verification_1', 'status': 'FAIL',
              'scope': options.scope, 'cases': [], 'whole_full_claimed': False,
              'owner_assets_read': False, 'sourceio_or_conversion_requested': False}
    original_fixture = None
    primary = None
    try:
        if options.scope in ('geometry', 'all'):
            result['cases'].append(run_case(folder, 'geometry', 'tests/editor_geometry_unit.gd',
                                            'EDITOR_GEOMETRY_UNIT ', 37, [], headless=True, timeout=30))
        if options.scope in ('face', 'all'):
            fixture_folder = folder/'Fixtures'
            fixture_folder.mkdir()
            fixture = fixture_folder/'shape.glb'
            shape_fixture(fixture)
            original_fixture = (fixture, identity(fixture.lstat()), hashlib.sha256(fixture.read_bytes()).hexdigest())
            case = run_case(folder, 'face', 'tests/face_window_layout_smoke.gd',
                            'FACE_WINDOW_LAYOUT ', 36, [str(fixture)], headless=False, timeout=110)
            face_contract(check_report(folder/'face', case, 'face-window-layout-result.json'))
            result['cases'].append(case)
        if options.scope in ('handles', 'all'):
            case = run_case(folder, 'handles', 'tests/pose_handle_size_smoke.gd',
                            'HANDLE_SIZE_SMOKE ', 38, [], headless=False, timeout=140)
            handle_contract(check_report(folder/'handles', case, 'handle-size-result.json'))
            for index in range(4):
                image = (folder/'handles'/('handle-case-'+str(index)+'.png')).read_bytes()
                need(len(image) >= 24 and image[:8] == b'\x89PNG\r\n\x1a\n'
                     and int.from_bytes(image[16:20], 'big') > 0 and int.from_bytes(image[20:24], 'big') > 0,
                     'Actual handle screenshots required')
            result['cases'].append(case)
        expected = {'geometry': 37, 'face': 36, 'handles': 38, 'all': 111}[options.scope]
        result['checks'] = sum(row['checks'] for row in result['cases'])
        need(result['checks'] == expected, 'All requested editor controls must complete')
        result['status'] = 'PASS'
    except BaseException as error:
        primary = error
        result['error_type'] = type(error).__name__
        result['error'] = str(error)
    finally:
        result['source_preservation_failures'] = sources_unchanged(frozen)
        result['all_admitted_sources_unchanged'] = not result['source_preservation_failures']
        result['generated_fixture_preserved'] = True
        if original_fixture:
            fixture, stamp, digest = original_fixture
            try:
                result['generated_fixture_preserved'] = (identity(fixture.lstat()) == stamp
                    and hashlib.sha256(fixture.read_bytes()).hexdigest() == digest and identity(fixture.lstat()) == stamp)
            except OSError:
                result['generated_fixture_preserved'] = False
        if not result['all_admitted_sources_unchanged'] or not result['generated_fixture_preserved']:
            result['status'] = 'FAIL'
        (folder/'verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'status': result['status'], 'checks': result.get('checks'),
                          'scope': options.scope, 'result': str(folder/'verification.json')}))
    if primary is not None:
        raise primary
    need(result['status'] == 'PASS', 'Editor source/fixture preservation failed')


if __name__ == '__main__':
    main()
