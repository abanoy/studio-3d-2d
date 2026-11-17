"""ROOT-ONLY future staging: interpret actual full/closure; never launch apps."""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
sys.dont_write_bytecode=True
from probe_support import ROOT,LOCK_SHA,REQUIRED_FILES,read_context,safe_path,sha,require

HERE=Path(__file__).resolve().parent
INPUTS=ROOT/'experiments/source_normal_followup_plan_20261115/INPUT_METADATA.json'
INPUTS_SHA='080cfbcea375c18fa21f29b51d9afbd30bfc4862524974b8900cfd67541d4914'
LOCK=ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json'


def write(path,value):
    with path.open('x',encoding='utf-8') as handle:json.dump(value,handle,indent=2,allow_nan=False);handle.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full-run',type=Path,required=True)
    parser.add_argument('--expected-full-commit',required=True)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--expected-functional-count',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expires-minutes',type=int,default=30)
    args=parser.parse_args()
    require(all(re.fullmatch('[a-f0-9]{40}',value) for value in (args.expected_full_commit,args.expected_head)),'Explicit full40-character commits required')
    require(5<=args.expires_minutes<=60,'Bounded5–60minute root lease expiry required')
    # This must complete BEFORE any stage directory/copy/lease is created.
    context=read_context(args.full_run,args.expected_full_commit,args.expected_functional_count)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head==args.expected_head,'Current HEAD differs')
    require(sha(LOCK.read_bytes())==LOCK_SHA,'Approved shared-input lock changed')
    lock=json.loads(LOCK.read_bytes())
    require(any(Path(name).resolve()==Path(sys.executable).resolve() for name in lock['runtime_executables']),'Use the approved Python runtime to stage')
    reader_path=ROOT/'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
    require(sha(reader_path.read_bytes())=='5be1d34aa6aced8fc112bee3ecadd489be9b7f38ab710553385bfd77ca500d83','Reviewed identity reader changed')
    spec=importlib.util.spec_from_file_location('normal_probe_identity_reader',reader_path);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    require(len(lock['runtime_executables'])==6 and all(reader.identity(Path(name))==value for name,value in lock['runtime_executables'].items()),'Approved runtime identities changed')
    require(len(lock['sourceio_files'])==574 and reader.metadata_map(reader.SOURCEIO)==lock['sourceio_files'],'Approved574SourceIO catalogue changed')
    require(len(lock['exporter_noncache_sources'])==120 and reader.metadata_map(Path(lock['exporter_root']),'exporter')==lock['exporter_noncache_sources'],'Approved120exporter catalogue changed')
    require(sha(INPUTS.read_bytes())==INPUTS_SHA,'Retained input metadata changed')
    original=json.loads(INPUTS.read_bytes())['files']
    files={}
    for name,row in original.items():
        path=safe_path(row['path'] if Path(row['path']).is_absolute() else ROOT/row['path'])
        require(sha(path.read_bytes())==row['sha256'],'Retained original changed: '+name)
        files[name]={'path':str(path),'sha256':row['sha256']}
    target=safe_path(args.output)
    require(target.is_relative_to(ROOT/'output') and target.parent.is_dir() and not target.exists(),'Fresh owned stage path with existing parent required')
    require(sys.platform=='win32','Actual Windows staging required')
    target.mkdir(exist_ok=False);inputs=target/'inputs';inputs.mkdir()
    original_blend=files['blend'].copy();copy=inputs/'editable.blend'
    with Path(original_blend['path']).open('rb') as src,copy.open('xb') as dst:shutil.copyfileobj(src,dst)
    require(sha(copy.read_bytes())==original_blend['sha256'],'Owned blend copy differs')
    files['blend']={'path':str(copy),'sha256':original_blend['sha256']}
    files.update(probe={'path':str(HERE/'capture_blender_normals.py'),'sha256':sha((HERE/'capture_blender_normals.py').read_bytes())},full_receipt=context['files']['state'],closure_receipt=context['files']['release'])
    require(set(files)==REQUIRED_FILES,'Exact12 locks not assembled')
    analysis={key:{'path':str(path),'sha256':sha(path.read_bytes())} for key,path in {'support':HERE/'probe_support.py','metrics':HERE/'normal_metrics.py','comparator':HERE/'compare_private_normals.py','matcher':ROOT/'experiments/source_appearance/native_coordinates_20261114/prove_coordinates_stdlib.py'}.items()}
    now=datetime.datetime.now(datetime.timezone.utc)
    lease={'format':'has_blender_normal_probe_lease_1','phase':'ROOT_APPROVED_AFTER_FULL_PASS','HEAD':head,'full_terminal_status':'PASS','root_authoritative_closure':True,'publish_private_arrays':False,'created_utc':now.isoformat(),'expires_utc':(now+datetime.timedelta(minutes=args.expires_minutes)).isoformat(),'files':files,'analysis_files':analysis,'original_blend':original_blend,'full_context':context,'private_output_directory':str(target/'capture'),'staging_runtime_executed':False,'approved_shared_input_lock_sha256':LOCK_SHA}
    lease_path=target/'lease.json';write(lease_path,lease)
    blender=[files['blender_exe']['path'],'--background','--factory-startup','--offline-mode','--disable-autoexec',str(copy),'--python-exit-code','1','--python',files['probe']['path'],'--','--lease',str(lease_path)]
    pythonw=Path(sys.executable).with_name('pythonw.exe');require(pythonw.is_file(),'Approved pythonw unavailable')
    wrapper=[str(pythonw),str(ROOT/'tools/private_desktop.py'),'--receipt',str(target/'private-receipt.json'),'--timeout','120','--memory-limit-mib','4096','--',*blender]
    compare=[sys.executable,'-B',str(HERE/'compare_private_normals.py'),'--lease',str(lease_path),'--private',str(target/'capture/PRIVATE_NORMALS.json'),'--output',str(target/'BLENDER_BOUNDARY_COMPARISON.json')]
    write(target/'ROOT_COMMANDS.json',{'format':'has_root_normal_probe_commands_1','not_executed':True,'capture_command':wrapper,'capture_cwd':str(ROOT),'stdout_private':str(target/'capture-stdout.log'),'stderr_private':str(target/'capture-stderr.log'),'outer_timeout_seconds':130,'capture_expected_marker':'HAS_NORMAL_CAPTURE ','capture_expected_public_status':'CAPTURE_COMPLETE_COMPARISON_UNRUN','required_capture_exit':0,'private_receipt_required':{'exit':0,'child_desktop_confirmed':True,'foreground_child_observed':False,'job_closed':True,'desktop_closed':True},'private_window_seen':'BackgroundBlendermayhave_no_window;thread desktop confirmation is required.','comparison_command':compare,'root_must_retain_Popen_identity_reap_and_authoritatively_close':True,'no_runtime_invoked_by_staging':True})
    write(target/'STAGED.json',{'format':'has_root_normal_probe_staging_1','lease_sha256':sha(lease_path.read_bytes()),'exact_primary_file_locks':12,'supplemental_analysis_sources':4,'full_source_commit':args.expected_full_commit,'current_head':head,'functional_count':args.expected_functional_count,'shared_catalogue_counts':[6,574,120],'owned_blend_copy_sha256':sha(copy.read_bytes()),'original_blend_sha256':original_blend['sha256'],'native_or_Blender_runtime_executed':False,'helper_sha256':sha(Path(__file__).read_bytes())})
    print(json.dumps({'staged':str(target),'lease_sha256':sha(lease_path.read_bytes()),'native_runtime_executed':False}))


if __name__=='__main__':main()
