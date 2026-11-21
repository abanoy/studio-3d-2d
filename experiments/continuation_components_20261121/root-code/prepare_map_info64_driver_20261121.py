from pathlib import Path
import hashlib
out=Path(__file__).resolve().parent
text=(out/'run_prepared_map64_20261121.py').read_text()
changes=[('source-prepared-map-editor-prep-20261121','source-prepared-map-editor-import-info-v2-prep-20261121'),('66a091596faa2c4531a2e27c4ba95c6ca7118f62bddaf1fb6753ffe1a44cb804','c7937e9febd4938425328144d986cbe47f3a9e71b0e23195d6d96f4c1d2e37a6'),("len(closure['files'])==327","len(closure['files'])==329"),('len(payload)==327','len(payload)==329'),('len(owned)==332','len(owned)==334'),('has-prepared-map-editor64-','has-prepared-map-editor-info64-'),("'has_prepared_map64_root_1'","'has_prepared_map_info64_root_1'")]
for old,new in changes:assert old in text;text=text.replace(old,new)
old="assert value['actual_current_app_and_SourceImport_completion'] is True and value['actual_Model_API_used'] is True"
assert text.count(old)==1;text=text.replace(old,old+" and value['import_info_overlay_composition'] is True")
path=out/'run_prepared_map_info64_20261121.py'
with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print(str(path),hashlib.sha256(path.read_bytes()).hexdigest())
