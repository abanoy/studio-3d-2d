"""Root launcher for a pinned, closed-stage CPU correction; no native apps."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
HEAD = 'ffed3fc2fe4f078a4c6cd506c5c757b7f46db82b'
STAGE = ROOT / 'output/source-material-carrier-run-1795228448950398100'
ORIGINAL = Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\sfm-bone-bindings-native-launch-20261114T033026205\run\Studio\output\compatibility\source-1794627119-888-34370685')
ORIGINAL_PINS = {
    'native/junko hair.mdl': (37644, '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
    'native/junko hair.vvd': (618368, '2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
    'native/junko hair.dx90.vtx': (173309, '924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a'),
    'editable.blend': (2423175, 'ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6'),
    'scene.glb': (2322644, '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'),
    'parameters.json': (159684, 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'),
}

def row(path):
    before = path.stat()
    with path.open('rb') as stream:
        assert os.fstat(stream.fileno()) == before
        raw = stream.read(before.st_size + 1)
        assert os.fstat(stream.fileno()) == before
    after = path.stat()
    assert before == after and before.st_mtime_ns == after.st_mtime_ns
    assert len(raw) == before.st_size
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'mtime_ns': before.st_mtime_ns}

def originals():
    result = {}
    for name, pin in ORIGINAL_PINS.items():
        value = row(ORIGINAL / name)
        assert (value['bytes'], value['sha256']) == pin, name
        result[name] = value
    return result

def git_head():
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, capture_output=True)
    value = result.stdout.decode('ascii').strip()
    assert value == HEAD
    return value

def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wrapper', required=True)
    parser.add_argument('--wrapper-bytes', type=int, required=True)
    parser.add_argument('--wrapper-sha256', required=True)
    args = parser.parse_args()
    wrapper = Path(args.wrapper).absolute()
    assert wrapper.is_relative_to(ROOT / 'output')
    wrapper_row = row(wrapper)
    assert (wrapper_row['bytes'], wrapper_row['sha256']) == (args.wrapper_bytes, args.wrapper_sha256)
    assert not sys.flags.optimize and sys.version_info[:2] == (3, 13)
    before = originals()
    git_head()
    serial = str(time.time_ns())
    output = ROOT / ('output/source-native-normal-correction-' + serial)
    prefix = ROOT / ('output/source-native-normal-correction-root-' + serial)
    files = {
        'audit': STAGE / 'PUBLIC_CARRIER_EXPORT_FAILED_PRESERVATION.json',
        'worker': STAGE / 'result/PUBLIC_CARRIER_EXPORT.json',
        'desktop': STAGE / 'private-desktop.json',
        'comparisons': STAGE / 'STRICT_CARRIER_COMPARISONS.json',
        'carrier': STAGE / 'result/carrier.glb',
        'relation': STAGE / 'result/PRIVATE_PRIMITIVE_IDS.json',
        'baseline': ORIGINAL / 'scene.glb',
        'mdl': STAGE / 'inputs/junko hair.mdl',
        'vvd': STAGE / 'inputs/junko hair.vvd',
        'vtx': STAGE / 'inputs/junko hair.dx90.vtx',
    }
    request = dict(format='has_closed_carrier_normal_correction_request_1', source_head=HEAD,
        closed_stage=str(STAGE), output=str(output), root_cpu_lane_confirmed=True,
        root_coordinator_reaped=True, wrapper={'bytes': args.wrapper_bytes, 'sha256': args.wrapper_sha256},
        files={name: row(path) for name, path in files.items()})
    request_path = Path(str(prefix) + '-request.json')
    write_new(request_path, request)
    request_row = row(request_path)
    write_new(Path(str(prefix) + '-before.json'), before)
    started = time.monotonic()
    result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(wrapper), '--request', str(request_path),
                             '--request-sha256', request_row['sha256']], cwd=ROOT, capture_output=True, timeout=60)
    elapsed = time.monotonic() - started
    Path(str(prefix) + '-stdout.log').write_bytes(result.stdout)
    Path(str(prefix) + '-stderr.log').write_bytes(result.stderr)
    after = originals()
    git_head()
    assert before == after and row(wrapper) == wrapper_row and row(request_path) == request_row
    assert all(row(path) == request['files'][name] for name, path in files.items())
    write_new(Path(str(prefix) + '-after.json'), after)
    summary = dict(format='has_root_conditional_normal_correction_launch_1', status='PASS' if result.returncode == 0 else 'FAIL',
        source_head=HEAD, wrapper=wrapper_row, request=request_row, returncode=result.returncode,
        elapsed_seconds=elapsed, all_six_originals_hash_size_nsmtime_unchanged=True,
        all_ten_inputs_hash_size_nsmtime_unchanged=True, native_process_launched=False,
        application_adoption_qualified=False, output=str(output.relative_to(ROOT)),
        correction_report_present=(output / 'PUBLIC_CORRECTION.json').is_file())
    write_new(Path(str(prefix) + '-result.json'), summary)
    print(json.dumps(summary))
    if result.stderr:
        print(result.stderr.decode('utf-8', errors='replace'))
    raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()
