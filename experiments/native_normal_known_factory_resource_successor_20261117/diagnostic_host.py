"""Future pinned-Blender host; main is never called by source/CPU preparation."""
from pathlib import Path
import argparse
import json
import os
import sys
import tempfile
import traceback
sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagnostic_support as S


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    request_path = S.safe(args.request)
    S.need(S.digest(request_path.read_bytes()) == args.request_sha256, 'Host request changed')
    request = S.read_json(request_path); stage = S.safe(request['stage'])
    S.need(stage.is_relative_to(S.ROOT / 'output') and request_path == stage / 'host-request.json', 'Owned host request required')
    S.packet(S.HERE, request['packet_sha256']); S.packet(S.SURVEY, S.SURVEY_SHA)
    admitted = S.check_inputs(request['admission_path'], request['admission_sha256'], request['packet_sha256'])
    S.need(request['public_reference'] == admitted[3], 'Exact public known-B reference required')
    S.need(stage == S.safe(admitted[0]['output']) and stage.parent == S.ROOT / 'output', 'Admitted fresh output required')
    r = S.reader(); original = S.safe(request['original_blend']); owned = S.safe(request['owned_blend'])
    S.validate_identity(request['original_identity'], with_path=False)
    S.validate_identity(request['owned_identity'], with_path=False)
    S.need(original == S.safe(S.ROOT / admitted[3]['files']['blend']['path'])
           and request['original_identity'] == admitted[1]['blend'], 'Known session B original required')
    S.need(owned == stage / 'editable.blend' and r.identity(owned, single_link=True) == request['owned_identity'], 'Owned B copy changed')
    S.need(all(request['owned_identity'][key] == admitted[1]['blend'][key] for key in ('bytes', 'sha256')),
           'Owned copy must contain the exact known original B bytes')
    S.need(r.identity(original, single_link=True) == request['original_identity'], 'Original B changed')
    for key in ('TEMP', 'TMP', 'BLENDER_USER_CONFIG', 'BLENDER_USER_SCRIPTS', 'BLENDER_USER_DATAFILES', 'BLENDER_USER_EXTENSIONS'):
        S.need(S.safe(os.environ[key]) == stage / 'environment' / key and S.safe(os.environ[key]).is_dir(), 'Owned child environment differs')
    S.need(S.safe(tempfile.gettempdir()) == stage / 'environment' / 'TEMP', 'Actual temporary directory differs')
    sys.path.insert(0, str(S.SURVEY))
    import bpy
    from known_loaded_survey import inspect_loaded_owned_scene
    from placement_sentinel import _hidden_placement_sentinel
    from survey_core import canonical
    approved_blender = next(path for path in admitted[2]['runtime_executables'] if Path(path).name.lower() == 'blender.exe')
    S.need(S.safe(bpy.app.binary_path) == S.safe(request['blender_executable']) == S.safe(approved_blender), 'Approved Blender binary path required')
    S.need(bpy.app.background is True and bpy.app.online_access is False and bpy.app.autoexec_fail is False
           and bpy.context.preferences.filepaths.use_scripts_auto_execute is False and bpy.data.filepath == '', 'Factory background/offline/no-file/disabled-autoexec required')
    bound = S.H.read_bound_baseline(admitted[0]['factory_baseline'], r, S.safe, S.ROOT)
    observed = S.H.check_live(bpy.app.handlers, bound, 'BEFORE_OWNED_B_OPEN')
    S.save(stage / 'PRIVATE_HANDLERS_BEFORE.json', observed)
    with _hidden_placement_sentinel() as placement:
        # Authorized read-only loader dependency resolution; no confinement claim.
        S.need(bpy.ops.wm.open_mainfile(filepath=str(owned), load_ui=False, use_scripts=False) == {'FINISHED'}, 'Owned B load did not finish')
        # Opening the owned B can invoke the matched installed factory callbacks.
        observed = S.H.check_live(bpy.app.handlers, bound, 'AFTER_OWNED_B_OPEN')
        S.save(stage / 'PRIVATE_HANDLERS_AFTER_LOAD.json', observed)
        private, survey, provenance = inspect_loaded_owned_scene(bpy, str(original), str(owned), request['public_reference'], factory_baseline=bound)
    observed = S.H.check_live(bpy.app.handlers, bound, 'AFTER_RESOURCE_COLLECTION')
    S.save(stage / 'PRIVATE_HANDLERS_AFTER_RESOURCES.json', observed)
    S.need(r.identity(original, single_link=True) == request['original_identity']
           and r.identity(owned, single_link=True) == request['owned_identity']
           and S.digest(request_path.read_bytes()) == args.request_sha256, 'Host inputs changed during diagnostic')
    S.need(S.check_inputs(request['admission_path'], request['admission_sha256'], request['packet_sha256']) == admitted,
           'Host root/source/tool/original context changed')
    private_path = stage / 'PRIVATE_RESOURCES.json'; public_path = stage / 'PUBLIC_RESOURCES.json'
    with private_path.open('xb') as stream: stream.write(canonical(private))
    public = {'format': 'has_session_B_resource_diagnostic_summary_1', 'profile': S.PROFILE,
              'status': 'METADATA_COLLECTED_ROOT_CLOSURE_PENDING', 'survey': survey,
              'export_branch': provenance['export_branch'], 'loader_readonly_dependency_resolution_authorized': True,
              'claims': {key: False for key in S.QUALIFICATIONS}, 'blend_saved': False, 'export_invoked': False,
              'factory_handlers': S.H.public_summary()}
    public['factory_handlers']['private_observations'] = {}
    for name in ('PRIVATE_HANDLERS_BEFORE.json', 'PRIVATE_HANDLERS_AFTER_LOAD.json', 'PRIVATE_HANDLERS_AFTER_RESOURCES.json'):
        raw = (stage / name).read_bytes()
        public['factory_handlers']['private_observations'][name] = {'bytes': len(raw), 'sha256': S.digest(raw)}
    S.save(public_path, public)
    sidecar = {'format': 'has_session_B_resource_diagnostic_placement_1', 'placement': placement,
               'request_sha256': args.request_sha256, 'public_sha256': S.digest(public_path.read_bytes()),
               'private_sha256': S.digest(private_path.read_bytes())}
    S.save(stage / 'PUBLIC_PLACEMENT.json', sidecar)
    print('HAS_B_RESOURCE_DIAGNOSTIC ' + json.dumps(public, sort_keys=True, allow_nan=False))
    print('HAS_B_RESOURCE_PLACEMENT ' + json.dumps(sidecar, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    try: main()
    except BaseException:
        # Blender stderr is captured privately by the retained root driver.
        traceback.print_exc(); raise
