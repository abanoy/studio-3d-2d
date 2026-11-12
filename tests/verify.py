"""Run real Godot + FFmpeg checks; Windows graphical tests use a private desktop."""
from pathlib import Path
import array
import hashlib
import json
import math
import os
import shutil
import subprocess
import struct
import sys
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command


def run(args, timeout=120, **kwargs):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout, **kwargs)
    if result.returncode:
        raise RuntimeError(f"Exit {result.returncode}: {args}\n{result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


def main():
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    results = {}
    native_fixture_log = run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_native_fixture_plans.py'])
    (output / 'native-fixture-plans-unit.log').write_text(native_fixture_log, encoding='utf-8')
    results['native_fixture_plans'] = {'exit': 0}
    krita_inventory_log = run([sys.executable, 'tests/test_krita_assets.py'])
    (output / 'krita-inventory-unit.log').write_text(krita_inventory_log, encoding='utf-8')
    results['krita_inventory'] = {'exit': 0}
    krita_preparation_log = run([sys.executable, 'tests/test_krita_preparation.py'])
    (output / 'krita-preparation-unit.log').write_text(krita_preparation_log, encoding='utf-8')
    results['krita_preparation'] = {'exit': 0}
    origin_log = run([sys.executable, 'tests/test_drawing_origin.py'])
    (output / 'drawing-origin-python.log').write_text(origin_log, encoding='utf-8')
    corpus = output / 'drawing-origin-corpus.json'
    run([sys.executable, 'tests/test_drawing_origin.py', '--corpus', str(corpus)])
    origin_domain = run(command('tests/drawing_origin_unit.gd', True, extra=['--', str(corpus)]))
    raster_domain = run(command('tests/raster_clip_unit.gd', True, extra=['--', str(output / ('raster-domain-' + str(time.time_ns())))]))
    for label, log in [('drawing-origin-domain', origin_domain), ('raster-clip-domain', raster_domain)]:
        if any(bad in log for bad in ['SCRIPT ERROR', 'FAIL ', '"failures":1']):raise RuntimeError(log)
        (output / (label + '.log')).write_text(log, encoding='utf-8')
    results['drawing_origin'] = {'exit': 0}
    krita_import_log = run([sys.executable, '-u', 'tests/verify_krita_import.py'], timeout=500)
    (output / 'krita-import-suite.log').write_text(krita_import_log, encoding='utf-8')
    results['krita_import'] = json.loads((output / 'krita-import-verification.json').read_text(encoding='utf-8'))
    body_pose_python = run([sys.executable, 'tests/test_pose_library.py'])
    (output / 'body-pose-python.log').write_text(body_pose_python, encoding='utf-8')
    body_pose_corpus = output / 'body-pose-corpus.json'
    run([sys.executable, 'tests/test_pose_library.py', '--corpus', str(body_pose_corpus)])
    body_pose_domain = run(command('tests/pose_library_unit.gd', True, extra=['--', str(body_pose_corpus)]))
    if 'POSE_LIBRARY_UNIT ' not in body_pose_domain or any(x in body_pose_domain for x in ['ERROR:', 'FAIL ']):raise RuntimeError(body_pose_domain)
    (output / 'body-pose-domain.log').write_text(body_pose_domain, encoding='utf-8')
    for name, wrapper, report in [('body_pose_library','verify_pose_library.py','body-pose-library-verification.json'),('body_pose_native','verify_pose_library_native.py','body-pose-native-verification.json')]:
        log = run([sys.executable, '-u', 'tests/' + wrapper], timeout=300)
        (output / (name + '-suite.log')).write_text(log, encoding='utf-8')
        results[name] = json.loads((output / report).read_text(encoding='utf-8'))
    fixtures = output / "fixtures"
    fixtures.mkdir(exist_ok=True)
    raw = array.array("h", (int(16000 * math.sin(2 * math.pi * 1000 * n / 44100)) for n in range(22050)))
    if sys.byteorder != "little": raw.byteswap()
    with wave.open(str(fixtures / "voice — тест.wav"), "wb") as wav:
        wav.setparams((1, 2, 44100, 0, "NONE", "not compressed"))
        wav.writeframes(raw.tobytes())
    payload = b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 3, 1, 44100, 176400, 4, 32) + b"data" + struct.pack("<I", 400) + bytes(400)
    (fixtures / "float.wav").write_bytes(b"RIFF" + struct.pack("<I", len(payload)) + payload)
    tests = [("unit", "tests/unit.gd", True, "UNIT 24 checks; failures=0"),
             ("motion_parts", "tests/motion_parts_unit.gd", True, 'MOTION_PARTS {"checks":40,"failures":0}'),
             ("motion_helper_edits", "tests/motion_helper_edits_unit.gd", True, 'MOTION_HELPER_EDITS_UNIT {"checks":16,"failures":0}'),
             ("opaque_order", "tests/opaque_order_unit.gd", True, 'OPAQUE_ORDER {"checks":9,"failures":0}'),
             ("required_extensions", "tests/required_extensions_unit.gd", True, 'REQUIRED_EXTENSIONS {"checks":9,"failures":0}'),
             ("contact_bend", "tests/contact_bend_unit.gd", True, 'CONTACT_BEND {"checks":16,"failures":0}'),
             ("spikes", "tests/spikes.gd", False, "SPIKES failures=0"),
             ("editor", None, False, '"failures":0'),
             ("export_failures", "tests/export_failures.gd", False, "EXPORT_FAILURES failures=0"),
             ("audio_editor", None, False, '"failures":0'),
             ("audio_dummy", None, False, 'AUDIO_DUMMY failures=0'),
             ("ui", None, False, 'UI_SMOKE '),
             ("recovery_write", None, False, "RECOVERY_WRITE failures=0"),
             ("recovery", None, False, "RECOVERY_SMOKE "),
             ("pose", None, False, "POSE_SMOKE "),
             ("autokey", "tests/autokey_smoke.gd", False, "AUTOKEY_SMOKE "),
             ("new_scene", "tests/new_scene_smoke.gd", False, "NEW_SCENE_SMOKE "),
             ("world_selection", "tests/world_selection_smoke.gd", False, "WORLD_SELECTION_SMOKE "),
             ("world_document", "tests/world_document_smoke.gd", False, "WORLD_DOCUMENT_SMOKE "),
             ("world_runtime", "tests/world_runtime_smoke.gd", False, "WORLD_RUNTIME_SMOKE "),
             ("world_edit", "tests/world_edit_smoke.gd", False, "WORLD_EDIT_SMOKE "),
             ("world_workflow", "tests/world_workflow_smoke.gd", False, "WORLD_WORKFLOW_SMOKE "),
             ("object_timing", "tests/object_timing_smoke.gd", False, "OBJECT_TIMING "),
             ("bone_labels", "tests/bone_labels_smoke.gd", False, "BONE_LABELS "),
             ("animation_clips_unit", "tests/animation_clips_unit.gd", True, "ANIMATION_CLIPS_UNIT "),
             ("animation_clips", "tests/animation_clips_smoke.gd", False, "ANIMATION_CLIPS_SMOKE "),
             ("visibility", "tests/visibility_smoke.gd", False, "VISIBILITY_SMOKE "),
             ("animated_channels", "tests/animated_channels_smoke.gd", False, "ANIMATED_CHANNELS "),
             ("limb_ik", "tests/limb_ik_smoke.gd", False, "LIMB_IK "),
             ("secondary_motion", "tests/secondary_motion_smoke.gd", False, "SECONDARY_MOTION "),
             ("fan_motion", "tests/fan_motion_smoke.gd", False, "FAN_MOTION "),
             ("physics", "tests/physics_smoke.gd", False, "PHYSICS_SMOKE "),
             ("physics_contacts", "tests/physics_contacts_smoke.gd", False, "PHYSICS_CONTACTS "),
             ("physics_props", "tests/physics_props_smoke.gd", False, "PHYSICS_PROPS "),
             ("physics_recording_unit", "tests/physics_recording_unit.gd", True, "PHYSICS_RECORDING_UNIT "),
             ("physics_recording", "tests/physics_recording_smoke.gd", False, "PHYSICS_RECORDING ")]
    launch_args = {
        "editor": ["--", "--smoke"],
        "ui": ["--", "--ui-smoke"],
        "audio_editor": ["--", "--audio-smoke"],
        "audio_dummy": ["--audio-driver", "Dummy", "--", "--audio-smoke", "--dummy-audio-test"],
        "recovery_write": ["--", "--recovery-smoke", "--recovery-write"],
        "recovery": ["--", "--recovery-smoke"],
        "pose": ["--", "--pose-smoke"],
    }
    for name, script, headless, marker in tests:
        start = time.perf_counter()
        extra = launch_args.get(name, [])
        # Existing film regressions deliberately use the sample, not implicit startup content.
        if script is None: extra = extra + ["--demo-room"]
        text = run(command(script, headless, extra))
        (output / f"{name}-stdout.log").write_text(text, encoding="utf-8")
        if name in ("physics", "physics_contacts", "physics_props", "physics_recording_unit", "physics_recording", "secondary_motion", "fan_motion") and '"failures":0' not in text:
            raise RuntimeError(f"physics failed; inspect output/physics-stdout.log\n{text}")
        if marker not in text or any(error in text for error in ("SCRIPT ERROR", "SHADER ERROR", "Shader compilation failed", "FAIL ", "ObjectDB instances leaked")) or (name in ("ui", "recovery", "pose", "autokey", "new_scene", "world_selection", "world_document", "world_runtime", "world_edit", "world_workflow", "object_timing", "bone_labels", "animation_clips_unit", "animation_clips", "visibility", "animated_channels", "limb_ik") and '"failures":0' not in text):
            raise RuntimeError(f"{name} failed; inspect output/{name}-stdout.log\n{text}")
        results[name] = {"exit": 0, "seconds": round(time.perf_counter() - start, 3)}
        print(f"PASS {name}: {results[name]['seconds']}s")

    workspace_log = run([sys.executable, '-u', 'tests/verify_workspace_controls.py'], timeout=310)
    (output / 'workspace-controls-suite.log').write_text(workspace_log, encoding='utf-8')
    results['workspace_controls'] = json.loads((output / 'workspace-controls-verification.json').read_text(encoding='utf-8'))
    run([sys.executable, '-u', 'tests/verify_workspace_resize.py'], timeout=310)
    results['workspace_resize'] = json.loads((output / 'workspace-resize-verification.json').read_text(encoding='utf-8'))
    run([sys.executable, '-u', 'tests/verify_workspace_docking.py'], timeout=350)
    results['workspace_docking'] = json.loads((output / 'workspace-docking-verification.json').read_text(encoding='utf-8'))
    run([sys.executable, '-u', 'tests/verify_workspace_nested.py'], timeout=350)
    results['workspace_nested'] = json.loads((output / 'workspace-nested-verification.json').read_text(encoding='utf-8'))
    run([sys.executable, '-u', 'tests/verify_fan_flutter.py'], timeout=250)
    results['fan_flutter'] = json.loads((output / 'fan-flutter-verification.json').read_text(encoding='utf-8'))
    print('PASS middle-click tools, non-blocking editing panels, movable/resizable workspace and readable selection text')

    shortcuts_log = run([sys.executable, '-u', 'tests/verify_shortcuts.py'], timeout=500)
    (output / 'shortcuts-suite.log').write_text(shortcuts_log, encoding='utf-8')
    results['shortcuts'] = json.loads((output / 'shortcuts-verification.json').read_text(encoding='utf-8'))
    print('PASS personal keyboard remapping, native capture, conflict guards, text safety and fresh preferences')

    numeric_camera_log = run([sys.executable, '-u', 'tests/verify_camera_transform.py'], timeout=500)
    (output / 'numeric-camera-suite.log').write_text(numeric_camera_log, encoding='utf-8')
    results['numeric_camera'] = json.loads((output / 'camera-transform-verification.json').read_text(encoding='utf-8'))
    print('PASS numeric temporary camera view, explicit keys, stale draft guards, cold HAS and exact movie')

    # Composite suite launches four separately bounded GPU jobs serially. Do not
    # apply a single-engine deadline to their combined runtime on a busy machine.
    helper_log = run([sys.executable, '-u', 'tests/verify_secondary_helpers.py'], timeout=600)
    (output / 'secondary-helpers-suite.log').write_text(helper_log, encoding='utf-8')
    results['secondary_helpers'] = json.loads((output / 'secondary-helpers-verification.json').read_text(encoding='utf-8'))
    print('PASS reviewed weighted helpers, native bindings, HAS and movie')
    morph_log = run([sys.executable, '-u', 'tests/verify_helper_morphs.py'])
    (output / 'helper-morphs-suite.log').write_text(morph_log, encoding='utf-8')
    results['helper_morphs'] = json.loads((output / 'helper-morphs-verification.json').read_text(encoding='utf-8'))
    print('PASS experimental shape-aware helper geometry and real GPU comparison')
    shape_log = run([sys.executable, '-u', 'tests/verify_source_shapes.py'], timeout=180)
    (output / 'source-shapes-suite.log').write_text(shape_log, encoding='utf-8')
    results['source_shapes'] = json.loads((output / 'source-shapes-verification.json').read_text(encoding='utf-8'))
    print('PASS imported shapes, old appearance compatibility, review, HAS and movie')
    base_log = run([sys.executable, '-u', 'tests/verify_base_shapes.py'], timeout=240)
    (output / 'base-shapes-suite.log').write_text(base_log, encoding='utf-8')
    results['base_shapes'] = json.loads((output / 'base-shapes-verification.json').read_text(encoding='utf-8'))
    print('PASS editable base shapes, native channels, transactional Undo, HAS and movie')
    animated_shape_log = run([sys.executable, '-u', 'tests/verify_shape_animation.py'], timeout=240)
    (output / 'shape-animation-suite.log').write_text(animated_shape_log, encoding='utf-8')
    results['shape_animation'] = json.loads((output / 'shape-animation-verification.json').read_text(encoding='utf-8'))
    print('PASS animated shapes, native GPU, blocks, clipboard, helper capture, recovery and movie')
    catalogue_log = run([sys.executable, '-u', 'tests/verify_shape_catalog.py'], timeout=240)
    (output / 'shape-catalogue-suite.log').write_text(catalogue_log, encoding='utf-8')
    results['shape_catalogue'] = json.loads((output / 'shape-catalog-verification.json').read_text(encoding='utf-8'))
    print('PASS control area estimates, manual organization, native identity, Undo, HAS and movie')
    study_log = run([sys.executable, '-u', 'tests/verify_shape_study.py'], timeout=280)
    (output / 'shape-study-suite.log').write_text(study_log, encoding='utf-8')
    results['shape_study'] = json.loads((output / 'shape-study-verification.json').read_text(encoding='utf-8'))
    print('PASS cancellable neutral deform study, explicit adoption, Undo, native identity, HAS and movie')
    comparison_log = run([sys.executable, '-u', 'tests/verify_shape_comparison.py'], timeout=260)
    (output / 'shape-comparison-suite.log').write_text(comparison_log, encoding='utf-8')
    results['shape_comparison'] = json.loads((output / 'shape-comparison-verification.json').read_text(encoding='utf-8'))
    print('PASS isolated neutral/deformed views, exact document isolation and pending-readback teardown')
    preset_log = run([sys.executable, '-u', 'tests/verify_expression_presets.py'], timeout=260)
    (output / 'expression-presets-suite.log').write_text(preset_log, encoding='utf-8')
    results['expression_presets'] = json.loads((output / 'expression-presets-verification.json').read_text(encoding='utf-8'))
    print('PASS embedded compound expression poses, native VRM bindings, Undo, HAS and movie')
    mmd_group_log = run([sys.executable, '-u', 'tests/verify_mmd_groups.py'], timeout=380)
    (output / 'mmd-groups-suite.log').write_text(mmd_group_log, encoding='utf-8')
    results['mmd_groups'] = json.loads((output / 'mmd-groups-verification.json').read_text(encoding='utf-8'))
    print('PASS native PMX compound/nested expressions through shared editable deform keys')
    height_log = run([sys.executable, '-u', 'tests/verify_character_height.py'], timeout=380)
    (output / 'character-height-suite.log').write_text(height_log, encoding='utf-8')
    results['character_height'] = json.loads((output / 'character-height-verification.json').read_text(encoding='utf-8'))
    print('PASS optional height review, partial/proportion guards, native physics, HAS and movie')
    map_log = run([sys.executable, '-u', 'tests/verify_map_calibration.py'], timeout=380)
    (output / 'map-calibration-suite.log').write_text(map_log, encoding='utf-8')
    results['map_calibration'] = json.loads((output / 'map-calibration-verification.json').read_text(encoding='utf-8'))
    print('PASS known-distance map picking, isolated size preview, anchor, Undo, HAS and movie')
    body_curve_log = run([sys.executable, '-u', 'tests/verify_body_curves.py'], timeout=240)
    (output / 'body-curves-suite.log').write_text(body_curve_log, encoding='utf-8')
    results['body_curves'] = json.loads((output / 'body-curves-verification.json').read_text(encoding='utf-8'))
    print('PASS independent body foundation and native GPU comparison')
    body_animation_log = run([sys.executable, '-u', 'tests/verify_body_animation.py'], timeout=240)
    (output / 'body-animation-suite.log').write_text(body_animation_log, encoding='utf-8')
    results['body_animation'] = json.loads((output / 'body-animation-verification.json').read_text(encoding='utf-8'))
    print('PASS normal independent body editing, native HAS, history, recovery and direct movie sampling')
    lighting_log = run([sys.executable, '-u', 'tests/verify_lighting.py'], timeout=240)
    (output / 'lighting-suite.log').write_text(lighting_log, encoding='utf-8')
    results['lighting'] = json.loads((output / 'lighting-verification.json').read_text(encoding='utf-8'))
    print('PASS project lighting, source materials, fades, native rigs, HAS and direct movie')
    live_appearance_log = run([sys.executable, '-u', 'tests/verify_live_appearance.py'], timeout=150)
    (output / 'live-appearance-suite.log').write_text(live_appearance_log, encoding='utf-8')
    results['live_appearance'] = json.loads((output / 'live-appearance-verification.json').read_text(encoding='utf-8'))
    print('PASS live hair retains project lighting and inherited parent fades')
    import_physics_log = run([sys.executable, '-u', 'tests/verify_import_physics.py'], timeout=240)
    (output / 'import-physics-suite.log').write_text(import_physics_log, encoding='utf-8')
    results['import_physics'] = json.loads((output / 'import-physics-verification.json').read_text(encoding='utf-8'))
    print('PASS interactive default physics, live body/hair peers, native rigs, Record and portable movie')
    pose_bounds_log = run([sys.executable, '-u', 'tests/verify_pose_bounds.py'], timeout=240)
    (output / 'pose-bounds-suite.log').write_text(pose_bounds_log, encoding='utf-8')
    results['pose_bounds'] = json.loads((output / 'pose-bounds-verification.json').read_text(encoding='utf-8'))
    print('PASS current skin and morph framing, live physics, native rigs and explicit shot isolation')
    camera_range_log = run([sys.executable, '-u', 'tests/verify_camera_range.py'], timeout=240)
    (output / 'camera-range-suite.log').write_text(camera_range_log, encoding='utf-8')
    results['camera_range'] = json.loads((output / 'camera-range-verification.json').read_text(encoding='utf-8'))
    print('PASS shot projection isolation, legacy cameras, native references, portable HAS and movie')
    sampler_log = run([sys.executable, '-u', 'tests/verify_color_sampler.py'], timeout=220)
    (output / 'color-sampler-suite.log').write_text(sampler_log, encoding='utf-8')
    results['color_sampler'] = json.loads((output / 'color-sampler-verification.json').read_text(encoding='utf-8'))
    print('PASS guide-free color sampling, native skin pixels, stale requests, safe teardown and portable movie')
    foot_log = run([sys.executable, '-u', 'tests/verify_foot_hold.py'], timeout=180)
    (output / 'foot-hold-suite.log').write_text(foot_log, encoding='utf-8')
    results['foot_hold'] = json.loads((output / 'foot-hold-verification.json').read_text(encoding='utf-8'))
    print('PASS body posing with held feet, native rigs, atomic Undo, portable HAS and movie; continuous playback contacts remain open')
    contacts_log = run([sys.executable, '-u', 'tests/verify_foot_contacts.py'], timeout=180)
    (output / 'foot-contacts-suite.log').write_text(contacts_log, encoding='utf-8')
    results['foot_contacts_experiment'] = json.loads((output / 'foot-contacts-verification.json').read_text(encoding='utf-8'))
    print('PASS continuous-contact foundation; versioned integration is checked separately below')
    # Run the complete contact workflow in dependency order. Persistence creates
    # a fresh native fixture consumed by binding/identity/selection/viewport tests.
    # These local integration suites require the documented owner asset samples.
    contact_suites = [
        ('animation', 180), ('editor', 180), ('clipboard', 200),
        ('physics', 240), ('parent', 180), ('correction', 200),
        ('persistence', 1000), ('bindings', 220), ('identity', 360),
        ('selection', 240), ('transform', 240), ('viewport', 340),
    ]
    for name, deadline in contact_suites:
        contact_text = run([sys.executable, '-u', f'tests/verify_contact_{name}.py'], timeout=deadline)
        (output / f'contact-{name}-suite.log').write_text(contact_text, encoding='utf-8')
        report = json.loads((output / f'contact-{name}-verification.json').read_text(encoding='utf-8'))
        if name == 'persistence':
            assert report['writer']['failures'] == 0 and all(row['failures'] == 0 for row in report['readers'].values())
        else:
            assert report['failures'] == 0
        if name == 'viewport':
            assert report['reader']['failures'] == 0
        results[f'contact_{name}'] = report
        print(f'PASS contact {name}: native shared-model integration')
        if name in ('clipboard', 'physics'):
            component_text = run([sys.executable, '-u', f'tests/verify_contact_{name}.py', '--components'], timeout=deadline)
            (output / f'component-contact-{name}-suite.log').write_text(component_text, encoding='utf-8')
            results[f'component_contact_{name}'] = json.loads((output / f'component-contact-{name}-verification.json').read_text(encoding='utf-8'))
            assert results[f'component_contact_{name}']['failures'] == 0


    multi_audio_log = run([sys.executable, '-u', 'tests/verify_multi_audio.py'], timeout=1000)
    (output / 'multi-audio-suite.log').write_text(multi_audio_log, encoding='utf-8')
    results['multi_audio'] = json.loads((output / 'multi-audio-verification.json').read_text(encoding='utf-8'))
    print('PASS independent multi-clip sound, master clock, native HAS/recovery/lesson and measured movie mix')
    duration_log = run([sys.executable, '-u', 'tests/verify_project_duration.py'], timeout=1000)
    (output / 'project-duration-suite.log').write_text(duration_log, encoding='utf-8')
    results['project_duration'] = json.loads((output / 'project-duration-verification.json').read_text(encoding='utf-8'))
    assert results['project_duration']['failures'] == 0 and len(results['project_duration']['fresh_readers']) == 4
    print('PASS scene length, protected shortening, exact audio Undo and fresh project readers')
    motion_suites = [
        ('assist', 'tests/verify_motion_assist.py', 'motion-assist-verification.json', 90),
        ('tracks', 'tests/verify_motion_assist_tracks.py', 'motion-assist-tracks-verification.json', 90),
        ('native_preview', 'tests/verify_motion_assist_native.py', 'motion-assist-native-verification.json', 240),
        ('model', 'tests/verify_motion_animation.py', 'motion-animation-unit-verification.json', 90),
        ('editor', 'tests/verify_motion_animation_app.py', 'motion-animation-app-verification.json', 360),
    ]
    for name, script, report_name, deadline in motion_suites:
        motion_text = run([sys.executable, '-u', script], timeout=deadline)
        (output / f'motion-{name}-suite.log').write_text(motion_text, encoding='utf-8')
        report = json.loads((output / report_name).read_text(encoding='utf-8'))
        assert report['failures'] == 0
        if name == 'editor': assert report['reader']['failures'] == 0
        results[f'motion_{name}'] = report
        print(f'PASS motion {name}: derived assistance and authoritative controls')
    opacity_log = run([sys.executable, '-u', 'tests/verify_opacity.py'], timeout=220)
    (output / 'opacity-suite.log').write_text(opacity_log, encoding='utf-8')
    results['opacity'] = json.loads((output / 'opacity-verification.json').read_text(encoding='utf-8'))
    print('PASS non-destructive layer opacity, dirty-region cache, native saves/recovery and movie')
    brush_log = run([sys.executable, '-u', 'tests/verify_brush_opacity.py'], timeout=380)
    (output / 'brush-opacity-suite.log').write_text(brush_log, encoding='utf-8')
    results['brush_opacity'] = json.loads((output / 'brush-opacity-verification.json').read_text(encoding='utf-8'))
    print('PASS even translucent strokes, gentle eraser, pixel Undo, cold HAS and exact movie')
    pressure_log = run([sys.executable, '-u', 'tests/verify_brush_pressure.py'], timeout=400)
    (output / 'brush-pressure-suite.log').write_text(pressure_log, encoding='utf-8')
    results['brush_pressure'] = json.loads((output / 'brush-pressure-verification.json').read_text(encoding='utf-8'))
    print('PASS native pressure-size input, independent taper reference, cold HAS and exact movie')
    layers_log = run([sys.executable, '-u', 'tests/verify_layers.py'], timeout=200)
    (output / 'layers-suite.log').write_text(layers_log, encoding='utf-8')
    results['layers'] = json.loads((output / 'layers-verification.json').read_text(encoding='utf-8'))
    print('PASS editable drawing layer order, names, removal, undo, portable recovery and movie')
    onion_log = run([sys.executable, '-u', 'tests/verify_onion.py'], timeout=200)
    (output / 'onion-suite.log').write_text(onion_log, encoding='utf-8')
    results['onion'] = json.loads((output / 'onion-verification.json').read_text(encoding='utf-8'))
    print('PASS editor-only onion guides, exposure selection, texture cache, GPU stacking and portable movie')
    fill_log = run([sys.executable, '-u', 'tests/verify_fill.py'], timeout=240)
    (output / 'fill-suite.log').write_text(fill_log, encoding='utf-8')
    results['fill'] = json.loads((output / 'fill-verification.json').read_text(encoding='utf-8'))
    print('PASS independent drawing fill, real background worker, spill preview, undo and portable movie')
    gaps_log = run([sys.executable, '-u', 'tests/verify_fill_gaps.py'], timeout=500)
    (output / 'fill-gaps-suite.log').write_text(gaps_log, encoding='utf-8')
    results['fill_gaps'] = json.loads((output / 'fill-gaps-verification.json').read_text(encoding='utf-8'))
    print('PASS virtual gap closing, independent morphology oracle, preview/Undo, cold HAS and exact movie')
    expand_log = run([sys.executable, '-u', 'tests/verify_fill_expand.py'], timeout=500)
    (output / 'fill-expand-suite.log').write_text(expand_log, encoding='utf-8')
    results['fill_expand'] = json.loads((output / 'fill-expand-verification.json').read_text(encoding='utf-8'))
    print('PASS previewed under-ink fill growth, independent pixel oracle, Undo, cold HAS and exact movie')
    connections_log = run([sys.executable, '-u', 'tests/verify_fill_connections.py'], timeout=500)
    (output / 'fill-connections-suite.log').write_text(connections_log, encoding='utf-8')
    results['fill_connections'] = json.loads((output / 'fill-connections-verification.json').read_text(encoding='utf-8'))
    print('PASS selectable edge/corner fill, exhaustive independent graph oracle, cold HAS and movie')
    palette_log = run([sys.executable, '-u', 'tests/verify_palette.py'], timeout=500)
    (output / 'palette-suite.log').write_text(palette_log, encoding='utf-8')
    results['palette'] = json.loads((output / 'palette-verification.json').read_text(encoding='utf-8'))
    print('PASS named project swatches, exact color reuse, Undo, cold HAS/recovery/lesson and movie')
    drawing_history_log = run([sys.executable, '-u', 'tests/verify_drawing_history.py'], timeout=400)
    (output / 'drawing-history-suite.log').write_text(drawing_history_log, encoding='utf-8')
    results['drawing_history'] = json.loads((output / 'drawing-history-verification.json').read_text(encoding='utf-8'))
    print('PASS independent drawing Undo/Redo preserves live ragdolls, overlay, cold HAS and movie')
    selection_log = run([sys.executable, '-u', 'tests/verify_drawing_selection.py'], timeout=500)
    (output / 'drawing-selection-suite.log').write_text(selection_log, encoding='utf-8')
    results['drawing_selection'] = json.loads((output / 'drawing-selection-verification.json').read_text(encoding='utf-8'))
    print('PASS independent raster selection/move/copy, live physics, guarded input, cold HAS and movie')
    transform_log = run([sys.executable, '-u', 'tests/verify_drawing_transform.py'], timeout=600)
    (output / 'drawing-transform-suite.log').write_text(transform_log, encoding='utf-8')
    results['drawing_transform'] = json.loads((output / 'drawing-transform-verification.json').read_text(encoding='utf-8'))
    print('PASS guarded drawing resize/free rotation, premultiplied reference, live physics, cold HAS and movie')
    identity_log = run([sys.executable, '-u', 'tests/verify_recovery_identity.py'], timeout=90)
    (output / 'recovery-identity-suite.log').write_text(identity_log, encoding='utf-8')
    results['recovery_identity'] = json.loads((output / 'recovery-identity-verification.json').read_text(encoding='utf-8'))
    print('PASS exact Windows owner identity, reused PID decisions and legacy recovery protection')
    startup_log = run([sys.executable, '-u', 'tests/verify_recovery_startup.py'], timeout=300)
    (output / 'recovery-startup-suite.log').write_text(startup_log, encoding='utf-8')
    results['recovery_startup'] = json.loads((output / 'recovery-startup-verification.json').read_text(encoding='utf-8'))
    print('PASS abrupt exit, normal newest-valid startup, fallback, native data and preserved manual HAS')
    history_log = run([sys.executable, '-u', 'tests/verify_recovery_history.py'], timeout=300)
    (output / 'recovery-history-suite.log').write_text(history_log, encoding='utf-8')
    results['recovery_history'] = json.loads((output / 'recovery-history-verification.json').read_text(encoding='utf-8'))
    print('PASS bounded recovery journal, idle previews, Advanced restore and deep native fallback')
    schedule_log = run([sys.executable, '-u', 'tests/verify_recovery_schedule.py'], timeout=180)
    (output / 'recovery-schedule-suite.log').write_text(schedule_log, encoding='utf-8')
    results['recovery_schedule'] = json.loads((output / 'recovery-schedule-verification.json').read_text(encoding='utf-8'))
    print('PASS completed-edit and minute recovery schedules, idle timer, retry and manual save protection')
    preview_log = run([sys.executable, '-u', 'tests/verify_recovery_preview.py'], timeout=180)
    (output / 'recovery-preview-suite.log').write_text(preview_log, encoding='utf-8')
    results['recovery_preview'] = json.loads((output / 'recovery-preview-verification.json').read_text(encoding='utf-8'))
    print('PASS background preview work, responsive editing/playback, queued checkpoints and joined teardown')
    home_log = run([sys.executable, '-u', 'tests/verify_home.py'], timeout=240)
    (output / 'home-suite.log').write_text(home_log, encoding='utf-8')
    results['home'] = json.loads((output / 'home-verification.json').read_text(encoding='utf-8'))
    print('PASS Home, real recent HAS workflows, safe cancellation, thumbnails and inherited startup priority')
    tutorial_log = run([sys.executable, '-u', 'tests/verify_tutorials.py'], timeout=260)
    (output / 'tutorial-suite.log').write_text(tutorial_log, encoding='utf-8')
    results['tutorials'] = json.loads((output / 'tutorials-verification.json').read_text(encoding='utf-8'))
    print('PASS first interactive chapters, original practice scene, whole-state Previous and fresh-process Continue')
    first_log = run([sys.executable, '-u', 'tests/verify_first_movie.py'], timeout=300)
    (output / 'first-movie-suite.log').write_text(first_log, encoding='utf-8')
    results['first_movie'] = json.loads((output / 'first-movie-verification.json').read_text(encoding='utf-8'))
    print('PASS beginner import-to-movie course, live physics, visual hints, optional Save and actual MP4 completion')
    ffmpeg = os.environ.get("HYBRID_FFMPEG", shutil.which("ffmpeg") or r"C:\Program Files\ffmpeg\bin\ffmpeg.exe")
    ffprobe = str(Path(ffmpeg).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe"))
    # Spike B fixture: 48kHz, exact silence until frame 24, then a 0.2s 1kHz tone.
    spike = output / "spikes"
    samples = array.array("h", (int(16000 * math.sin(2 * math.pi * 1000 * n / 48000))
                               if 48000 <= n < 57600 else 0 for n in range(96000)))
    if sys.byteorder != "little":
        samples.byteswap()
    tone = spike / "known tone.wav"
    with wave.open(str(tone), "wb") as wav:
        wav.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        wav.writeframes(samples.tobytes())
    # Also exercises the application's encoder adapter with audio, independently of editor Stage 2.
    run(command("tests/audio_spike.gd"))
    for name, movie in [("silent", Path(json.loads((output / "editor-smoke/result.json").read_text())["export"]) / "movie.mp4"),
                        ("tone", spike / "movie.mp4"),
                        ("editor_audio", Path(json.loads((output / "audio-editor/result.json").read_text())["export"]) / "movie.mp4"),
                        ("autokey", Path(json.loads((output / "autokey-result.json").read_text())["movie"])),
                        ("new_scene", Path(json.loads((output / "new-scene-result.json").read_text())["movie"])),
                        ("world_runtime", Path(json.loads((output / "world-runtime-result.json").read_text())["movie"])),
                        ("world_edit", Path(json.loads((output / "world-edit-result.json").read_text())["movie"])),
                        ("world_workflow", Path(json.loads((output / "world-workflow-result.json").read_text())["movie"])),
                        ("object_timing", Path(json.loads((output / "object-timing-result.json").read_text())["movie"])),
                        ("animation_clips", Path(json.loads((output / "animation-clips-result.json").read_text())["movie"])),
                        ("visibility", Path(json.loads((output / "visibility-result.json").read_text())["movie"])),
                        ("animated_channels", Path(json.loads((output / "animated-channels-result.json").read_text())["movie"])),
                        ("limb_ik", Path(json.loads((output / "limb-ik-result.json").read_text())["movie"])),
                        ("physics", Path(json.loads((output / "physics-result.json").read_text())["movie"])),
                        ("secondary_motion", Path(json.loads((output / "secondary-motion-result.json").read_text())["movies"][0])),
                        ("fan_motion", Path(json.loads((output / "fan-motion-result.json").read_text())["movie"])),
                        ("physics_props", Path(json.loads((output / "physics-props-result.json").read_text())["movie"])),
                        ("physics_recording", Path(json.loads((output / "physics-recording-result.json").read_text())["movie"]))]:
        metadata = json.loads(run([ffprobe, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(movie)]))
        video = next(s for s in metadata["streams"] if s["codec_type"] == "video")
        assert video["codec_name"] == "h264" and video["nb_read_frames"] == "48"
        assert video["width"] == 1920 and video["height"] == 1080 and video["r_frame_rate"] == "24/1"
        assert abs(float(metadata["format"]["duration"]) - 2) < 0.01
        if name in ("tone", "editor_audio", "world_workflow", "animation_clips", "visibility", "animated_channels", "limb_ik", "physics_props", "physics_recording"):
            assert any(s["codec_name"] == "aac" for s in metadata["streams"])
        else:
            assert not any(s["codec_type"] == "audio" for s in metadata["streams"])
        (output / f"{name}-ffprobe.json").write_text(json.dumps(metadata, indent=2))
        results[name + "_video"] = {"frames": 48, "fps": "24/1", "duration": metadata["format"]["duration"]}
    pose_report = json.loads((output / "pose-smoke/result.json").read_text(encoding="utf-8"))
    for index, movie in enumerate(pose_report["movies"]):
        metadata = json.loads(run([ffprobe, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", movie]))
        video = next(stream for stream in metadata["streams"] if stream["codec_type"] == "video")
        assert video["codec_name"] == "h264" and video["nb_read_frames"] == "48"
        assert video["width"] == 1920 and video["height"] == 1080 and video["r_frame_rate"] == "24/1"
        assert abs(float(metadata["format"]["duration"]) - 2) < 0.01
        results[f"posed_model_video_{index}"] = {"frames": 48, "fps": "24/1", "duration": metadata["format"]["duration"]}
    results["pose_checks"] = pose_report["checks"]
    results["actual_mmd_tested"] = pose_report["actual_mmd_tested"]
    decoded = spike / "decoded.wav"
    run([ffmpeg, "-v", "error", "-y", "-i", str(spike / "movie.mp4"), "-vn", "-c:a", "pcm_s16le", str(decoded)])
    with wave.open(str(decoded), "rb") as wav:
        pcm = array.array("h", wav.readframes(wav.getnframes()))
        if sys.byteorder != "little": pcm.byteswap()
        rate = wav.getframerate()
    # AAC can ring around transients. Use 10ms RMS windows and a documented tolerance.
    onset = None
    for index in range(0, len(pcm) - 480, 480):
        rms = math.sqrt(sum(v * v for v in pcm[index:index + 480]) / 480)
        if rms > 1500:
            onset = index / rate
            break
    assert onset is not None and abs(onset - 1.0) <= 0.02, onset
    results["tone_onset_seconds"] = onset
    editor_report = json.loads((output / "audio-editor/result.json").read_text())
    editor_movie = Path(editor_report["export"]) / "movie.mp4"
    editor_pcm = output / "audio-editor/decoded.wav"
    run([ffmpeg, "-v", "error", "-y", "-i", str(editor_movie), "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(editor_pcm)])
    with wave.open(str(editor_pcm), "rb") as wav:
        pcm = array.array("h", wav.readframes(wav.getnframes()))
        if sys.byteorder != "little": pcm.byteswap()
    first = next((n / 48000 for n in range(0, len(pcm) - 480, 480)
                  if math.sqrt(sum(v*v for v in pcm[n:n+480]) / 480) > 1500), None)
    assert first is not None and abs(first - 1.0) <= 0.02, first
    rms = math.sqrt(sum(v*v for v in pcm[52800:57600]) / 4800)
    assert 5300 < rms < 6000, rms  # 16000 amplitude at -6dB, allowing AAC loss.
    results["editor_audio"] = {"onset_seconds": first, "rms_at_1_1s": rms,
                               "audio_driver": editor_report["audio_driver"]}
    results["representative_png_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in [spike / "frame_000001.png", spike / "frame_000025.png", spike / "frame_000048.png"]}
    (output / "verification.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
