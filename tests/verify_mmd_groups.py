"""Native PMX grouped expression import, shared authoring and portable HAS/movie."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from run import command
from mmd_expression_fixture import create
def main():
    folder=ROOT/'output/mmd-groups'/str(time.time_ns());folder.mkdir(parents=True)
    unit=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_mmd_expression_groups.py'],cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace');(folder/'python.log').write_text(unit.stdout+unit.stderr,encoding='utf-8');assert unit.returncode==0 and 'Ran 12 tests'in unit.stderr
    source=folder/'Original groups.pmx';create(source);original=(hashlib.sha256(source.read_bytes()).hexdigest(),source.stat().st_mtime_ns);results=[];receipts=[]
    for name,extra in [('app',[]),('reader',['reader'])]:
        args=command('tests/mmd_groups_smoke.gd',extra=['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=185)
        log=p.stdout+p.stderr;(folder/(name+'.log')).write_text(log,encoding='utf-8');(folder/(name+'-command.json')).write_text(json.dumps({'args':args,'exit':p.returncode}))
        assert p.returncode==0 and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log[-7000:]
        tag='MMD_GROUPS_'+name.upper()+' ';r=json.loads(next(line.split(tag,1)[1]for line in log.splitlines()if line.startswith(tag)));assert r['failures']==0;results.append(r)
        receipt=Path(args[args.index('--receipt')+1]);record=json.loads(receipt.read_text());assert record['exit']==0 and record['child_desktop_confirmed']and not record['foreground_child_observed']and record['job_closed']and record['desktop_closed'];receipts.append(str(receipt))
    parameters=json.loads((Path(results[0]['bundle'])/'parameters.json').read_text(encoding='utf-8'));assert parameters['mmd_expression_source_counts']=={'groups':4,'bindings':8}
    glb=(Path(results[0]['bundle'])/'scene.glb').read_bytes();json_size=int.from_bytes(glb[12:16],'little');assert hashlib.sha256(glb[20+json_size:]).hexdigest()==parameters['expression_geometry_tail_sha256']
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',results[0]['movie']],encoding='utf-8'));v=next(v for v in probe['streams']if v['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48')and abs(float(probe['format']['duration'])-2)<.001
    assert (hashlib.sha256(source.read_bytes()).hexdigest(),source.stat().st_mtime_ns)==original
    result={'checks':12+sum(r['checks']for r in results),'failures':0,'folder':str(folder),'results':results,'private_receipts':receipts,'fixture':'original authored PMX, not a supplied native group corpus'}
    (ROOT/'output/mmd-groups-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
