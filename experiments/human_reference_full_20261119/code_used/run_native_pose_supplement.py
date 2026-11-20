from pathlib import Path
import hashlib,importlib.util,json,os,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from tools.build_owner_review_snapshot import freeze_source
REV='08ad583de735393c5baa75ca9960482243dccff1'
folder=ROOT/'output'/('native-pmd-pose-supplement-'+str(time.time_ns()));folder.mkdir()
studio=folder/'Studio';revision,hashes=freeze_source(ROOT,studio,REV,runtime_scope=True)
assert revision==REV
profile='HAS Native PMD Pose Supplement '+str(time.time_ns())
(studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n',encoding='utf-8')
def identity(path):
    s=path.stat();return {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
source_root=ROOT.parent/'has-acceptance-session-20261111'/'output/compatibility/miku-tested'
expected={'scene.glb':'b0a78fd482908e72099ad970649849bc0cd392e6e50585efade1175f45dece9a','parameters.json':'cfe628f5a8c5134df94448b72597146975707dbec938ada7efe3d04305514fc8'}
originals={};staged={}
for name,digest in expected.items():
    original=source_root/name;stamp=identity(original);assert stamp['sha256']==digest
    for part in (original,*original.parents):assert not part.is_symlink() and not (getattr(part.lstat(),'st_file_attributes',0)&0x400)
    target=studio/'output/compatibility/miku-tested'/name;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();shutil.copy2(original,target)
    assert identity(original)==identity(target)==stamp
    originals[str(original)]=stamp;staged[str(target)]=stamp
(folder/'preparation.json').write_text(json.dumps({'source_commit':revision,'profile':profile,'source_hashes':hashes,'originals':originals,'staged':staged},indent=2)+'\n')
spec=importlib.util.spec_from_file_location('pmd_supplement_run',studio/'run.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
environment=os.environ.copy();environment.update(HYBRID_GODOT=r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe',HYBRID_PYTHON=sys.executable,PYTHONDONTWRITEBYTECODE='1',HYBRID_FFMPEG=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe')
os.environ['HYBRID_GODOT']=environment['HYBRID_GODOT']
args=module.command(extra=['--audio-driver','Dummy','--','--pose-smoke'])
(folder/'command.json').write_text(json.dumps(args,indent=2)+'\n')
print(json.dumps({'folder':str(folder)}),flush=True)
p=subprocess.run(args,cwd=studio,env=environment,capture_output=True,timeout=230,creationflags=subprocess.CREATE_NO_WINDOW)
log=p.stdout+p.stderr;(folder/'console.log').write_bytes(log)
assert p.returncode==0 and b'POSE_SMOKE ' in log and not any(word in log for word in (b'ERROR:',b'FAIL ',b'ObjectDB instances leaked',b'resources still in use')),log[-6000:]
result=json.loads((studio/'output/pose-smoke/result.json').read_bytes())
assert result['actual_mmd_tested'] is True and result['checks']==45 and result['failures']==0 and len(result['movies'])==2,result
receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
assert r['exit']==0 and r['child_desktop_confirmed'] and r['private_window_seen'] and r['job_closed'] and r['desktop_closed'] and not r['foreground_child_observed'] and not r['desktop_switch_requested']
videos=[]
for movie in result['movies']:
    metadata=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',movie],creationflags=subprocess.CREATE_NO_WINDOW))
    video=next(s for s in metadata['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(metadata['format']['duration'])-2)<.01
    videos.append({'codec':'h264','width':1920,'height':1080,'fps':'24/1','frames':48,'duration':metadata['format']['duration']})
assert all(identity(Path(path))==stamp for path,stamp in {**originals,**staged}.items())
assert all(hashlib.sha256((studio/name).read_bytes()).hexdigest()==digest for name,digest in hashes.items())
final={'format':'has_native_pmd_pose_supplement_1','status':'PASS','source_commit':REV,'checks':45,'failures':0,'actual_mmd_tested':True,'movies':videos,'private_receipt':str(receipt),'private_receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'originals_and_staged_preserved':True,'runtime_files_unchanged':len(hashes),'full_run_results_relabelled':False,'private_art_uploaded':False}
(folder/'verification.json').write_text(json.dumps(final,indent=2)+'\n')
print(json.dumps(final,indent=2))
