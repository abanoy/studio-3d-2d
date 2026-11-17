"""Future root-only staging; no Blender/native/CIM process is launched here."""
from pathlib import Path
import argparse,datetime,json,re,subprocess,sys
sys.dont_write_bytecode=True
from setter_support import ROOT,HERE,ROLES,LOCK,READER,OLD_SUPPORT,normal_support,approved,validate_prior,safe,sha,require
B=ROOT/'output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685'
PRIOR=ROOT/'output/normal-boundary-20261116-attempt2'
SIO=ROOT/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
def write(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--expected-head',required=True);p.add_argument('--expected-full-commit',required=True);p.add_argument('--full-run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--expires-minutes',type=int,default=30);a=p.parse_args()
    require(all(re.fullmatch('[a-f0-9]{40}',s) for s in (a.expected_head,a.expected_full_commit)) and 5<=a.expires_minutes<=60,'Bounded exact root context required')
    context=normal_support().read_context(a.full_run,a.expected_full_commit,1019)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head==a.expected_head,'Actual current HEAD differs')
    lock=approved();require(any(Path(n).resolve()==Path(sys.executable).resolve() for n in lock['runtime_executables']),'Approved Python required')
    paths={'mdl':B/'native/junko hair.mdl','vvd':B/'native/junko hair.vvd','vtx':B/'native/junko hair.dx90.vtx','saved_capture':PRIOR/'capture/PRIVATE_NORMALS.json','prior_public':PRIOR/'capture/PUBLIC_CAPTURE.json','prior_comparison':PRIOR/'BLENDER_BOUNDARY_COMPARISON.json','prior_execution':PRIOR/'root-execution/verification.json','prior_closure':PRIOR/'root-execution/after-closure.json',
        'blender_exe':Path(r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'),'probe':HERE/'setter_probe.py','support':HERE/'setter_support.py','instrumentation':HERE/'instrumentation.py','vvd_parser':HERE/'vvd_normals.py','approved_lock':LOCK,'identity_reader':READER,'normal_support':OLD_SUPPORT,'bridge':ROOT/'tools/blender_source_bridge.py',
        'importer':SIO/'blender_bindings/models/mdl49/import_mdl.py','sourceio_common':SIO/'blender_bindings/models/common.py','sourceio_fastmesh':SIO/'blender_bindings/utils/fast_mesh.py','sourceio_vvd':SIO/'library/models/vvd/__init__.py','sourceio_vtx':SIO/'library/models/vtx/v7/vtx.py','sourceio_vtx_init':SIO/'library/models/vtx/__init__.py','sourceio_mdl':SIO/'library/models/mdl/v49/mdl_file.py','full_state':Path(context['files']['state']['path']),'graphics_release':Path(context['files']['release']['path'])}
    require(set(paths)==ROLES,'Setter role set differs')
    expected={'mdl':'8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716','vvd':'2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0','vtx':'924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a','saved_capture':'0ef144f3ffe093d6c01f31e5e6fadf98e87a5c7de2b4013c27d42809dabd6921','importer':'173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b','blender_exe':'1e6624af112b3c936f4b038b025ebd2bf00ae72c4b62881a6787166d71c58fa5'}
    for name,pin in expected.items():require(sha(safe(paths[name]).read_bytes())==pin,'Known input differs: '+name)
    prior=validate_prior(paths);files={n:{'path':str(safe(p)),'sha256':sha(p.read_bytes())} for n,p in paths.items()}
    target=safe(a.output);require(target.is_relative_to(ROOT/'output') and target.parent.is_dir() and not target.exists(),'Fresh owned output required')
    # First output mutation occurs after all actual full/source/prior/catalogue validation.
    target.mkdir();now=datetime.datetime.now(datetime.timezone.utc)
    lease={'format':'has_sourceio_setter_boundary_lease_1','phase':'ROOT_APPROVED_AFTER_CLOSED_NORMAL_PROBE','private_arrays_public':False,'expected_head':head,'full_context':context,'prior_context':prior,'sourceio_root':str(SIO),'files':files,'created_utc':now.isoformat(),'expires_utc':(now+datetime.timedelta(minutes=a.expires_minutes)).isoformat(),'private_output':str(target/'capture'),'fresh_root_process_inventory_and_exclusive_lease_required_separately':True}
    path=target/'lease.json';write(path,lease)
    blender=[str(paths['blender_exe']),'--background','--factory-startup','--offline-mode','--disable-autoexec','--python-exit-code','1','--python',str(paths['probe']),'--','--lease',str(path)]
    wrapper=[str(Path(sys.executable).with_name('pythonw.exe')),str(ROOT/'tools/private_desktop.py'),'--receipt',str(target/'private-receipt.json'),'--timeout','150','--memory-limit-mib','4096','--',*blender]
    write(target/'ROOT_COMMANDS.json',{'format':'has_setter_probe_future_root_commands_1','not_executed':True,'capture_command':wrapper,'capture_cwd':str(ROOT),'outer_timeout_seconds':165,'expected_exit':0,'expected_marker':'HAS_SETTER_PROBE ','expected_public_status':'SETTER_BOUNDARIES_MEASURED','private_result':str(target/'capture/PRIVATE_SETTER.json'),'public_result':str(target/'capture/PUBLIC_SETTER.json'),'receipt_requirements':{'exit':0,'child_desktop_confirmed':True,'foreground_child_observed':False,'job_closed':True,'desktop_closed':True},'root_must_retain_Popen_reap_and_authoritatively_close':True})
    write(target/'STAGED.json',{'format':'has_setter_probe_stage_1','lease_sha256':sha(path.read_bytes()),'roles':len(files),'current_head':head,'full_source_commit':a.expected_full_commit,'functional_source_files':1019,'prior_context':prior,'native_engine_launched':False})
    print(json.dumps({'staged':str(target),'lease_sha256':sha(path.read_bytes()),'native_engine_launched':False}))
if __name__=='__main__':main()
