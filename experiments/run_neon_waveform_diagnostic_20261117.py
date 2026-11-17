from pathlib import Path
import hashlib,importlib.util,json,shutil
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
FOLDER=REVIEW/'output/neon-waveform-diagnostic-20261117-attempt1'
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def main():
    source=ROOT/'experiments/neon_waveform_diagnostic_20261117/waveform_levels_smoke.diagnostic.gd'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='39b92686a7a50407cb1ab7739e72875a2d1f694644fe5884689e8ece730b935d'
    FOLDER.mkdir(exist_ok=False)
    safety=module(ROOT/'experiments/run_neon_behavior_original_20261116.py','wave_diagnostic_safety');safety.FOLDER=FOLDER
    safety.closed('before');before=safety.sources()
    relative='experiments/neon_waveform_runtime_20261117/diagnostic.gd';target=REVIEW/relative
    target.parent.mkdir(exist_ok=True,parents=True);assert not target.exists();target.write_bytes(source.read_bytes())
    shutil.copy2(REVIEW/'output/neon-auxiliary-original-20261117-attempt1/waveform-case/impulses.wav',FOLDER/'impulses.wav')
    (FOLDER/'prefs.cfg').write_text('[display]\ntheme="neon"\n',encoding='utf-8')
    runner=module(REVIEW/'run.py','wave_diagnostic_runner')
    observer=module(ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py','wave_diagnostic_observer')
    try:
        command=runner.command(relative,extra=['--log-file',str(FOLDER/'engine.log'),'--',FOLDER.as_posix()])
        process,log=observer.invoke(FOLDER,'app',command,150)
        receipt=json.loads(Path(command[command.index('--receipt')+1]).read_bytes())
        diagnostics=[json.loads(line.split(' ',1)[1]) for line in log.splitlines() if line.startswith('WAVEFORM_SAMPLE_DIAGNOSTIC ') or line.startswith('WAVEFORM_CONTEXT_DIAGNOSTIC ')]
        markers=[line[len('WAVEFORM_LEVELS_SMOKE '):] for line in log.splitlines() if line.startswith('WAVEFORM_LEVELS_SMOKE ')]
        result=json.loads(markers[0]) if len(markers)==1 else None
    finally:
        safety.closed('after');preserved=safety.sources()==before
    record={'format':'has_neon_waveform_diagnostic_execution_1','process':process,'receipt':receipt,'result':result,'diagnostics':diagnostics,'source_preserved':preserved,'original14_predicates_unchanged':True}
    safety.save(FOLDER/'verification.json',record)
    print(json.dumps({'folder':str(FOLDER),'exit':process['exit'],'result':result,'diagnostic_records':len(diagnostics),'source_preserved':preserved}))
if __name__=='__main__':main()
