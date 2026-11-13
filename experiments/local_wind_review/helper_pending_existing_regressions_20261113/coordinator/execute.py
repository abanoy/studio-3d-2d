from pathlib import Path
import hashlib, importlib.util, json, os, subprocess, sys, time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('owned_preview_regression_source', ROOT/'tests/verify_helper_preview.py')
proof = importlib.util.module_from_spec(spec); spec.loader.exec_module(proof)
before = proof.source_manifest(ROOT)
head = proof.git(ROOT, 'rev-parse', 'HEAD')
jobs = [
    ('secondary_helpers', ['tests/verify_secondary_helpers.py'], 600),
    ('secondary_existing_ribbon', ['tests/verify_secondary_existing.py', '--prepared-source', str(ROOT/'output/wind-main-fixtures-1794548724013390200/wind-native/ribbon/scene.glb'), '--with-ribbon'], 300),
    ('secondary_picking', ['tests/verify_secondary_picking.py'], 250),
    ('secondary_batch', ['tests/verify_secondary_batch.py'], 400),
    ('helper_morphs', ['tests/verify_helper_morphs.py'], 180),
    ('scene_view', ['tests/verify_scene_view.py'], 350),
]
env = os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1', HYBRID_GODOT=str(proof.GODOT), HYBRID_NATIVE_INPUTS=r'C:\a\dump', HYBRID_FFMPEG=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe')
rows = []
error = None
def save(name, value):
    (FOLDER/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
save('source-before.json', before)
try:
    for label, args, deadline in jobs:
        command = [str(proof.PYTHON), '-B', '-u', *args]
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW)
        row = dict(label=label, command=command, pid=process.pid, started_ns=time.time_ns())
        rows.append(row); save('progress.json', rows)
        try:
            out, err = process.communicate(timeout=deadline)
        except subprocess.TimeoutExpired:
            process.kill(); out, err = process.communicate(); row['timed_out'] = True
        (FOLDER/(label+'.log')).write_text(out+err, encoding='utf-8')
        row.update(exit=process.returncode, reaped=process.poll() is not None, finished_ns=time.time_ns())
        row['passed'] = row['exit']==0 and row['reaped'] and not row.get('timed_out', False)
        save('progress.json', rows)
        print(('PASS ' if row['passed'] else 'FAIL ')+label, flush=True)
        if not row['passed']: raise RuntimeError('Existing regression failed: '+label)
except Exception as failure:
    error = type(failure).__name__+': '+str(failure)
finally:
    after = proof.source_manifest(ROOT)
    save('source-after.json', after)
    report = dict(format='has_pending_helper_existing_regressions_1', head_before=head, head_after=proof.git(ROOT, 'rev-parse', 'HEAD'), source_context='main_working_source', results=rows, error=error, source_preserved=before==after)
    report['passed'] = not error and len(rows)==len(jobs) and all(row['passed'] for row in rows) and report['source_preserved'] and report['head_before']==report['head_after']
    save('verification.json', report)
print(json.dumps(dict(passed=report['passed'], folder=str(FOLDER))), flush=True)
raise SystemExit(0 if report['passed'] else 1)
