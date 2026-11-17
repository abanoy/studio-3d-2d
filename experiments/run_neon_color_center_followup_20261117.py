"""Root runs the original color verifier after the single input-fixture correction."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1]
support=ROOT/'experiments/run_neon_scene_followup_20261117.py'
assert hashlib.sha256(support.read_bytes()).hexdigest()=='07e37aa4ddba05e31658f2fe14bda53a25ce0f7646f2c966961a635ef6b85255'
spec=importlib.util.spec_from_file_location('root_centered_color_original_runner',support);H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
def main():
 before=json.loads((H.REVIEW/'output/windows-neon-696ca7f-20261117T170720480423/source-before.json').read_bytes())['source_sha256'];current=H.sources()
 assert len(current)==1029 and set(current)==set(before)
 assert {n for n in current if current[n]!=before[n]}=={'tests/color_sampler_smoke.gd'}
 assert current['tests/color_sampler_smoke.gd']=='102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=H.REVIEW).strip()==b'3a3701ab6edfa81dc883759403c170b8555aab07'
 dirty=subprocess.check_output(['git','diff','--name-only','--','src','tests','tools','data','examples','project.godot','main.tscn','run.py','launch.pyw'],cwd=H.REVIEW,text=True).splitlines()
 # The first prelaunch refused a tracked has_project.pyc. Match the declared
 # functional scope; preserve compiled caches and continue to reject all source dirt.
 assert all('__pycache__' in Path(n).parts or n.endswith('.pyc') for n in dirty)
 os.environ['HYBRID_NATIVE_FIXTURES']=str(ROOT/'output');os.environ['HYBRID_FFMPEG']=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
 H.CASES=(('color','verify_color_sampler.py',[],'color-sampler-verification.json',220),)
 return H.main()
if __name__=='__main__':raise SystemExit(main())
