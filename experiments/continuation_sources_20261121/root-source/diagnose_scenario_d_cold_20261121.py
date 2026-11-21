"""Repeat only failed cold read, retaining exact strings and bounded differences."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
case=ROOT/'output/import-off-followup-scoped-1795256798459581600/scenario-d-artifacts'
source=ROOT/'tests/scenario_d_smoke.gd';raw=source.read_text(encoding='utf-8')
old='  for at in range(48,-1,-1):exact=exact and sample_stamp(expected.ids,at)==expected.samples[str(at)]'
new='''  var actual_stamps: Dictionary={};var differences: Array=[]
  for at in range(48,-1,-1):
   var actual_text: String=sample_stamp(expected.ids,at);var expected_text: String=expected.samples[str(at)]
   actual_stamps[str(at)]=actual_text
   if actual_text!=expected_text:
    exact=false
    var first:=0
    while first<mini(actual_text.length(),expected_text.length()) and actual_text[first]==expected_text[first]:first+=1
    differences.append({"frame":at,"parsed_equal":JSON.parse_string(actual_text)==JSON.parse_string(expected_text),"expected_length":expected_text.length(),"actual_length":actual_text.length(),"first_different_character":first,"expected_excerpt":expected_text.substr(maxi(0,first-30),100),"actual_excerpt":actual_text.substr(maxi(0,first-30),100)})
  FileAccess.open(folder.path_join("actual-stamps-diagnostic.json"),FileAccess.WRITE).store_string(JSON.stringify(actual_stamps,"",true,true))
  FileAccess.open(folder.path_join("cold-differences-diagnostic.json"),FileAccess.WRITE).store_string(JSON.stringify(differences,"",true,true))
  print("SCENARIO_D_COLD_DIAGNOSTIC ",JSON.stringify({"mismatching_frames":differences.size(),"examples":differences.slice(0,3)}))'''
assert raw.count(old)==1;raw=raw.replace(old,new,1)
script=ROOT/'output/scenario_d_cold_diagnostic_20261121.gd';assert not script.exists();script.write_text(raw,encoding='utf-8')
logs=ROOT/'output'/('scenario-d-cold-diagnostic-'+str(time.time_ns()));logs.mkdir()
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
for key in ('APPDATA','LOCALAPPDATA','TEMP','TMP'):
    path=logs/key;path.mkdir();env[key]=str(path)
inputs={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,script,case/'scenario-d.has',case/'expected.json')}
args=command('output/scenario_d_cold_diagnostic_20261121.gd',extra=['--audio-driver','Dummy','--log-file',str(logs/'engine.log'),'--',str(case),'--read'])
with (logs/'stdout.log').open('wb') as out,(logs/'stderr.log').open('wb') as err:
    proc=subprocess.Popen(args,cwd=ROOT,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    try:proc.wait(timeout=90)
    except subprocess.TimeoutExpired:proc.kill();proc.wait();raise
receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
assert r['exit']==proc.returncode and r['job_closed'] and r['desktop_closed'] and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and not r['desktop_switch_requested']
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in inputs.items())
result={'format':'has_scenario_d_cold_diagnostic_1','exit':proc.returncode,'pid':proc.pid,'child_reaped':proc.poll() is not None,
 'all_private_resources_closed':True,'inputs_preserved':True,'main_test_unchanged':True,'receipt':str(receipt),'receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),
 'diagnostic_source_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'failed_assertion_not_waived':True,'whole_full_claimed':False}
(logs/'completion.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result));print((case/'cold-differences-diagnostic.json').read_text()[:2200]);print(str(logs))
