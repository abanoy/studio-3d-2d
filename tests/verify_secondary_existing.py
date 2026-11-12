"""Actual native Back hair existing-joint review, fan, restore and portable output."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'tools'))
import run
import secondary_helpers as helpers


def identity(path):
    return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'mtime_ns': path.stat().st_mtime_ns, 'bytes': path.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared-source', type=Path, required=True)
    parser.add_argument('--isolated-display')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--with-ribbon', action='store_true', help='Explicit known weighted-ribbon composition regression')
    parser.add_argument('--batch', action='store_true', help='Explicit one-edit ribbon plus Back hair setup on the pristine source')
    options = parser.parse_args()
    if options.batch and options.with_ribbon: parser.error('Batch starts from the pristine source; choose one explicit regression')
    if sys.platform == 'linux':
        if not options.isolated_display: parser.error('An explicit private display is required')
        run.configure_private_display(options.isolated_display)
    source = options.prepared_source.resolve(strict=True)
    pristine_sha = '4b23dbf5dfc402a08871d392143efa687dc10b869fc9344aa3f565099947e1f2'
    expected_sha = '4d62236d5c34468ea1f91c43089d6ce3c193be27b8460d53ea8d91d2238ab7b5' if options.with_ribbon else pristine_sha
    if identity(source)['sha256'] != expected_sha:
        parser.error('This exact native Back hair regression requires the supplied prepared player GLB')
    ribbon_report = None
    if options.with_ribbon:
        glb = helpers.GLB(source); springs = glb.springs()
        assert len(springs) == 1 and len(springs[0]['joints']) == 4
        joint_nodes = [j['node'] for j in springs[0]['joints']]
        ribbon_report = glb.doc['nodes'][joint_nodes[0]]['extras']['has_generated_helper']['authoring']
        assert ribbon_report['source_sha256'] == pristine_sha and ribbon_report['helper_nodes'] == joint_nodes
        assert (ribbon_report['region']['node'], ribbon_report['region']['primitive'], ribbon_report['region']['component'],
                ribbon_report['region']['anchor_name']) == (85, 0, 2, 'hair_ribbon_left')
    parameters = source.with_name('parameters.json')
    if not parameters.is_file(): parser.error('The native input requires its parameters.json sibling')
    originals = {str(p): identity(p) for p in (source, parameters)}
    folder = (options.output or ROOT/'output/secondary-existing-native'/str(time.time_ns())).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    source_paths = sorted([*ROOT.glob('src/*.gd'),*ROOT.glob('src/*.gdshader'),ROOT/'main.tscn',ROOT/'project.godot',
        ROOT/'tools/secondary_helpers.py',ROOT/'tools/secondary_helpers_batch.py',ROOT/'tools/secondary_helper_worker.py',
        ROOT/'tests/secondary_existing_native_smoke.gd',Path(__file__)])
    source_hashes = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    (folder/'source-sha256.json').write_text(json.dumps(source_hashes,indent=2)+'\n',encoding='utf-8')
    staged = folder/'input'; staged.mkdir()
    for path in (source, parameters): shutil.copy2(path, staged/path.name)
    (folder/'input-provenance.json').write_text(json.dumps({'with_ribbon': options.with_ribbon,
        'input_sha256': expected_sha, 'pristine_sha256': pristine_sha, 'ribbon_report': ribbon_report},indent=2)+'\n',encoding='utf-8')
    args = run.command('tests/secondary_existing_native_smoke.gd', extra=[
        '--audio-driver', 'Dummy', '--log-file', str(folder/'engine.log'),
        '--', str(folder), str(staged/source.name)] + (['--with-ribbon'] if options.with_ribbon else []) + (['--batch'] if options.batch else []))
    with (folder/'stdout.log').open('w', encoding='utf-8') as log:
        p = subprocess.run(args, cwd=ROOT, stdout=log, stderr=log, timeout=190)
    text = (folder/'stdout.log').read_text(encoding='utf-8', errors='replace')
    if p.returncode or any(marker in text for marker in
                           ['SCRIPT ERROR', 'SHADER ERROR', 'ERROR:', 'FAIL ', 'ObjectDB instances leaked']):
        raise RuntimeError(f'Native existing-joint test failed; inspect {folder}')
    result = json.loads((folder/'result.json').read_bytes()); assert result['failures'] == 0
    receipt = None
    if os.name == 'nt':
        receipt = json.loads(Path(args[args.index('--receipt')+1]).read_bytes())
        assert (receipt['exit'] == 0 and receipt['child_desktop_confirmed'] and
                not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'])
    encoder = os.environ.get('HYBRID_FFMPEG', '')
    sibling = Path(encoder).with_name('ffprobe.exe' if os.name == 'nt' else 'ffprobe') if encoder else None
    ffprobe = str(sibling) if sibling and sibling.is_file() else shutil.which('ffprobe') or 'ffprobe'
    media = json.loads(subprocess.check_output([ffprobe, '-v', 'error', '-count_frames',
        '-show_streams', '-of', 'json', result['movie']]))
    video = next(s for s in media['streams'] if s['codec_type'] == 'video')
    assert (video['codec_name'], video['width'], video['height'], video['r_frame_rate'],
            video['nb_read_frames'], float(video['duration'])) == ('h264', 1920, 1080, '24/1', '24', 1.)
    assert not any(s['codec_type'] == 'audio' for s in media['streams'])
    assert all(identity(Path(path)) == before for path, before in originals.items())
    assert source_hashes == {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}, 'Runtime changed during native verification'
    proof = {'result': result, 'originals': originals, 'private_receipt': receipt, 'with_ribbon': options.with_ribbon, 'batch': options.batch,
             'video': {k: video[k] for k in ['codec_name', 'width', 'height', 'r_frame_rate', 'nb_read_frames', 'duration']},
             'scope': 'Actual prepared native player Back hair; same-process packed reopen, not a cold-machine or artist fidelity certification'}
    (folder/'verification.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__': main()
