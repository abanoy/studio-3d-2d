"""Derive an independently pinned attempt2 coordinator; preserve attempt1 code."""
from pathlib import Path
source=Path(__file__).with_name('run_owned.py')
body=source.read_text(encoding='utf-8')
for old,new in [('normal-boundary-20261116-attempt1','normal-boundary-20261116-attempt2'),('normal_boundary_probe_20261116','normal_boundary_probe_sentinel_20261116'),('49e7f5067be896b2faab57ae41f3afb2089a94a55b9988ea35150e4227f73856','a2475b28c03c6b87cc0d98d537433204b9553122a97f1197321455a491e2ef64'),('69c521fead52d27d0798868e64cfb4e20b531a7ad65421f148fdb0bb610d918e','9462405eeb4d909c7c5bd8394f89926b1b864f94937869bf1992aae3dc7d7b02')]:
    assert body.count(old)==1;body=body.replace(old,new,1)
anchor='    comparison=None;result={}'
old="    for name,row in load(PACKET/'INDEX.json')['files'].items():"
new="    rows=load(PACKET/'INDEX.json')['files']\n    entries=rows.items() if isinstance(rows,dict) else ((row['path'],row) for row in rows)\n    for name,row in entries:"
assert body.count(old)==1;body=body.replace(old,new,1)
extra='''    required=load(PACKET/'ROOT_ADDITIONAL_REQUIREMENTS.json')['public_field_required_values']
    policy=public.get('background_isolation_sentinel',{})
    capture_ok=capture_ok and receipt.get('private_window_seen') is True and 'HAS_NORMAL_ISOLATION_SENTINEL ' in stdout and all(type(policy.get(k)) is type(v) and policy.get(k)==v for k,v in required.items())
'''
assert body.count(anchor)==1;body=body.replace(anchor,extra+anchor,1)
target=source.with_name('run_sentinel_owned.py')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
print(str(target))
