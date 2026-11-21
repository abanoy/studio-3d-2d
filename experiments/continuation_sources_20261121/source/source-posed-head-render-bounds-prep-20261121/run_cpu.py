"""Synthetic headless checks only. Never touches a Full checkout or owner assets."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GODOT = Path('C:/a/tools/Godot/Godot_v4.6-stable_win64.exe')

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    base_pins = json.loads((HERE / 'BASE_SOURCE_PINS.json').read_text(encoding='utf-8'))['files']
    for row in base_pins:
        source = ROOT / row['path']
        if source.stat().st_size != row['bytes'] or sha(source) != row['sha256']:
            raise RuntimeError('Current source base changed: ' + row['path'])
    stage = HERE / ('cpu-stage-' + str(time.time_ns()))
    stage.mkdir()
    (stage / 'src').mkdir()
    (stage / 'tests').mkdir()
    inputs = []
    for relative in ('src/posed_render_envelope.gd', 'src/posed_render_bounds.gd',
                     'tests/posed_render_envelope_unit.gd', 'tests/posed_render_bounds_unit.gd',
                     'src/pose_bounds.gd', 'src/source_shape.gd'):
        source = (HERE / 'payload' / relative) if 'posed_render_' in relative else ROOT / relative
        target = stage / relative
        shutil.copyfile(source, target)
        inputs.append({'source': str(source), 'target': str(target), 'bytes': source.stat().st_size,
                       'sha256': sha(source)})
    (stage / 'project.godot').write_text(
        'config_version=5\n[application]\nconfig/name="HAS Synthetic Render Bounds CPU"\n'
        'config/use_custom_user_dir=true\nconfig/custom_user_dir_name="HASSyntheticRenderBoundsCPU"\n'
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n', encoding='utf-8')
    (stage / 'CPU_INPUTS.json').write_text(json.dumps(inputs, indent=2) + '\n', encoding='utf-8')
    before_env = dict(os.environ)
    reports = []
    try:
        for script, marker, expected in (('posed_render_envelope_unit.gd', 'POSED_RENDER_ENVELOPE', 21),
                                         ('posed_render_bounds_unit.gd', 'POSED_RENDER_BOUNDS', 22)):
            env = dict(before_env)
            for name in ('APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP'):
                local = stage / ('owned-' + name.lower())
                local.mkdir(exist_ok=True)
                env[name] = str(local)
            stdout = stage / (script + '-stdout.log')
            engine = stage / (script + '-engine.log')
            command = [str(GODOT), '--headless', '--path', str(stage), '--log-file', str(engine),
                       '--script', 'res://tests/' + script]
            reaped = False
            timed_out = False
            with stdout.open('wb') as log:
                proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env,
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                try:
                    code = proc.wait(timeout=90)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    proc.kill()
                    code = proc.wait(timeout=15)
                finally:
                    reaped = proc.poll() is not None
            if stdout.stat().st_size > 1024 * 1024:
                raise RuntimeError('Synthetic output exceeded the bounded log size')
            text = stdout.read_text(encoding='utf-8', errors='replace')
            engine_text = engine.read_text(encoding='utf-8', errors='replace') if engine.exists() else 'ERROR: Missing engine log'
            errors = re.findall(r'^(?:SCRIPT ERROR:|ERROR:|FAIL |WARNING: ObjectDB instances leaked).*$', text + '\n' + engine_text, flags=re.MULTILINE)
            matches = re.findall(r'^' + marker + r' (\{.*\})$', text, flags=re.MULTILINE)
            result = json.loads(matches[0]) if len(matches) == 1 else None
            ok = code == 0 and reaped and not timed_out and not errors and result is not None
            ok = ok and type(result.get('checks')) is int and result['checks'] == expected
            ok = ok and sum(line.startswith('PASS ') for line in text.splitlines()) == expected
            ok = ok and type(result.get('failures')) is int and result['failures'] == 0
            reports.append({'script': script, 'exit_code': code, 'reaped': reaped, 'timed_out': timed_out,
                            'status': 'PASS' if ok else 'FAIL', 'result': result, 'error_lines': errors,
                            'stdout_sha256': sha(stdout)})
            if not ok:
                break
    finally:
        preserved = all(Path(row['source']).stat().st_size == row['bytes']
                        and sha(Path(row['source'])) == row['sha256']
                        and sha(Path(row['target'])) == row['sha256'] for row in inputs)
        final = {'format': 'has_synthetic_render_bounds_cpu_1', 'cases': reports,
                 'all_inputs_preserved': preserved, 'parent_environment_unchanged': dict(os.environ) == before_env,
                 'graphics_or_native_assets_used': False, 'native_qualification': 'UNRUN',
                 'stage': str(stage)}
        final['status'] = 'PASS' if len(reports) == 2 and all(r['status'] == 'PASS' for r in reports) and preserved and final['parent_environment_unchanged'] else 'FAIL'
        (stage / 'CPU_RESULT.json').write_text(json.dumps(final, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(final))
    return 0 if final['status'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
