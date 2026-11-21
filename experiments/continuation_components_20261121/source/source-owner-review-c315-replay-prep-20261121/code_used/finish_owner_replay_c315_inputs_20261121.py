"""Bind the additional authored validation module; never import/run it."""
from pathlib import Path
import ast,hashlib,json
OUT=Path(__file__).resolve().parent;DEST=OUT/'source-owner-review-c315-replay-prep-20261121'
p=DEST/'review_validation.py';b=p.read_bytes();ast.parse(b)
old=DEST/'INPUT_PINS.json';v=json.loads(old.read_bytes());assert len(v['files'])==8
v['files'].append({'path':'review_validation.py','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
target=DEST/'HOST_INPUT_PINS.json';assert not target.exists();raw=(json.dumps(v,indent=2)+'\n').encode();target.write_bytes(raw)
print(json.dumps({'host_input_pin':[len(raw),hashlib.sha256(raw).hexdigest()],
 'validation_module_pin':[len(b),hashlib.sha256(b).hexdigest()]}))
