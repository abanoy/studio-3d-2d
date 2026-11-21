"""Read source text only; no imports, processes, file moves or native tools."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
DEST=OUT/'source-easing-cpu-cleanup-readiness-prep-20261121'
NAMES=('has-easing-headless-1795254145851799500','has-easing435-app-cpu-1795254384845561100',
 'has-easing435-app-cpu-1795254695259497400','has-easing435-app-cpu-1795254761995523000',
 'has-easing-headless-1795254831934151300','has-easing435-graphics-parse-1795258322734840400',
 'has-easing-c315-graphics-parse-1795260866931895900')
PACKETS=('source-easing-c315-graphics-qualification-prep-20261121',
 'source-miku-contact-c315-1103-successor-prep-20261121',
 'source-posed-head-native-c315-1103-qualification-prep-20261121')
rows=[];hits=[]
for name in PACKETS:
 base=OUT/name
 for p in sorted(base.rglob('*')):
  if not p.is_file() or p.suffix not in ('.py','.gd','.md','.json'):continue
  raw=p.read_bytes();text=raw.decode('utf-8-sig');relative=p.relative_to(base).as_posix()
  runtime=(relative in ('run_easing_graphics.py','run_miku_contact_qualification.py','run_posed_head_controls.py',
       'source1103.py','qualified_helpers.py','qualified_ui_host.py') or relative.startswith('payload/'))
  if runtime:rows.append({'packet':name,'path':relative,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
  for line_no,line in enumerate(text.splitlines(),1):
   for stage in NAMES:
    if stage in line:
     hits.append({'packet':name,'path':relative,'line':line_no,'stage':stage,'runtime_entry_or_dependency':runtime,
        'classification':'runtime_dependency_REQUIRES_REVIEW' if runtime else 'copied_provenance_or_authoring_only_reference',
        'excerpt':line[:400]})
for name in ('experiments/reference_body_20261120/run_full.py','experiments/reference_body_20261120/stage_legacy_inputs.py','tests/verify.py'):
 p=ROOT/name;raw=p.read_bytes();text=raw.decode('utf-8-sig')
 rows.append({'packet':'current_c315_full_source','path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
 for no,line in enumerate(text.splitlines(),1):
  for stage in NAMES:
   if stage in line:hits.append({'packet':'current_c315_full_source','path':name,'line':no,'stage':stage,'runtime_entry_or_dependency':True,'classification':'runtime_dependency_REQUIRES_REVIEW','excerpt':line[:400]})
value={'format':'has_easing_cpu_future_host_text_dependencies_1','status':'SOURCE_TEXT_AUDIT_ONLY','scanned_runtime_sources':rows,
 'exact_stage_name_references':hits,'runtime_exact_stage_dependencies':[r for r in hits if r['runtime_entry_or_dependency']],
 'dynamic_dependencies_not_generally_proven_by_text_scan':True,
 'actual_reviewed_runtime_contract':'New hosts build from immutable c315 Git sources and local packet copies; parse evidence is already copied, not read from old stage by runtime entry.',
 'old_authoring_reproduction':'After deletion, collectors that explicitly copy old-stage evidence require restoration of exact preserved artifacts at their original paths first.',
 'no_cleanup_authorization':True}
p=DEST/'FUTURE_HOST_DEPENDENCIES.json';assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'runtime_sources_scanned':len(rows),'text_references':len(hits),'runtime_exact_stage_dependencies':len(value['runtime_exact_stage_dependencies'])}))
