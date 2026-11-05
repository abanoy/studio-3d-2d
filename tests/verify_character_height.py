"""Optional neutral character-size review, source integrity and standard placement."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from run import command
def main():
    folder=ROOT/'output/character-height'/str(time.time_ns());folder.mkdir(parents=True)
    plans=[{'label':'Authored figure','source':str(ROOT/'examples/tutorials/Practice figure.glb'),'metadata':{},'rotation':[0,0,0,1]}]
    native=[];by_sha={};catalogue_path=ROOT/'output/shape-catalog-verification.json';audit_path=ROOT/'output/import-height-audit.json'
    if catalogue_path.is_file():
        prior=json.loads(catalogue_path.read_text(encoding='utf-8'));native=json.loads((Path(prior['folder'])/'catalogue-plans.json').read_text(encoding='utf-8'))[1:]
    audit_rows=[]
    if audit_path.is_file():
        audit=json.loads(audit_path.read_text(encoding='utf-8'));audit_rows=json.loads((Path(audit['folder'])/'plans.json').read_text(encoding='utf-8'))
    for row in audit_rows:
        path=Path(row['source'])
        if path.is_file():by_sha[hashlib.sha256(path.read_bytes()).hexdigest()]=row
    originals={}
    raw_plan={};native_manifest=ROOT/'output/native-import-verification.json'
    if native_manifest.is_file():
        for name in json.loads(native_manifest.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(name);report_path=bundle/'parameters.json'
            if not report_path.is_file():continue
            report=json.loads(report_path.read_text(encoding='utf-8'));candidate=bundle/'native'/report.get('source_file','')
            if report.get('kind')=='vrm_preparation' and candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest()==report['source_sha256']:
                raw_plan={'source':str(candidate)};originals[candidate]=(report['source_sha256'],candidate.stat().st_mtime_ns);break
    (folder/'raw-vrm.json').write_text(json.dumps(raw_plan),encoding='utf-8')
    for row in native:
        path=Path(row['source'])
        if not path.is_file():continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest();old=by_sha.get(digest,{})
        plans.append({'label':row['label'],'source':str(path),'metadata':old.get('metadata',{}),'rotation':old.get('rotation_xyzw',[0,0,0,1])})
    for row in plans:
        path=Path(row['source']);originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'plans.json').write_text(json.dumps(plans),encoding='utf-8')
    args=command('tests/character_height_smoke.gd',extra=['--',str(folder)]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=230)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8');(folder/'command.json').write_text(json.dumps({'args':args,'exit':p.returncode}))
    assert p.returncode==0 and 'CHARACTER_HEIGHT_APP 'in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log[-6500:]
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert result['failures']==0
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed']
    reader_args=command('tests/character_height_smoke.gd',extra=['--',str(folder),'reader']);p=subprocess.run(reader_args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=65)
    log=p.stdout+p.stderr;(folder/'reader.log').write_text(log,encoding='utf-8');(folder/'reader-command.json').write_text(json.dumps({'args':reader_args,'exit':p.returncode}))
    assert p.returncode==0 and 'CHARACTER_HEIGHT_READER 'in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log[-4000:]
    reader=json.loads(next(line.split('CHARACTER_HEIGHT_READER ',1)[1]for line in log.splitlines()if line.startswith('CHARACTER_HEIGHT_READER ')));assert reader['failures']==0
    cold_receipt=Path(reader_args[reader_args.index('--receipt')+1]);r=json.loads(cold_receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed']
    receipts=[str(receipt),str(cold_receipt)];native_result=None
    if raw_plan:
        native_args=command('tests/height_import_native_smoke.gd',extra=['--',str(folder)]);p=subprocess.run(native_args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=100)
        log=p.stdout+p.stderr;(folder/'native.log').write_text(log,encoding='utf-8');(folder/'native-command.json').write_text(json.dumps({'args':native_args,'exit':p.returncode}))
        assert p.returncode==0 and 'HEIGHT_IMPORT_NATIVE 'in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log[-5000:]
        native_result=json.loads(next(line.split('HEIGHT_IMPORT_NATIVE ',1)[1]for line in log.splitlines()if line.startswith('HEIGHT_IMPORT_NATIVE ')));assert native_result['failures']==0
        native_receipt=Path(native_args[native_args.index('--receipt')+1]);r=json.loads(native_receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed'];receipts.append(str(native_receipt))
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',result['movie']],encoding='utf-8'));v=next(v for v in probe['streams']if v['codec_type']=='video')
    assert(v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48')and abs(float(probe['format']['duration'])-2)<.001
    for path,value in originals.items():assert(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==value,path
    result.update(folder=str(folder),private_receipts=receipts,reader=reader,native_import=native_result,native_models=len(plans)-1);(ROOT/'output/character-height-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
