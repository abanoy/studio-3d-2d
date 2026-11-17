from pathlib import Path
import importlib.util,json,shutil
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
FOLDER=REVIEW/'output/neon-waveform-classic-reveal-20261117-attempt1'
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def main():
    FOLDER.mkdir(exist_ok=False)
    safety=module(ROOT/'experiments/run_neon_behavior_original_20261116.py','wave_classic_safety');safety.FOLDER=FOLDER
    safety.closed('before');before=safety.sources()
    source=REVIEW/'output/neon-auxiliary-original-20261117-attempt1/waveform-case/impulses.wav'
    shutil.copy2(source,FOLDER/'impulses.wav')
    (FOLDER/'prefs.cfg').write_text('[display]\ntheme="light"\n',encoding='utf-8')
    runner=module(REVIEW/'run.py','wave_classic_runner')
    observer=module(ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py','wave_classic_observer')
    try:
        command=runner.command('tests/waveform_levels_smoke.gd',extra=['--log-file',str(FOLDER/'engine.log'),'--',FOLDER.as_posix()])
        process,log=observer.invoke(FOLDER,'app',command,150)
        receipt=json.loads(Path(command[command.index('--receipt')+1]).read_bytes())
        lines=[line[len('WAVEFORM_LEVELS_SMOKE '):] for line in log.splitlines() if line.startswith('WAVEFORM_LEVELS_SMOKE ')]
        result=json.loads(lines[0]) if len(lines)==1 else None
    finally:
        safety.closed('after');preserved=safety.sources()==before
    record={'format':'has_classic_waveform_reveal_counterfactual_1','process':process,'receipt':receipt,'result':result,'source_preserved':preserved}
    safety.save(FOLDER/'verification.json',record);print(json.dumps(record))
if __name__=='__main__':main()
