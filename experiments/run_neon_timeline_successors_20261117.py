"""Root: retain originals, apply input/API fixtures and execute focused profiles."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
FOLDER=REVIEW/'output/neon-timeline-successors-20261117-attempt1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def main():
    FOLDER.mkdir(exist_ok=False)
    safety=module(ROOT/'experiments/run_neon_behavior_original_20261116.py','neon_timeline_safety');safety.FOLDER=FOLDER
    safety.closed('before')
    baseline=json.loads((REVIEW/'output/windows-neon-381d5a9-20261117T003337/source-before.json').read_bytes())['source_sha256']
    assert safety.sources()==baseline
    wave_original=(REVIEW/'tests/waveform_levels_smoke.gd').read_bytes()
    replacements={
     'tests/animated_channels_smoke.gd':ROOT/'experiments/neon_timeline_fixture_followup_20261117/animated_channels_smoke.gd',
     'tests/movement_path_smoke.gd':ROOT/'experiments/neon_movement_fixture_managed_raster_20261117/movement_path_smoke.proposed.gd',
     'tests/waveform_levels_smoke.gd':ROOT/'experiments/neon_timeline_fixture_audit_20261117/waveform_levels_smoke.proposed.gd'}
    assert sha(replacements['tests/animated_channels_smoke.gd'])=='2714a15589dfe9175518ea04e002b9898ab160eb4fe9dac760b790957a546e4a'
    assert sha(replacements['tests/movement_path_smoke.gd'])=='b2c7d1131d291df99290f1ad5bd2327ff6716c8cbbeb903041fcd32544676ae4'
    proof=json.loads((ROOT/'experiments/neon_timeline_fixture_audit_20261117/WAVEFORM_INPUT_PROOF.json').read_bytes())
    for name,source in replacements.items():
        assert source.is_file();(FOLDER/(Path(name).name+'.original')).write_bytes((REVIEW/name).read_bytes())
        (REVIEW/name).write_bytes(source.read_bytes())
    before=safety.sources();safety.save(FOLDER/'source-before.json',before)
    experiment=REVIEW/'experiments/neon_auxiliary_runtime_20261117';experiment.mkdir(exist_ok=False)
    original_script=experiment/'original_waveform.gd';original_script.write_bytes(wave_original)
    observer=module(ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py','neon_timeline_observer')
    runner=module(REVIEW/'run.py','neon_timeline_runner')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=sys.executable,HYBRID_GODOT=r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe',HYBRID_FFMPEG=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe')
    rows=[]
    try:
        command=runner.command('tests/animated_channels_smoke.gd',extra=['--log-file',str(FOLDER/'animated-engine.log')])
        process,log=observer.invoke(FOLDER,'animated',command,150)
        receipt=json.loads(Path(command[command.index('--receipt')+1]).read_bytes())
        result=json.loads((REVIEW/'output/animated-channels-result.json').read_bytes())
        assert result['checks']==48 and len(result['native_samples'])==3
        safety.save(FOLDER/'animated-result.json',result)
        rows.append({'label':'animated','process':process,'result':result,'receipt':receipt});safety.closed('animated-after')
        for label,extra in [('movement',[]),('components',['--components'])]:
            command=[sys.executable,'-B',str(REVIEW/'tests/verify_movement_path.py'),*extra]
            process,log=observer.invoke(FOLDER,label,command,180)
            rows.append({'label':label,'process':process});safety.closed(label+'-after')
        wav=REVIEW/'output/neon-auxiliary-original-20261117-attempt1/waveform-case/impulses.wav'
        assert wav.is_file()
        for label,script,theme in [('classic-original','experiments/neon_auxiliary_runtime_20261117/original_waveform.gd','light'),('neon-reveal-only','tests/waveform_levels_smoke.gd','neon')]:
            folder=FOLDER/label;folder.mkdir(exist_ok=False);shutil.copy2(wav,folder/'impulses.wav')
            (folder/'prefs.cfg').write_text('[display]\ntheme="'+theme+'"\n',encoding='utf-8')
            command=runner.command(script,extra=['--log-file',str(folder/'engine.log'),'--',folder.as_posix()])
            process,log=observer.invoke(FOLDER,label,command,150)
            receipt=json.loads(Path(command[command.index('--receipt')+1]).read_bytes())
            markers=[line[len('WAVEFORM_LEVELS_SMOKE '):] for line in log.splitlines() if line.startswith('WAVEFORM_LEVELS_SMOKE ')]
            result=json.loads(markers[0]) if len(markers)==1 else None
            rows.append({'label':label,'process':process,'result':result,'receipt':receipt});safety.closed(label+'-after')
    finally:
        safety.closed('after');preserved=safety.sources()==before
        safety.save(FOLDER/'verification.json',{'format':'has_neon_focused_timeline_successors_1','rows':rows,'source_preserved_during_runs':preserved,'full_pass_claimed':False})
    print(json.dumps({'folder':str(FOLDER),'source_preserved':preserved,'rows':[{'label':r['label'],'exit':r['process']['exit'],'seconds':r['process']['seconds'],'result':r.get('result')} for r in rows]}))
if __name__=='__main__':main()
