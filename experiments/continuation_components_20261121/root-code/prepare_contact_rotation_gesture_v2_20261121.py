"""Keep the CRLF-anchor refusal; prepare against the exact pinned LF test source."""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
original=HERE/'prepare_contact_rotation_gesture_20261121.py';source=original.read_bytes()
failed=HERE/'source-contact-rotation-gesture-prep-20261121';assert failed.exists() and not (failed/'SOURCE_PINS.json').exists()
base=subprocess.check_output(['git','show','c31576d0c1d84030d51ec886f2f3976a60a70c7b:tests/contact_transform_smoke.gd'],cwd=ROOT)
assert b'\r' not in base and base.count(b'\n')>100
refusal={'status':'PREPARATION_REFUSED_BEFORE_PAYLOAD_WRITE','reason':'Pinned GDS fixture uses LF; initial exact CRLF anchor absent',
 'application_changed':False,'runtime_executed':False,'base_sha256':hashlib.sha256(base).hexdigest(),'script_sha256':hashlib.sha256(source).hexdigest()}
refusal_path=failed/'PREPARATION_REFUSAL.json';assert not refusal_path.exists();refusal_path.write_text(json.dumps(refusal,indent=2)+'\n')
old=b"DEST=ROOT/'output/source-contact-rotation-gesture-prep-20261121'"
new=b"DEST=ROOT/'output/source-contact-rotation-gesture-v2-prep-20261121'"
assert source.count(old)==1;source=source.replace(old,new,1)
# Change only the constructor's explicit escaped line endings; do not normalize input files.
assert source.count(b'\\r\\n')==4
source=source.replace(b'\\r\\n',b'\\n')
needle=b"rows=[]\n"
if needle not in source:needle=b"rows=[]\r\n"
assert source.count(needle)==1
extra=(b"put('code_used/prepare_contact_rotation_gesture_v2_20261121.py',(ROOT/'output/prepare_contact_rotation_gesture_v2_20261121.py').read_bytes())\n"
       b"put('code_used/executed_preparation.py',EXECUTED_SOURCE_RAW)\n"
       b"put('evidence/initial_preparation_refusal.json',(ROOT/'output/source-contact-rotation-gesture-prep-20261121/PREPARATION_REFUSAL.json').read_bytes())\n")
source=source.replace(needle,extra+needle,1)
exec(compile(source,str(original),'exec'),{'__file__':str(original),'__name__':'__main__','EXECUTED_SOURCE_RAW':source})
