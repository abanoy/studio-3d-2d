"""One procedural private-desktop replay; no native cases, opt-in lease required."""
from pathlib import Path
import argparse
import importlib.util
import json
import subprocess
import sys
import time

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-gpu', action='store_true')
    parser.add_argument('--lease-confirmed', action='store_true')
    options = parser.parse_args()
    if not options.run_gpu or not options.lease_confirmed:
        parser.error('Root must explicitly release its GPU lease and supply both switches')
    spec = importlib.util.spec_from_file_location('wind_procedural_private_check', BASE / 'verify_gpu.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.guard(BASE, module.ROOT / 'output')
    before_runtime = module.runtime_hashes()
    before_sources = module.source_manifest()
    folder = BASE / 'gpu-procedural-verification' / str(time.time_ns())
    module.guard(folder, BASE)
    folder.mkdir(parents=True, exist_ok=False)
    case = folder / 'procedural'
    case.mkdir()
    module.write_json(folder / 'source-before.json', before_sources)
    tone = folder / 'known-tone.wav'
    module.audio(tone)
    request = case / 'request.json'
    module.write_json(request, {'mode': 'procedural', 'folder': str(case).replace('\\', '/'), 'audio': str(tone).replace('\\', '/')})
    runner = module.runner()
    args = runner.command('tests/wind_review_gpu_motion.gd', extra=['--audio-driver', 'Dummy', '--log-file', str(case / 'engine.log'), '--', str(request)])
    module.require('--receipt' in args and 'private_desktop.py' in args[1], 'No private Windows desktop; visible fallback refused')
    receipt_path = case / 'private-receipt.json'
    args[args.index('--receipt') + 1] = str(receipt_path)
    module.write_json(case / 'command.json', args)
    exit_code = None
    log = ''
    error = ''
    try:
        process = subprocess.run(args, cwd=module.STUDIO, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=330)
        exit_code = process.returncode
        log = process.stdout + process.stderr
    except (OSError, subprocess.SubprocessError) as caught:
        error = str(caught)
    finally:
        (case / 'process.log').write_text(log, encoding='utf-8')
        result = json.loads((case / 'result.json').read_bytes()) if (case / 'result.json').is_file() else {}
        receipt = json.loads(receipt_path.read_bytes()) if receipt_path.is_file() else {}
        clean = receipt.get('exit') == 0 and receipt.get('child_desktop_confirmed') and not receipt.get('foreground_child_observed', True) and receipt.get('job_closed') and receipt.get('desktop_closed')
        after_runtime = module.runtime_hashes()
        after_sources = module.source_manifest()
        module.write_json(folder / 'source-after.json', after_sources)
        errors = [word for word in ['ERROR:', 'SCRIPT ERROR', 'FAIL ', 'ObjectDB instances leaked', 'unclaimed string names', 'Object was freed while a signal is being emitted', '_set_transient_exclusive_child'] if word in log]
        report = {'format': 'has_wind_procedural_once_1', 'folder': str(folder), 'exit': exit_code, 'error': error, 'checks': result.get('checks'), 'failures': result.get('failures'), 'runtime_unchanged': before_runtime == after_runtime, 'all_prototype_source_hash_size_mtime_unchanged': before_sources == after_sources, 'runtime_source_sha256': before_runtime, 'test_sha256': {name: module.sha(module.STUDIO / name) for name in module.SCRIPTS}, 'clean_isolation': bool(clean), 'private_receipt': str(receipt_path), 'error_markers': errors, 'gpu_used': True, 'scope': 'Only the owned procedural fixture. No VRM0, VRM1, Back hair, lifecycle or primary-physics case ran; this is not a six-case matrix pass.'}
        report['passed'] = exit_code == 0 and not error and result.get('failures', 1) == 0 and 'WIND_REVIEW_GPU_MOTION ' in log and clean and not errors and before_runtime == after_runtime and before_sources == after_sources
        module.write_json(folder / 'verification.json', report)
    print(json.dumps({'folder': str(folder), 'passed': report['passed'], 'checks': report['checks'], 'failures': report['failures'], 'native_cases_run': False}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
