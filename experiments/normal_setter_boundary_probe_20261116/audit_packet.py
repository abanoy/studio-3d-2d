"""CPU-only source/provenance/test audit. Never starts Blender, CIM, Git or a client."""
from pathlib import Path
import ast
import datetime
import io
import json
import struct
import sys
import time
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from setter_support import ROOT, approved, normal_support, validate_prior, sha, require
from instrumentation import observed_import_function
from vvd_normals import decode_lod0_normals
from stage_after_full import B, PRIOR, SIO

FULL_COMMIT = '52f63c944ded7a651da871524d23a345b606424d'
FULL_RUN = ROOT / 'output/windows-canonical-bone-binding-20261116T041518335'
EXPECTED_INPUTS = {
    'mdl': (B / 'native/junko hair.mdl', '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
    'vvd': (B / 'native/junko hair.vvd', '2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
    'vtx': (B / 'native/junko hair.dx90.vtx', '924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a'),
    'saved_capture': (PRIOR / 'capture/PRIVATE_NORMALS.json', '0ef144f3ffe093d6c01f31e5e6fadf98e87a5c7de2b4013c27d42809dabd6921'),
    'importer': (SIO / 'blender_bindings/models/mdl49/import_mdl.py', '173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b'),
}


def metadata(path):
    body = path.read_bytes()
    return {'path': str(path), 'bytes': len(body), 'sha256': sha(body)}


def main():
    require(not (HERE / 'CPU_VALIDATION.json').exists(), 'Preserve earlier CPU audit; use a fresh packet for another audit')
    start = time.monotonic()
    lock = approved()
    require(str(Path(sys.executable).resolve()) in lock['runtime_executables'], 'Use the approved exact Python executable')
    pins = {}
    for role, (path, expected) in EXPECTED_INPUTS.items():
        pins[role] = metadata(path)
        require(pins[role]['sha256'] == expected, 'Known actual input differs: ' + role)
    approved_vtx = [identity['sha256'] for files in lock['native_families'].values() for name, identity in files.items()
                    if name.replace('\\', '/').lower().endswith('/junko hair.dx90.vtx')]
    require(approved_vtx == [EXPECTED_INPUTS['vtx'][1]], 'Retained exact VTX is not the approved native family member')
    raw_mdl = EXPECTED_INPUTS['mdl'][0].read_bytes()
    raw_vvd = EXPECTED_INPUTS['vvd'][0].read_bytes()
    checksum = struct.unpack_from('<I', raw_mdl, 8)[0]
    decoded = decode_lod0_normals(raw_vvd, expected_checksum=checksum)
    require(len(decoded['normals']) == 9661 and decoded['raw_vertex_indices'] == tuple(range(9661)), 'Exact original LOD0 profile differs')
    observed, inverse = observed_import_function(EXPECTED_INPUTS['importer'][0].read_text(encoding='utf-8'))
    compile(observed, '[actual SourceIO function plus observer]', 'exec')
    parsed = []
    for path in sorted(HERE.glob('*.py')):
        compile(ast.parse(path.read_text(encoding='utf-8')), str(path), 'exec')
        parsed.append(path.name)
    paths = {role: path for role, (path, _) in EXPECTED_INPUTS.items()}
    paths.update(prior_public=PRIOR/'capture/PUBLIC_CAPTURE.json', prior_comparison=PRIOR/'BLENDER_BOUNDARY_COMPARISON.json',
                 prior_execution=PRIOR/'root-execution/verification.json', prior_closure=PRIOR/'root-execution/after-closure.json')
    prior = validate_prior(paths)
    context = normal_support().read_context(FULL_RUN, FULL_COMMIT, 1019)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(unittest.defaultTestLoader.discover(str(HERE), pattern='test_*.py'))
    report = {
        'format': 'has_sourceio_setter_probe_cpu_validation_1',
        'status': 'CPU_SOURCE_READY_NATIVE_UNRUN' if result.wasSuccessful() else 'CPU_TEST_FAILED_NATIVE_UNRUN',
        'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'seconds': time.monotonic()-start,
        'python': str(Path(sys.executable).resolve()),
        'unit_tests': {'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                       'skipped': len(result.skipped), 'synthetic_only': True, 'log': stream.getvalue()},
        'python_sources_parsed': parsed,
        'source_files': {p.name: metadata(p) for p in sorted(HERE.glob('*.py'))},
        'actual_input_pins': pins,
        'approved_catalogues_unchanged': {'runtime_executables': 6, 'SourceIO_files': 574, 'exporter_sources': 120},
        'actual_VVD_profile': {'checksum': checksum, 'lod0_vertex_count': len(decoded['normals']),
                               'raw_lod0_identity_map': True, 'normal_arrays_published': False},
        'actual_importer_AST': inverse,
        'prior_closed_normal_context': prior,
        'actual_full_source_context': {'commit': context['expected_commit'], 'functional_source_count': context['functional_count'],
                                       'files': context['files']},
        'Blender_executed': False, 'SourceIO_import_executed': False, 'Git_executed': False, 'CIM_executed': False,
        'main_functional_files_modified': False,
        'normal_fidelity': 'FAILED_UNQUALIFIED; previous original raw-GLB failure remains unchanged',
    }
    with (HERE/'CPU_VALIDATION.json').open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({'status': report['status'], 'tests': result.testsRun, 'failures': len(result.failures),
                      'errors': len(result.errors), 'seconds': report['seconds'],
                      'report_sha256': sha((HERE/'CPU_VALIDATION.json').read_bytes())}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__': raise SystemExit(main())
