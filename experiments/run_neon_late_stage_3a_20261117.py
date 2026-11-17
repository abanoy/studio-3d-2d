"""Root-only targeted late-stage preflight; never substitutes for a canonical full."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
packet=ROOT/'experiments/neon_late_stage_cases_source_20261117'
assert sha(packet/'INDEX.json')=='790277ef5e25f78e63d46350dba0304dce6c083c84ad5e010ac478fcea865ea3'
for row in json.loads((packet/'INDEX.json').read_bytes())['files']:
 assert (packet/row['path']).stat().st_size==row['bytes'] and sha(packet/row['path'])==row['sha256']
spec=importlib.util.spec_from_file_location('root_late_canonical_cases',packet/'late_cases.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
parent=ROOT/'experiments/run_neon_scene_followup_20261117.py';raw=parent.read_bytes()
A.check_source((REVIEW/'tests/verify.py').read_bytes(),raw)
pins=json.loads((packet/'STATIC_SOURCE_PINS.json').read_bytes())
for name,row in pins['wrappers'].items():assert (REVIEW/'tests'/name).stat().st_size==row['bytes'] and sha(REVIEW/'tests'/name)==row['sha256']
anchor=b"                row['report'] = json.loads(report_path.read_bytes())\r\n"
assert raw.count(anchor)==1
extra=b"                A.assert_canonical_report(label, row['report'])\r\n"
modified=raw.replace(anchor,anchor+extra,1)
assert modified.replace(anchor+extra,anchor,1)==raw
scope={'__file__':str(parent),'__name__':'root_late_owned_host','A':A}
exec(compile(modified,str(parent),'exec'),scope)
scope['CASES']=A.CASES
def main():
 expected=json.loads((REVIEW/'output/windows-neon-696ca7f-20261117T170720480423/source-before.json').read_bytes())['source_sha256']
 expected['tests/color_sampler_smoke.gd']='102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'
 assert scope['sources']()==expected and len(expected)==1029
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REVIEW).strip()==b'3a3701ab6edfa81dc883759403c170b8555aab07'
 dirty=subprocess.check_output(['git','diff','--name-only','--','src','tests','tools','data','examples','project.godot','main.tscn','run.py','launch.pyw'],cwd=REVIEW,text=True).splitlines()
 assert all('__pycache__' in Path(n).parts or n.endswith('.pyc') for n in dirty)
 os.environ['HYBRID_NATIVE_FIXTURES']=str(ROOT/'output')
 # Attempt1 omitted the canonical native-input directory. Its component wrapper
 # correctly refused missing native coverage; preserve that closed failed run.
 native=Path(r'C:\a\dump\AvatarSample_A.vrm')
 assert sha(native)=='14d2b2c751e2d6b7739471b961d71b7b16ca28089c04d9465b9c71a113033ee3'
 os.environ['HYBRID_NATIVE_INPUTS']=r'C:\a\dump'
 os.environ['HYBRID_HECATIA_KRA']=str(ROOT/'output/owner-fixtures/hecatia.kra')
 os.environ['PYTHONDONTWRITEBYTECODE']='1'
 os.environ['HYBRID_SOURCEIO']=str(REVIEW/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
 os.environ['HYBRID_BLENDER']=r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'
 os.environ['HYBRID_FFMPEG']=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
 label=sys.argv[sys.argv.index('--label')+1];assert label.startswith('neon-late-3a-')
 result=None;completed=False
 try:
  result=scope['main']()
  report=json.loads((REVIEW/'output'/label/'verification.json').read_bytes())
  completed=result==0 and report['passed'] is True and len(report['rows'])==44 and [r['label'] for r in report['rows']]==[r[0] for r in A.CASES]
  if completed:
   for row in report['rows']:A.assert_canonical_report(row['label'],row['report'])
  return 0 if completed else 1
 finally:
  folder=REVIEW/'output'/label
  if folder.exists():scope['save'](folder/'TARGETED-COMPLETION.json',{'format':'has_targeted_neon_late_stage_completion_1','candidate_commit':'3a3701ab6edfa81dc883759403c170b8555aab07','expected_wrappers':44,'all44_completed_and_canonical_reports_passed':completed,'host_return':result,'full_PASS_or_merge_claimed':False})
if __name__=='__main__':raise SystemExit(main())
