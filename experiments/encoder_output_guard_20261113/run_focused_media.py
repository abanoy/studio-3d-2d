import hashlib, importlib.util, json, os, pathlib, subprocess, time, traceback

root = pathlib.Path(__file__).resolve().parents[2]
base = pathlib.Path(__file__).resolve().parent
folder = base / ('focused-main-' + str(time.time_ns()))
folder.mkdir()
spike = folder / 'spikes'
spike.mkdir()
membership = json.loads((root / 'output/canonical-owned-20261113T014241546/source-before.json').read_bytes())['source_sha256']

def source():
    return {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
            'files': {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in membership}}

before = source()
(folder/'source-before.json').write_text(json.dumps(before, indent=2)+'\n', encoding='utf-8')
spec = importlib.util.spec_from_file_location('focused_canonical_verifier', root/'tests/verify.py')
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
original_run = verify.run
receipts = []

def checked_run(args, *a, **k):
    if '--receipt' in args:
        receipts.append(pathlib.Path(args[args.index('--receipt')+1]))
    return original_run(args, *a, **k)

verify.run = checked_run
os.environ['HYBRID_FFMPEG'] = r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
os.environ['HYBRID_PYTHON'] = r'C:\Program Files\Python313\python.exe'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
proof = {'format': 'has_encoder_fixed_scoped_media_1', 'status': 'running',
         'scope': 'Fresh fixed silent/tone exports plus final media checks against retained functional-workflow reports from failed3acanonical; not a fresh fullaggregate',
         'full_aggregate': False, 'functional_files': len(membership), 'results': {}, 'private_receipts': []}
error = None
try:
    text = checked_run(verify.command('tests/spikes.gd', extra=['--', str(spike)]))
    (folder/'spikes.log').write_text(text, encoding='utf-8')
    assert 'SPIKES failures=0' in text and not any(x in text for x in ['SCRIPT ERROR', 'FAIL ', 'ObjectDB instances leaked']), text
    verify.verify_media(root/'output', spike, proof['results'])
    proof['status'] = 'passed'
except BaseException:
    error = traceback.format_exc()
    proof['status'] = 'failed'
    proof['error'] = error
finally:
    after = source()
    (folder/'source-after.json').write_text(json.dumps(after, indent=2)+'\n', encoding='utf-8')
    proof['source_unchanged'] = after == before
    for path in receipts:
        if path.is_file():
            raw = path.read_bytes()
            proof['private_receipts'].append({'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'value': json.loads(raw)})
    proof['clean_private_receipts'] = len(receipts) == 2 and len(proof['private_receipts']) == 2 and all(
        r['value']['exit'] == 0 and r['value']['child_desktop_confirmed'] and not r['value']['foreground_child_observed']
        and r['value']['job_closed'] and r['value']['desktop_closed'] for r in proof['private_receipts'])
    if not proof['source_unchanged'] or not proof['clean_private_receipts']:
        proof['status'] = 'failed'
    (folder/'verification.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'folder': str(folder), 'status': proof['status'], 'results': proof['results'],
                  'source_unchanged': proof['source_unchanged'], 'clean_private_receipts': proof['clean_private_receipts']}, indent=2))
if error:
    print(error)
raise SystemExit(0 if proof['status'] == 'passed' else 1)
