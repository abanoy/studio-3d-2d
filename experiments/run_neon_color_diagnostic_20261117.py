"""ROOT: run an instrumented copy, preserving the original color test and sources."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
support=ROOT/'experiments/run_neon_scene_followup_20261117.py'
assert sha(support)=='07e37aa4ddba05e31658f2fe14bda53a25ce0f7646f2c966961a635ef6b85255'
H=module('root_color_diagnostic_scope',support)
def input_map():
 result={}
 for name in ('pose-smoke/miku-project','source-smoke/source-project','sfm-smoke/project'):
  base=REVIEW/'output'/name;assert (base/'project.json').is_file()
  for p in sorted(base.rglob('*')):
   assert not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400
   if p.is_file():result[p.relative_to(REVIEW).as_posix()]=sha(p)
 return result
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--producer-index-sha256',required=True);parser.add_argument('--label',required=True);args=parser.parse_args()
 assert args.label.startswith('neon-color-diagnostic-696-') and all(c.isalnum() or c=='-' for c in args.label)
 packet=ROOT/'experiments/neon_color_sampler_conjunction_diagnostic_20261117'
 assert sha(packet/'INDEX.json')==args.producer_index_sha256
 index=json.loads((packet/'INDEX.json').read_bytes())
 for row in index.get('files',index.get('payloads',[])):
  p=packet/row['path'];assert p.resolve().is_relative_to(packet.resolve()) and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
 producer=module('root_color_diagnostic_producer',packet/'producer.py')
 original=REVIEW/'tests/color_sampler_smoke.gd';raw=original.read_bytes()
 assert sha(original)=='7c2150ad2a5221bf3e81cad758cea609f46d414e8e2761c9b50cfb82598bf141'
 frozen=json.loads((REVIEW/'output/windows-neon-696ca7f-20261117T170720480423/source-before.json').read_bytes())
 assert H.sources()==frozen['source_sha256'] and len(H.sources())==1029
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REVIEW).strip()==b'696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
 tools={H.PYTHON:'03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9',H.PWSH:'2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233',H.ENGINE:'63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf',Path(r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'):'8d334ffec552898aed0f095f507cd994c4f2825d4b88c352e7a37cd26b7f5b70',Path(r'C:\Program Files\ffmpeg\bin\ffprobe.exe'):'6080217dc842c5850c1ab58988074ef11012423d594c0c942f075563a483fd19'}
 assert all(sha(p)==pin for p,pin in tools.items())
 folder=REVIEW/'output'/args.label;folder.mkdir(exist_ok=False)
 H.save(folder/'source-before.json',H.sources());before=input_map();H.save(folder/'native-inputs-before.json',before)
 H.closed(folder,'before')
 script=folder/'instrumented.gd';script.write_bytes(producer.instrument(raw));assert original.read_bytes()==raw
 sys.path.insert(0,str(REVIEW));import run as Runner
 assert Path(Runner.__file__).resolve()==REVIEW/'run.py'
 os.environ['HYBRID_GODOT']=str(H.ENGINE);os.environ['HYBRID_PYTHON']=str(H.PYTHON)
 os.environ['HYBRID_FFMPEG']=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
 resultfolder=folder/'case';resultfolder.mkdir()
 command=Runner.command(script.relative_to(REVIEW).as_posix(),extra=['--',str(resultfolder),'--demo-room'])
 H.save(folder/'command.json',command);start=time.time_ns()
 p=subprocess.Popen(command,cwd=REVIEW,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
 H.save(folder/'process-start.json',{'pid':p.pid,'retained_Popen':True,'started_ns':start})
 out,err=p.communicate(timeout=190)
 (folder/'stdout.log').write_bytes(out);(folder/'stderr.log').write_bytes(err)
 H.save(folder/'process-result.json',{'pid':p.pid,'exit':p.returncode,'reaped':p.poll() is not None,'seconds':(time.time_ns()-start)/1e9,'timed_out':False})
 receipt=Path(command[command.index('--receipt')+1]);value=json.loads(receipt.read_bytes())
 assert value['exit']==p.returncode and value['child_desktop_confirmed'] is True and value['foreground_child_observed'] is False and value['job_closed'] is True and value['desktop_closed'] is True
 H.save(folder/'private-receipt.json',value)
 after=H.sources();native_after=input_map();H.save(folder/'source-after.json',after);H.save(folder/'native-inputs-after.json',native_after)
 scope=H.closed(folder,'after')
 assert after==frozen['source_sha256'] and native_after==before and original.read_bytes()==raw
 assert all(sha(path)==pin for path,pin in tools.items())
 marker=b'COLOR_SAMPLER_NATIVE_PROBE '
 rows=[json.loads(line.split(marker,1)[1]) for line in out.splitlines() if marker in line]
 H.save(folder/'PRIVATE-native-diagnostics.json',rows)
 summary={'format':'has_original_color_sampler_instrumented_diagnostic_1','child_exit':p.returncode,'reaped':p.poll() is not None,'diagnostic_cases':len(rows),'functional_sources_unchanged':1029,'native_input_files_unchanged':len(before),'private_job_and_desktop_closed':True,'host_scope_closed':scope['owned_count']==0,'original_test_and_all_assertions_preserved':True,'full_PASS_merge_or_fix_claimed':False}
 H.save(folder/'DIAGNOSTIC-RECORD.json',summary);print(json.dumps(summary));return p.returncode
if __name__=='__main__':raise SystemExit(main())
