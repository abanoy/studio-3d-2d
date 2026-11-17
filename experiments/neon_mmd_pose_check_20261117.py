"""Run the unchanged canonical pose command and require owner MMD evidence."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
sys.path.insert(0, str(REVIEW))
from run import command


def main():
    fixture = REVIEW / 'output/compatibility/miku-tested/scene.glb'
    before = hashlib.sha256(fixture.read_bytes()).hexdigest()
    arguments = command(None, False, ['--', '--pose-smoke', '--demo-room'])
    receipt_path = Path(arguments[arguments.index('--receipt') + 1])
    child = subprocess.Popen(arguments, cwd=REVIEW,
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    out, err = child.communicate(timeout=180)
    private = REVIEW / 'output/pose-smoke'
    (private / 'root-focused-stdout.log').write_bytes(out)
    (private / 'root-focused-stderr.log').write_bytes(err)
    assert child.poll() is not None and child.returncode == 0
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['format'] == 'studio_private_desktop_1' and receipt['exit'] == 0
    assert all(receipt.get(key) is True for key in (
        'private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed'))
    assert all(receipt.get(key) is False for key in ('desktop_switch_requested', 'foreground_child_observed'))
    assert not any(receipt.get(key) for key in ('error', 'monitor_error', 'desktop_enumeration_error', 'cancelled'))
    text = (out + err).decode('utf-8', 'replace')
    assert 'POSE_SMOKE ' in text and not any(marker in text for marker in (
        'SCRIPT ERROR', 'SHADER ERROR', 'Shader compilation failed', 'FAIL ',
        'ObjectDB instances leaked', 'SKIP actual MMD sample absent'))
    report = json.loads((private / 'result.json').read_bytes())
    assert report['checks'] == 45 and report['failures'] == 0
    assert report['actual_mmd_tested'] is True and len(report['movies']) == 2
    ffprobe = Path(os.environ['HYBRID_FFMPEG']).with_name('ffprobe.exe')
    for movie in report['movies']:
        probe = subprocess.Popen([str(ffprobe), '-v', 'error', '-count_frames',
            '-show_streams', '-show_format', '-of', 'json', movie],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW)
        raw, errors = probe.communicate(timeout=30)
        assert probe.poll() is not None and probe.returncode == 0 and not errors.strip()
        metadata = json.loads(raw)
        video = next(row for row in metadata['streams'] if row['codec_type'] == 'video')
        assert video['codec_name'] == 'h264' and video['nb_read_frames'] == '48'
        assert video['width'] == 1920 and video['height'] == 1080 and video['r_frame_rate'] == '24/1'
        assert abs(float(metadata['format']['duration']) - 2) < .01
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == before
    print('PASS unchanged canonical pose: 45 checks, native MMD, two independently probed movies')


if __name__ == '__main__':
    main()
