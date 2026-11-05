"""One owned, cancellable local shape study with an atomic bounded result."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time
from shape_observations import observe
from secondary_helpers import unique


def work(source, folder):
    folder = Path(folder); started = time.monotonic(); request = {}
    try:
        path = folder / 'request.json'
        if path.stat().st_size > 1024 * 1024: raise ValueError('Deform study request exceeds1MiB')
        request = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)
        if not isinstance(request, dict) or request.get('format') != 'studio_shape_study_request_1': raise ValueError('Invalid deform study request')
        job = request.get('job_id')
        if not isinstance(job, str) or not job.isascii() or not job.isdecimal() or len(job) > 30: raise ValueError('Invalid deform study identity')
        if not isinstance(request.get('seeds'), dict): raise ValueError('Missing labelled study seeds')
        if (folder / 'cancel').exists(): raise ValueError('Deform study cancelled')
        if Path(source).stat().st_size > 128 * 1024 * 1024: raise ValueError('Deform source exceeds128MiB')
        if hashlib.sha256(Path(source).read_bytes()).hexdigest() != request['seeds'].get('source_sha256'): raise ValueError('Deform source changed before study')
        def cancelled():
            if time.monotonic() - started > 120: raise ValueError('Deform study timed out')
            return (folder / 'cancel').exists()
        report = observe(source, request['seeds'], cancelled)
        if cancelled(): raise ValueError('Deform study cancelled')
        result = {'format': 'studio_shape_study_result_1', 'job_id': job, 'ok': True, 'value': report}
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if len(encoded) > 8 * 1024 * 1024: raise ValueError('Deform study report exceeds8MiB')
    except Exception as error:
        encoded = json.dumps({'format': 'studio_shape_study_result_1', 'job_id': request.get('job_id', '') if isinstance(request, dict) else '', 'ok': False, 'error': str(error)}).encode('utf-8')
    temporary = folder / 'result.json.tmp'
    with temporary.open('xb') as stream: stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    if (folder / 'result.json').exists(): raise ValueError('Study result already exists')
    os.replace(temporary, folder / 'result.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('source'); parser.add_argument('folder')
    options = parser.parse_args(); work(options.source, options.folder)


if __name__ == '__main__': main()
