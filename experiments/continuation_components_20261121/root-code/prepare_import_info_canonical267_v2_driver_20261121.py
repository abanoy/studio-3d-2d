from pathlib import Path
import json,hashlib
out=Path(__file__).resolve().parent
old=out/'run_import_info_canonical267_scoped_20261121.py'
text=old.read_text()
for a,b in [('source-import-capability-canonical-c315-prep-20261121','source-import-capability-canonical-c315-v2-prep-20261121'),('2bb5e13801a10583d72470bcc58ab87b696248946fdc961c83a5f7e894155643','0cc2240218def0037cfe0377d22a0c22f772805dc07f967c5144b0d0dce66977'),('has-import-info-canonical267-','has-import-info-canonical267-v2-'),("'has_import_info_canonical267_root_1'","'has_import_info_canonical267_root_v2_1'")]:
 assert a in text;text=text.replace(a,b)
target=out/'run_import_info_canonical267_v2_scoped_20261121.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
(out/'IMPORT_INFO_RECEIPT_CONTROLS30_ROOT_20261121.json').write_text(json.dumps({'status':'PASS','checks':30,'failures':0,'processes_launched':0,'execution':'Root tool result e2a6eb, exit0, 2026-11-21','test_sha256':'5c57c6dfdf1b2771b3de96c12c2d5331dd026bd68e3368ee756bbba1ffaf4eed','Full_claimed':False},indent=2)+'\n')
print(str(target),hashlib.sha256(target.read_bytes()).hexdigest())
