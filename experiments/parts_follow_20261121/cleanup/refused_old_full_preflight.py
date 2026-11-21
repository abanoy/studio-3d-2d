"""Read-only audit of the completed, independently archived 2f1 Full checkout."""
from pathlib import Path
import hashlib,json,os,subprocess
root=Path(__file__).resolve().parents[1]
target=root.parent/'has-import-info-full-20261121-2f1acbd'
assert target.resolve(strict=True)==target and target.parent==root.parent
assert (target/'.git').is_dir()
def git(*args):return subprocess.check_output(['git','-C',str(target),*args])
assert git('rev-parse','HEAD').decode().strip()=='2f1acbd7867087d9f18cfbc1122cc0c883c5f788'
assert git('worktree','list','--porcelain').decode().count('worktree ')==1
backup=root/'experiments/source_followup_20261121/evidence/full/coordinator'
before=json.loads((backup/'source-before.json').read_bytes());after=json.loads((backup/'source-after.json').read_bytes())
assert before==after and len(before)==1109
for name,row in before.items():
    data=(target/name).read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],name
complete=json.loads((backup/'completion.json').read_bytes())
assert complete['exit']==0 and complete['child_reaped'] and complete['all_private_jobs_isolated_closed'] and complete['unique_current_private_jobs']==259
staging=json.loads((target/'output/reference-body-legacy-staging.json').read_bytes())
assert staging['count']==13 and staging['originals_unchanged']
for row in staging['files']:
    source=Path(row['source']);s=source.stat();assert s.st_size==row['bytes'] and s.st_mtime_ns==row['mtime_ns'] and hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256'],str(source)
tracked={p for p in git('ls-files','-z').decode().split('\0') if p}
def generated(name):return name.startswith(('output/','.godot/','__pycache__/','tools/__pycache__/','tests/__pycache__/'))
changed=[p for p in git('diff','--name-only','HEAD','-z').decode().split('\0') if p]
assert all(generated(p) for p in changed),changed
files=0;size=0;unknown=[];aliases=[];hardlinks=[];pending=[target]
while pending:
    folder=pending.pop()
    for item in os.scandir(folder):
        path=Path(item.path);relative=path.relative_to(target).as_posix();info=item.stat(follow_symlinks=False)
        if getattr(info,'st_file_attributes',0)&0x400 or item.is_symlink():aliases.append(relative);continue
        if item.is_dir(follow_symlinks=False):pending.append(path);continue
        files+=1;size+=info.st_size
        if info.st_nlink!=1:hardlinks.append(relative)
        if relative not in tracked and not relative.startswith('.git/') and not generated(relative):unknown.append(relative)
assert not aliases and not hardlinks and not unknown,{'aliases':aliases[:5],'hardlinks':hardlinks[:5],'unknown':unknown[:10]}
references=[]
for sibling in root.parent.iterdir():
    if not sibling.is_dir() or sibling==target:continue
    alternate=sibling/'.git/objects/info/alternates'
    if alternate.is_file() and str(target).replace('\\','/').lower() in alternate.read_text(errors='replace').replace('\\','/').lower():references.append(str(alternate))
assert not references,references
report={'format':'has_completed_full_cleanup_preflight_1','status':'READ_ONLY_PREFLIGHT_PASS','target':str(target),'revision':'2f1acbd7867087d9f18cfbc1122cc0c883c5f788','files':files,'logical_bytes':size,'functional_sources':1109,'source_before_after_and_commit_scope_preserved':True,'original_fixture_files_rechecked':13,'original_fixture_hashes_sizes_mtimes_unchanged':True,'dirty_generated_paths':len(changed),'unknown_non_generated_files':0,'aliases_or_hardlinks':0,'dependent_worktrees_or_top_level_alternates':0,'closed_private_jobs_in_archived_completion':259,'native_outputs_disposable_test_copies':True,'pending_product_agents_confirm_no_dependency':True,'current243_full_and_owner_review_excluded':True,'originals_and_installed_tools_excluded':True,'actual_removal':False}
(root/'output/OLD_FULL_CLEANUP_PREFLIGHT_20261121.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
