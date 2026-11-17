"""Concrete copy-only successor. Activation and all qualification IO belong to Q.

This module never launches an application, installs a tool, deletes or overwrites
an existing file. Actual build execution is disabled until Q admits a future
sealed full-PASS/root-closure/merged-source activation.
"""
from pathlib import Path,PurePosixPath
from types import SimpleNamespace
import ast,hashlib,json,os,re,shutil,stat,subprocess,time,zipfile

HERE=Path(__file__).resolve().parent
REFERENCE_SHA='a09361bf71593cc7ddc38af31e096abe97338a0437077b1cbff2e6558eca6f1e'
FUNCTIONS={'need','no_links','guarded','identity','tree','exporter_sources','source_map',
           'git_blobs','write_new','copy_new','package_readback'}
PIN='fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
FUNCTIONAL=('src','tests','tools','data','examples')
ENTRY=('project.godot','main.tscn','run.py','launch.pyw')

def helpers(root):
    """Load exact old helper ASTs only; never import its main/admission module."""
    raw=(HERE/'reference_builder.py').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=REFERENCE_SHA:raise RuntimeError('Pinned old builder source differs')
    nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in FUNCTIONS]
    if len(nodes)!=len(FUNCTIONS) or {n.name for n in nodes}!=FUNCTIONS:raise RuntimeError('Pinned helper function set differs')
    root=Path(root).absolute()
    namespace={'Path':Path,'PurePosixPath':PurePosixPath,'hashlib':hashlib,'json':json,'os':os,
               'shutil':shutil,'stat':stat,'subprocess':subprocess,'zipfile':zipfile,
               'ROOT':root,'WORKSPACE':root.parent,'FUNCTIONAL':FUNCTIONAL,'ENTRY':ENTRY,
               'PIN':PIN,'SOURCEIO':root/'output/dependencies'/('sourceio-'+PIN),
               'NATIVE_RUN':root/'output/sfm-bone-bindings-native-launch-20261114T033026205/run'}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact pinned old owner-copy helpers>','exec'),namespace)
    return SimpleNamespace(**{k:v for k,v in namespace.items() if k in FUNCTIONS or k in
                              {'ROOT','WORKSPACE','FUNCTIONAL','ENTRY','PIN','SOURCEIO','NATIVE_RUN'}})

def _relative(name):
    if type(name) is not str or not name or '\\' in name or ':' in name or any(p in ('','.','..') for p in name.split('/')) or PurePosixPath(name).is_absolute():
        raise RuntimeError('Canonical relative source name required')
    return Path(name)

def _write_blob(H,target,boundary,raw,expected_sha256):
    """Exclusive exact Git-support blob primitive; no EOL reconstruction."""
    H.need(type(raw) is bytes and type(expected_sha256) is str and re.fullmatch('[a-f0-9]{64}',expected_sha256)
           and hashlib.sha256(raw).hexdigest()==expected_sha256,'Support blob bytes differ')
    target=H.guarded(target,boundary);H.need(not target.exists(),'Support destination already exists')
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(raw)
    H.need(H.identity(target)['sha256']==expected_sha256,'Exclusive support copy differs')

def _write_text(H,path,boundary,value):
    path=H.guarded(path,boundary)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(value)

def _gate_files(H,rows,label):
    H.need(type(rows) is dict and rows,label+' identities missing')
    H.need(all(H.identity(Path(path))==expected for path,expected in rows.items()),label+' identity changed')

