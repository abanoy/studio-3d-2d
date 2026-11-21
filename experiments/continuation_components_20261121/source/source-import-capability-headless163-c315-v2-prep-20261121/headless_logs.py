"""Headless163 result admission only; no launcher or old fixed-stage validator."""
from pathlib import Path
import re
MAX_LOG=8*1024*1024
BAD=re.compile(r'SCRIPT ERROR|SHADER ERROR|FAIL |ObjectDB instances leaked|_set_transient_exclusive_child|^ERROR:',re.M)
def validate_logs(H,job,record):
    text=[]
    for leaf in ('godot-stdout.log','godot-stderr.log'):
        text.append(H.read(record/leaf,limit=MAX_LOG).decode('utf-8','replace'))
    engine=H.read(Path(job['args'][job['args'].index('--log-file')+1]),limit=MAX_LOG).decode('utf-8','replace')
    H.need(not BAD.search('\n'.join([*text,engine])),'HEADLESS_ERROR_ASSERTION_OR_LEAK')
    hits=[line[len(job['expected_marker']):] for line in text[0].splitlines() if line.startswith(job['expected_marker'])]
    H.need(len(hits)==1,'EXACT_ONE_HEADLESS_MARKER');value=H.parse(hits[0]);expected=job['expected_checks']
    H.need(type(value.get('checks')) is int and value['checks']==expected and type(value.get('failures')) is int and value['failures']==0,'EXACT_HEADLESS_COUNT')
    H.need(sum(line.startswith('PASS ') for line in text[0].splitlines())==expected,'EXACT_HEADLESS_PASS_LINES')
    if job['name']=='unit':H.need(value.get('legacy_controls')==43 and value.get('native_assets_used') is False,'LEGACY43_SCOPE')
    else:H.need(value.get('actual_app') is True and value.get('headless') is True and value.get('native_worker_started') is False and value.get('graphics_qualified') is False and value.get('application_adopted') is False,'ACTUAL_APP_HEADLESS_SCOPE')
    return value
