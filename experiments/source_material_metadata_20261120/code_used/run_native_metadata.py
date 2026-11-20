"""Root-only, exact-family RAM metadata observation; no Blender or asset writes."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import stat
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).with_name('material_metadata.py')
CODE_PIN = (13818, 'c04c4e20705b490ed7633855b2e3bdde14350adec35c8b2a25afc42b69508395')
INPUTS = {
    'mdl': ('junko hair.mdl', 37644, '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
    'vvd': ('junko hair.vvd', 618368, '2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
    'vtx': ('junko hair.dx90.vtx', 173309, '924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a'),
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path, count, digest):
    for parent in (path, *path.parents):
        info = parent.lstat()
        if info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RuntimeError('REPARSE_PATH_REFUSED')
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise RuntimeError('REGULAR_SINGLE_LINK_REQUIRED')
    raw = path.read_bytes()
    after = path.lstat()
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_nlink')
    if tuple(getattr(before, k) for k in fields) != tuple(getattr(after, k) for k in fields):
        raise RuntimeError('INPUT_CHANGED_DURING_READ')
    if len(raw) != count or sha(raw) != digest:
        raise RuntimeError('PINNED_INPUT_IDENTITY_DIFFERS')
    return raw, dict(bytes=count, sha256=digest, mtime_ns=after.st_mtime_ns)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root-lane-confirmed', action='store_true')
    args = parser.parse_args()
    if not args.root_lane_confirmed or not sys.dont_write_bytecode:
        raise RuntimeError('ROOT_AND_NO_BYTECODE_REQUIRED')
    folder = ROOT / 'output/source-current-id-run-1795202600420799400/inputs'
    destination = ROOT / 'output/source-material-native-metadata-20261120-01'
    if not folder.resolve().is_relative_to((ROOT / 'output').resolve()):
        raise RuntimeError('OWNED_STAGING_REQUIRED')
    destination.mkdir(exist_ok=False)
    code_raw, code_before = read(CODE, *CODE_PIN)
    controller_raw = Path(__file__).read_bytes()
    before, native_refs = {}, {}
    for role, (name, count, digest) in INPUTS.items():
        raw, before[role] = read(folder / name, count, digest)
        native_refs[role] = dict(raw=raw, bytes=count, sha256=digest)
    spec = importlib.util.spec_from_file_location('has_material_metadata_candidate', CODE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    started = time.perf_counter()
    result = dict(format='has_exact_native_material_metadata_root_observation_1',
                  application_checkpoint='610379aeb672b6f7a585b5d7d3bf7e20f7265c30',
                  parser_identity=code_before, controller_sha256=sha(controller_raw),
                  input_identities=before, private_native_arrays_published=False,
                  actual_Blender_SourceIO_library_or_exporter_executed=False,
                  original_B_opened=False, input_geometry_decoded=False,
                  raw_mesh_material_field_is_resolved_native_skin_material=False,
                  VTX_face_material_order_qualified=False, Blender_face_slot_binding_qualified=False,
                  B_dependency_closure_qualified=False, normal_fidelity_qualified=False,
                  application_adoption_qualified=False)
    error = None
    try:
        derived = module.derive_material_metadata(native_refs)
        metadata = derived['metadata']
        encoded = json.dumps(metadata, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
        models = [model for part in metadata['body_parts'] for model in part['models']]
        result.update(status='EXACT_NATIVE_METADATA_PARSED',
                      metadata_sha256=sha(encoded), materials=len(metadata['materials']),
                      search_paths=len(metadata['search_paths']),
                      skin_reference_count=metadata['skin_reference_count'],
                      skin_families=len(metadata['skin_families']),
                      body_parts=len(metadata['body_parts']), model_records=len(models),
                      renderable_models=sum(model['vertex_count'] > 0 for model in models),
                      mesh_records=metadata['mesh_records'],
                      aggregate_model_vertices=sum(model['vertex_count'] for model in models))
    except module.Refusal as refusal:
        code = str(refusal)
        if re.fullmatch('[A-Z0-9_]+', code) is None:
            raise RuntimeError('UNEXPECTED_REFUSAL_PAYLOAD')
        result.update(status='REFUSED_NATIVE_METADATA_PROFILE', refusal=code)
        error = code
    finally:
        _raw, code_after = read(CODE, *CODE_PIN)
        if code_after != code_before or Path(__file__).read_bytes() != controller_raw:
            raise RuntimeError('PARSER_OR_CONTROLLER_CHANGED')
        for role, (name, count, digest) in INPUTS.items():
            _raw, after = read(folder / name, count, digest)
            if after != before[role]:
                raise RuntimeError('NATIVE_INPUT_CHANGED')
    result.update(wall_seconds=time.perf_counter()-started,
                  source_and_input_hash_size_nsmtime_unchanged=True,
                  Python_executable=str(Path(sys.executable)),
                  no_native_metadata_or_names_persisted=True)
    raw = (json.dumps(result, indent=2)+'\n').encode('utf-8')
    (destination / 'PUBLIC_RESULT.json').write_bytes(raw)
    print(json.dumps(result))
    return 1 if error else 0

if __name__ == '__main__':
    raise SystemExit(main())
