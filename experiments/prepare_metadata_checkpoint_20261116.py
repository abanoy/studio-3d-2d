"""Catalogue only finished, reviewed continuation source and compact evidence."""
from pathlib import Path
import gzip,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
FOLDERS=['current_full_receipts_20261116','full_native_five_20261116','native_five_full_actual_20261116','native_five_full_preflight_20261116','native_five_remote_readback_20261116',
 'native_five_review_actual_20261116','native_five_review_actual_packet_20261116','native_five_review_after_full_20261116','normal_boundary_actual_20261116','normal_boundary_probe_20261116',
 'normal_boundary_probe_actual_20261116','normal_boundary_probe_sentinel_20261116','normal_rounding_source_followup_20261116','six_foot_boundary_review_20261116',
 'six_foot_domain_actual_20261116','six_foot_domain_initial_actual_packet_20261116','six_foot_import_basis_candidate_20261116','six_foot_import_basis_gd_candidate_20261116','six_foot_independent_review_20261116']
FILES=['LLM.md','docs/progress_memo.md','docs/NEXT_SESSION_PLAN_2026-11-15.md','docs/NEXT_SESSION_PLAN_2026-11-16.md','docs/RESUME_MASTER_PLAN.md','docs/completion_checklist.json','docs/completion_checklist.md',
 'docs/benchmarks/native_five_full_2026-11-16.json','docs/benchmarks/native_five_owner_review_2026-11-16.json','docs/benchmarks/source_normal_boundary_2026-11-16.json','docs/benchmarks/six_foot_gd_initial_2026-11-16.json',
 'experiments/record_full_pass_20261116.py','experiments/record_followup_progress_20261116.py','experiments/prepare_metadata_checkpoint_20261116.py']
for name in FOLDERS:
    folder=ROOT/'experiments'/name;assert folder.is_dir()
    FILES.extend(p.relative_to(ROOT).as_posix() for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
paths=sorted(set(FILES));blocked={'.glb','.gltf','.vrm','.pmx','.pmd','.mdl','.vvd','.vtx','.vtf','.png','.jpg','.jpeg','.wav','.mp3','.mp4','.has','.kra','.zip','.rar','.bin','.dll','.exe','.blend'}
rows=[]
for name in paths:
    p=ROOT/name;assert p.resolve().is_relative_to(ROOT.resolve()) and not p.is_symlink() and p.suffix.lower() not in blocked
    body=p.read_bytes()
    if p.suffix=='.gz':json.loads(gzip.decompress(body))
    else:
        assert b'\0' not in body;body.decode('utf-8-sig')
        if p.suffix=='.json':json.loads(body)
    rows.append({'path':name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
before=json.loads((ROOT/'output/windows-canonical-bone-binding-20261116T041518335/source-before.json').read_bytes())
assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in before['source_sha256'].items())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='52f63c944ded7a651da871524d23a345b606424d'
target=ROOT/'output/metadata-checkpoint-20261116-manifest.json'
with target.open('x',encoding='utf-8',newline='\n') as f:json.dump({'format':'has_finished_continuation_metadata_checkpoint_1','files':rows,'functional_source_files_unchanged':1019,'active_source_drafts_excluded':True},f,indent=2);f.write('\n')
print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'source1019_unchanged':True,'manifest':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
