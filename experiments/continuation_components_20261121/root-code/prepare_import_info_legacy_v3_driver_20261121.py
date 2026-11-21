from pathlib import Path
out=Path(__file__).resolve().parent;text=(out/'run_import_info_legacy_scopes_20261121.py').read_text()
anchor="(studio/'override.cfg').write_text("
extra='''MMD=OUT/'source-import-info-missing-texture-v3-prep-20261121'
value=H.parse(H.read(MMD/'SOURCE_PINS.json',digest='57db4f1a5d8ee9951f51716deba0de1cdd2130cd6a3345de0697ef3c3afabcf3'))
for row in value['files']:H.read(MMD/H.rel(row['path']),row['bytes'],row['sha256'])
target=studio/'tests/mmd_missing_texture_smoke.gd';assert sha(target.read_bytes())=='aaaa50b191f7aff04501dafbbfc9f0bcaf2253b007e90e3964c521898d3e2626'
target.write_bytes(H.read(MMD/'payload/tests/mmd_missing_texture_smoke.gd',4015,'72d80b683017d90277d4cecb8d161581b27d4eda9c376918ba37018b9d2dfe6d'))
'''
assert text.count(anchor)==1;text=text.replace(anchor,extra+anchor).replace('has-import-info-legacy-scopes-','has-import-info-legacy-v3-scopes-').replace("'has_import_info_legacy_scopes_1'","'has_import_info_legacy_v3_scopes_1'")
target=out/'run_import_info_legacy_v3_scopes_20261121.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print(str(target))
