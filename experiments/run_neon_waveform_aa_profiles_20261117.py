from pathlib import Path
import hashlib,importlib.util,json,shutil
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
FOLDER=REVIEW/'output/neon-waveform-aa-profiles-20261117-attempt1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def main():
    source=ROOT/'experiments/neon_waveform_aa_successor_20261117/waveform_levels_smoke.proposed.gd'
    assert sha(source)=='847279d94ad0b42b3efc733b34ca4ff9538b0501e5d6268597c1039b9b739fab'
    target=REVIEW/'tests/waveform_levels_smoke.gd';assert sha(target)=='9775d5a497b64025fc93d958aa1a900316288b5fb2fb7fb34f77f3340ec3aa66'
    FOLDER.mkdir(exist_ok=False)
    safety=module(ROOT/'experiments/run_neon_behavior_original_20261116.py','wave_palette_safety');safety.FOLDER=FOLDER
    safety.closed('before');(FOLDER/'input-only-source.gd').write_bytes(target.read_bytes());target.write_bytes(source.read_bytes())
    before=safety.sources()
    runner=module(REVIEW/'run.py','wave_palette_runner')
    observer=module(ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py','wave_palette_observer')
    wav=REVIEW/'output/neon-auxiliary-original-20261117-attempt1/waveform-case/impulses.wav'
    rows=[]
    try:
        for label,theme in [('neon','neon'),('classic','light')]:
            folder=FOLDER/label;folder.mkdir(exist_ok=False);shutil.copy2(wav,folder/'impulses.wav')
            (folder/'prefs.cfg').write_text('[display]\ntheme="'+theme+'"\n',encoding='utf-8')
            command=runner.command('tests/waveform_levels_smoke.gd',extra=['--log-file',str(folder/'engine.log'),'--',folder.as_posix()])
            process,log=observer.invoke(FOLDER,label,command,150)
            receipt=json.loads(Path(command[command.index('--receipt')+1]).read_bytes())
            lines=[line[len('WAVEFORM_LEVELS_SMOKE '):] for line in log.splitlines() if line.startswith('WAVEFORM_LEVELS_SMOKE ')]
            result=json.loads(lines[0]) if len(lines)==1 else None
            rows.append({'label':label,'process':process,'receipt':receipt,'result':result,'errors':[l for l in log.splitlines() if any(t in l for t in ('ERROR:','SCRIPT ERROR','ObjectDB instances leaked'))]})
            safety.closed(label+'-after')
    finally:
        safety.closed('after');preserved=safety.sources()==before
        safety.save(FOLDER/'verification.json',{'format':'has_waveform_aa_profile_execution_1','rows':rows,'source_preserved':preserved,'product_palette_changed':False})
    print(json.dumps({'folder':str(FOLDER),'source_preserved':preserved,'rows':[{'label':r['label'],'exit':r['process']['exit'],'result':r['result'],'errors':r['errors']} for r in rows]}))
if __name__=='__main__':main()
