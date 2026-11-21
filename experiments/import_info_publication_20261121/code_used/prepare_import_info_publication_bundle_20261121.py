from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent
stage=(OUT/'stage_import_off_checkpoint_20261121.py').read_text().replace('IMPORT_OFF','IMPORT_INFO').replace('import-off','import-info')
stage=stage.replace("assert not git('diff','--cached','--check')","assert not git('diff','--cached','--check','--',*sorted(n for n in names if not n.startswith('experiments/continuation_components_20261121/')))")
with (OUT/'stage_import_info_checkpoint_20261121.py').open('x',encoding='utf-8',newline='\n') as f:f.write(stage)
remote=(OUT/'verify_import_off_remote_20261121.py').read_text().replace('IMPORT_OFF','IMPORT_INFO').replace('import_off','import_info').replace('==1103','==1109').replace("'functional_source_count':1103","'functional_source_count':1109")
with (OUT/'verify_import_info_remote_20261121.py').open('x',encoding='utf-8',newline='\n') as f:f.write(remote)
full=(OUT/'run_import_off_full_isolated_20261121.py').read_text().replace('has-import-off-full-20261121-','has-import-info-full-20261121-').replace('has_import_off_full_','has_import_info_full_')
with (OUT/'run_import_info_full_isolated_20261121.py').open('x',encoding='utf-8',newline='\n') as f:f.write(full)
contract=json.loads((OUT/'source-miku-contact-c315-1103-successor-prep-20261121/FULL182_GROUP_CONTRACT.json').read_bytes())
assert len(contract['expected_group_keys'])==182 and 'import_capability' not in contract['expected_group_keys']
contract['format']='has_exact_full183_group_contract_1';contract.pop('revision');contract['source_baseline']='c315 plus qualified Import info increment; actual committed revision bound by postflight argument and fresh remote proof';contract['expected_group_keys']=sorted(contract['expected_group_keys']+['import_capability']);contract['new_import_info_checks']=267;contract['functional_sources']=1109
(OUT/'FULL183_GROUP_CONTRACT_20261121.json').write_text(json.dumps(contract,indent=2)+'\n')
target=ROOT/'experiments/import_info_publication_20261121';assert not target.exists();target.mkdir();code=target/'code_used';code.mkdir()
for name in ['prepare_import_info_publication_20261121.py','prepare_import_info_publication_bundle_20261121.py','stage_import_info_checkpoint_20261121.py','verify_import_info_remote_20261121.py','run_import_info_full_isolated_20261121.py','verify_import_info_full183_root_20261121.py']:
 (code/name).write_bytes((OUT/name).read_bytes())
(target/'FULL183_GROUP_CONTRACT_20261121.json').write_bytes((OUT/'FULL183_GROUP_CONTRACT_20261121.json').read_bytes())
peer=OUT/'independent-components-archive-audit-20261121';dest=target/'independent_archive_audit';dest.mkdir()
for path in peer.iterdir():
 assert path.is_file();(dest/path.name).write_bytes(path.read_bytes())
(target/'README.md').write_text('''# Import info publication and fresh Full verification

The application/source increment is scoped-qualified, with1109 functional files
and183 canonical groups. The new aggregate is not claimed as passed here.
The companion continuation_components archive contains exact source packets,
failed/scoped evidence and the final source catalogue; this folder adds the
publication/remote/Full programs and an independent archive audit.

These are exact Root programs authored for execution from the repository output
folder. To reproduce, copy the applicable code_used programs and companion group
contract into a new owned output folder at repository root. Retrieve the required
selection/catalogue from saved evidence or regenerate against the explicit base;
do not run mutating publication programs blindly on an advanced checkout.

The Full caller accepts the freshly retrieved checkout and exact published
revision, isolates user folders and retains the unchanged source coordinator.
The postflight requires its retained Root process to have completed/reaped; it
audits exact source bytes,183 keys,267 Import info checks,626 editor/camera checks,
21 movie groups and every persisted current private receipt. Five authenticated
headless cases have lifecycle evidence; all graphical cases retain private
desktop confirmation. Human/device/clean-install evidence remains separate.
''',encoding='utf-8')
rows=[]
for path in sorted(target.rglob('*')):
 if path.is_file():
  raw=path.read_bytes();rows.append({'path':path.relative_to(target).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(target/'CONTENTS.json').write_text(json.dumps({'format':'has_import_info_publication_sources_1','files':rows,'new_Full_status':'REQUIRED_NOT_RUN'},indent=2)+'\n')
print(str(target),len(rows)+1)
