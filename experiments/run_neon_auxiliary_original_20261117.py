"""Root counterfactual checks for unchanged older focused UI fixtures."""
from pathlib import Path
import importlib.util,json,os,sys
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
FOLDER=REVIEW/'output/neon-auxiliary-original-20261117-attempt1'
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def main():
    FOLDER.mkdir(exist_ok=False)
    safety=module(ROOT/'experiments/run_neon_behavior_original_20261116.py','neon_auxiliary_safety');safety.FOLDER=FOLDER
    safety.closed('before');before=safety.sources()
    snapshot=json.loads((REVIEW/'output/windows-neon-381d5a9-20261117T003337/source-before.json').read_bytes())['source_sha256']
    assert before==snapshot
    observer=module(ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py','neon_auxiliary_observer')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=sys.executable,HYBRID_GODOT=r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe',HYBRID_FFMPEG=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe')
    rows=[]
    try:
        for label,script,extra,timeout in [('movement','verify_movement_path.py',[],180),('waveform','verify_waveform_levels.py',['--output',str(FOLDER/'waveform-case')],1000)]:
            command=[sys.executable,'-B',str(REVIEW/'tests'/script),*extra]
            process,log=observer.invoke(FOLDER,label,command,timeout)
            row={'label':label,'process':process,'original_source_unchanged':safety.sources()==before,'result_kind':'Original focused fixture; success or failure retained, not a full verifier result'}
            rows.append(row);safety.closed(label+'-after')
    finally:
        safety.closed('after');preserved=safety.sources()==before
        safety.save(FOLDER/'verification.json',{'format':'has_neon_original_auxiliary_fixtures_1','rows':rows,'functional_source_preserved':preserved,'source_commit':'381d5a974d34eb4dc10208a44c1a54d178c72fbb','full_pass_claimed':False})
    print(json.dumps({'folder':str(FOLDER),'source_preserved':preserved,'rows':[{'label':r['label'],'exit':r['process']['exit'],'seconds':r['process']['seconds']} for r in rows]}))
if __name__=='__main__':main()