def build(admitted):
    # No external source/native/qualification path is read before this token gate.
    import qualified_inputs as Q
    Q.assert_admitted(admitted)
    d=admitted.data
    root=Path(d['root']).absolute();workspace=Path(d['workspace']).absolute();final=Path(d['final']).absolute()
    H=helpers(root);need=H.need
    merged=d['merged_revision'];candidate=d['candidate_commit'];lock=d['lock']
    need(re.fullmatch('[a-f0-9]{40}',merged) and re.fullmatch('[a-f0-9]{40}',candidate),'Exact admitted revisions required')
    H.guarded(root,workspace);H.guarded(final,workspace)
    need(root.parent==workspace and final.parent==workspace and final.name=='HAS-Review-Neon-'+merged[:7]+'-native'
         and not final.exists(),'Exact fresh owner-review sibling required')
    old_review=Path(d['old_review']).absolute()
    need(old_review.parent==workspace and old_review.is_dir() and final!=old_review,'Protected owner review missing')
    need(not (root/'override.cfg').exists() and not (root/'project.binary').exists(),'Unreviewed startup override refused')
    identities=d['source_identities'];functional_hashes=d['source_hashes']
    need(type(identities) is dict and len(identities)==1029 and set(identities)==set(functional_hashes)
         and H.source_map()==functional_hashes,'Exact qualified functional source inventory differs')
    for name,row in identities.items():
        source=H.guarded(root/_relative(name),root)
        need(H.identity(source)==row and row['sha256']==functional_hashes[name],'Tested raw source identity differs: '+name)
    extra=d['support_source_blobs'];extra_hashes=d['support_source_hashes']
    need(type(extra) is dict and type(extra_hashes) is dict and set(extra)==set(extra_hashes)
         and not set(extra)&set(identities),'Committed support inventory differs')
    names=[*identities,*extra]
    need(len({n.casefold() for n in names})==len(names),'Source/support case collision')
    for name,raw in extra.items():
        _relative(name)
        need(name.split('/')[0] not in FUNCTIONAL and name not in ENTRY,
             'Functional file cannot be admitted as committed support')
        need(name.split('/')[0] not in ('.git','.godot','output') and name not in ('override.cfg','project.binary'),
             'Generated or startup support payload refused')
        need(type(raw) is bytes and hashlib.sha256(raw).hexdigest()==extra_hashes[name],'Committed support hash differs')
    need(type(d['support_catalogue_identity']) is dict and d['support_catalogue_identity'],'Committed support provenance missing')
    need(len(lock['runtime_executables'])==6 and len(lock['sourceio_files'])==574
         and len(lock['exporter_noncache_sources'])==120 and len(lock['projects'])==4 and len(lock['source_chooser'])==4,
         'Inherited fixed input-lock scope differs')
    native_path=H.NATIVE_RUN/'verification.json'
    need(H.identity(native_path)==lock['native_verification'],'Original native verification identity differs')
    native=json.loads(native_path.read_bytes())
    need(native.get('passed') is True and all(v is True for v in native['preservation'].values())
         and H.identity(native_path)==lock['native_verification'],'Original four-case DATA verification changed')
    sourceio_before=H.tree(H.SOURCEIO)
    need(sourceio_before==lock['sourceio_files'] and (H.SOURCEIO/'LICENSE').is_file(),'Original approved SourceIO differs')
    runtimes_before={path:H.identity(Path(path)) for path in lock['runtime_executables']}
    need(runtimes_before==lock['runtime_executables'],'Approved runtime fingerprints differ')
    exporter=Path(lock['exporter_root'])
    need(H.exporter_sources(exporter)==lock['exporter_noncache_sources'],'Installed exporter source catalogue differs')
    families=lock['native_families']
    need(sum(len(rows) for rows in families.values())==495
         and sum(row['bytes'] for rows in families.values() for row in rows.values())==451266730,
         'Exact complete native family scope differs')
    need(all(H.tree(Path(path))==rows for path,rows in families.items()),'Original complete native family differs')
    for project in lock['projects']:
        need(H.identity(Path(project['source']))==project['identity'],'Original packed DATA example differs')
        H.package_readback(Path(project['source']))
    protected={str(path):H.tree(path) for path in sorted(workspace.glob('HAS-Review-*')) if path.is_dir()}
    need(str(old_review) in protected,'Protected owner review was not captured')
    full_gate=d['full_gate'];preparation=d['preparation']
    _gate_files(H,full_gate,'Qualified full/root release')
    _gate_files(H,preparation,'Reviewed executor preparation')
    # Recheck admitted sealed data before the first mutation; refusal leaves no target.
    Q.assert_admitted(admitted)
    profile='HAS Neon Native Review '+merged[:7]+' '+str(time.time_ns())
    final.mkdir(exist_ok=False)
    H.write_new(final/'BUILD-STARTED.json',{'merged_revision':merged,'candidate_commit':candidate,
                 'graphics_launched':False,'source_mode':'candidate_tested_raw_bytes_with_reviewed_Git_EOL_bridge'})
    studio=final/'Studio';studio.mkdir(exist_ok=False)
    for name,row in identities.items():H.copy_new(root/_relative(name),studio/_relative(name),final,row)
    for name,raw in extra.items():_write_blob(H,studio/_relative(name),final,raw,extra_hashes[name])
    need(not (studio/'output').exists() and not (studio/'.godot').exists() and not (studio/'.git').exists()
         and not (studio/'override.cfg').exists(),'Copied Studio is not a clean unlaunched snapshot')
    _write_text(H,studio/'override.cfg',final,'[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n')
    dependency=final/'Dependencies'/('sourceio-'+PIN)
    for name,row in sourceio_before.items():H.copy_new(H.SOURCEIO/name,dependency/name,final,row)
    projects=[]
    for row in lock['projects']:
        target=final/'Examples'/(row['title']+'.has')
        H.copy_new(Path(row['source']),target,final,row['identity'])
        projects.append({'title':row['title'],'file':target.relative_to(final).as_posix(),
                         **H.identity(target),**H.package_readback(target)})
    native_rows=[]
    for row in lock['source_chooser']:
        source_root=Path(row['resource_root']);destination=final/'Native sources'/row['folder']
        for name,expected in families[str(source_root)].items():H.copy_new(source_root/name,destination/name,final,expected)
        native_rows.append({'name':row['name'],'MDL':(destination/row['relative_MDL']).relative_to(final).as_posix()})
    runtime=lock['runtime_paths']
    lines=['@echo off','setlocal','set "HYBRID_PYTHON='+runtime['python']+'"','set "HYBRID_GODOT='+runtime['godot']+'"',
           'set "HYBRID_FFMPEG='+runtime['ffmpeg']+'"','set "HYBRID_SOURCE_BLENDER='+runtime['blender']+'"',
           'set "HYBRID_SOURCEIO=%~dp0Dependencies\\sourceio-'+PIN+'"','set "PYTHONDONTWRITEBYTECODE=1"']
    def launcher(name,project=None):
        command='start "" "'+runtime['pythonw']+'" "%~dp0Studio\\launch.pyw"'
        if project is not None:command+=' "%~dp0'+project.replace('/','\\')+'"'
        _write_blob(H,final/name,final,('\r\n'.join([*lines,command])+'\r\n').encode('utf-8'),
                    hashlib.sha256(('\r\n'.join([*lines,command])+'\r\n').encode('utf-8')).hexdigest())
    launcher('Start review.bat')
    for project in projects:launcher('Open '+project['title']+'.bat',project['file'])
    guide=(HERE/'README.template.md').read_text(encoding='utf-8').replace('{{MERGED_REVISION}}',merged).replace('{{CANDIDATE_COMMIT}}',candidate)
    _write_text(H,final/'README.md',final,guide)
    H.write_new(final/'Native-source-chooser.json',{'format':'has_private_SFM_source_chooser_1','models':native_rows})
    # No cleanup or rollback: an unexpected failure retains the owned partial copy.
    need(H.source_map()==functional_hashes and all(H.identity(root/name)==row for name,row in identities.items()),
         'Qualified raw main source changed during copy')
    need(H.tree(H.SOURCEIO)==sourceio_before and H.tree(dependency)==sourceio_before,'SourceIO source/copy changed')
    need(all(H.tree(Path(path))==rows for path,rows in protected.items()),'Previous owner review changed')
    need(all(H.tree(Path(path))==rows for path,rows in families.items()),'Original native family changed')
    need(all(H.identity(Path(path))==row for path,row in lock['runtime_executables'].items()),'Shared runtime changed')
    need(H.exporter_sources(exporter)==lock['exporter_noncache_sources'],'Installed exporter source changed')
    need(H.identity(native_path)==lock['native_verification'],'Original native DATA proof changed')
    need(all(H.identity(Path(row['source']))==row['identity'] for row in lock['projects']),'Original packed DATA example changed')
    combined={**functional_hashes,**extra_hashes}
    need(all(H.identity(studio/name)['sha256']==expected for name,expected in combined.items()),'Final Studio source/support bytes differ')
    need(all(H.identity(studio/name)==expected for name,expected in identities.items()),'Final tested-raw source stamps differ')
    _gate_files(H,full_gate,'Qualified full/root release')
    _gate_files(H,preparation,'Reviewed executor preparation')
    Q.assert_admitted(admitted)
    report={'format':'has_neon_qualified_merge_owner_review_copy_1','passed':True,'final':str(final),
            'source_commit':merged,'candidate_commit':candidate,'builder_preparation':preparation,'profile':profile,
            'source_mode':'candidate_tested_raw_bytes_with_reviewed_Git_EOL_bridge','functional_source_hashes':functional_hashes,
            'support_source_mode':'exact_committed_nonfunctional_Git_blobs','support_source_hashes':extra_hashes,
            'support_catalogue_identity':d['support_catalogue_identity'],'source_hashes':combined,
            'checkout_EOL_admission':d['eol_recipe'],'source_delta_admission':d['source_delta_admission'],
            'projects':projects,'native_sources_included':True,'native_source_files':495,'native_source_bytes':451266730,
            'SourceIO_local_copy_exact':True,'sourceio_revision':PIN,'sourceio_files':len(sourceio_before),
            'full_run_gate':full_gate,'installed_exporter_sources_preserved':len(lock['exporter_noncache_sources']),
            'previous_reviews_preserved':list(protected),'original_native_families_preserved':True,
            'shared_runtimes_preserved':True,'installed_Studio_not_written':True,'write_boundaries':[str(final)],
            'graphics_launched':False,'startup_or_final_replay':'UNRUN_root_private_187_validation_required',
            'native_Source_solver':{'implementation':'bounded_five_rule_0x31','solved_rules':5,'retained_rules':49,
                'strands':3,'copy_only_builder_no_runtime_launch':True,'SDK_artist_or_full49_parity':False},
            'owner_participation_requested':False,'owner_manual_or_portable_acceptance_claimed':False}
    H.write_new(final/'BUILD-VERIFICATION.json',report)
    return report

def main():
    import qualified_inputs as Q
    admitted=Q.require_qualified_inputs()
    report=build(admitted)
    print(json.dumps({'final':report['final'],'source_commit':report['source_commit'],'passed':True,'graphics_launched':False}))
if __name__=='__main__':main()
