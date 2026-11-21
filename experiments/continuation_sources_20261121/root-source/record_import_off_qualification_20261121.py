from pathlib import Path
import hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
def load(path):
    raw=path.read_bytes();return json.loads(raw),{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
first,first_pin=load(OUT/'import-off-followup-scoped-1795256301357827900/completion.json')
second,second_pin=load(OUT/'import-off-followup-scoped-1795256474017879900/completion.json')
last,last_pin=load(OUT/'import-off-followup-scoped-1795258730224048700/completion.json')
height,height_pin=load(OUT/'import-off-followup-scoped-1795256301357827900/height/verification.json')
physics,physics_pin=load(OUT/'import-off-followup-scoped-1795256301357827900/import-physics/verification.json')
movie,movie_pin=load(OUT/'import-off-followup-scoped-1795256474017879900/first-movie/verification.json')
scenario,scenario_pin=load(OUT/'import-off-followup-scoped-1795258730224048700/scenario-d-artifacts/verification.json')
assert height['failures']==0 and height['native_import']['checks']==15 and height['native_import']['failures']==0
assert physics['checks']==54 and physics['failures']==0
assert len(movie['results'])==2 and all(r['failures']==0 for r in movie['results'])
assert scenario['reports']['wire_unit']['checks']==28 and scenario['reports']['wire_unit']['failures']==0
assert scenario['reports']['writer']['checks']==30 and scenario['reports']['writer']['failures']==0
assert scenario['reports']['reader']['checks']==4 and scenario['reports']['reader']['failures']==0
assert scenario['reports']['reader']['sampled_frames']==49==scenario['reports']['reader']['physical_frames_exact']
assert last['status']=='PASS' and last['current_private_jobs']==2 and last['all_current_jobs_exit0']
for result in (first,second,last):
    assert all(result[k] for k in ('sources_unchanged','head_unchanged','parent_environment_preserved','prior_receipts_unchanged','all_current_private_jobs_isolated_closed'))
spec=importlib.util.spec_from_file_location('off_final_source',ROOT/'experiments/reference_body_20261120/run_full.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
sources=helper.snapshot();assert len(sources)==1103
(OUT/'IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf-8')
result={'format':'has_default_off_followup_qualified_1','status':'SCOPED_ROUTES_PASS_NEW_FULL_REQUIRED',
 'base_head':'435dc02426a7cdd313e43fe674c9008520845428','functional_source_count':1103,
 'production_change':'Beginner guidance explicitly teaches Physics On then Off; import policy/simulator/parser remain unchanged.',
 'modified_functional_files':['src/first_movie_lesson.gd','tests/height_import_native_smoke.gd','tests/first_movie_smoke.gd','tests/scenario_d_smoke.gd','tests/verify_scenario_d.py'],
 'new_functional_file':'tests/scenario_d_wire_unit.gd',
 'routes':{'height':{'writer_checks':height['checks'],'cold_reader':height['reader'],'native_checks':15,'raw_result_pin':height_pin},
  'import_physics':{'checks':54,'native_models':physics['native_models'],'raw_result_pin':physics_pin},
  'first_movie':{'results':movie['results'],'cue_onset_sample':movie['cue_onset_sample'],'raw_result_pin':movie_pin},
  'scenario_d':{'wire_checks':28,'writer':scenario['reports']['writer'],'reader':scenario['reports']['reader'],
   'audio_onset_sample':scenario['audio_onset_sample'],'manual_has_unchanged':scenario['manual_has_unchanged'],
   'originals_and_writer_cache_unavailable_for_cold_open':scenario['originals_and_writer_cache_unavailable_for_cold_open'],'raw_result_pin':scenario_pin}},
 'scope_composition':'Height/import passed before test-only first-movie repeat and scenario wire refinements; complete first-movie then final scenario passed separately. No single-batch or new WholeFull claim.',
 'scope_completion_pins':{'first_failed_batch':first_pin,'second_failed_batch':second_pin,'final_scenario_pass':last_pin},
 'all_executed_private_jobs_closed':True,'historical_full435':'FAIL1961.792s/source1102andHEADunchanged/113closedjobs/new626checksPASS/no fresh aggregate',
 'canonical_Full_result_groups_expected':182,'canonical_Full_for_1103':'NOT_RUN',
 'required_implementation_score':'52/54','formal_acceptance_score':'55/62','human_device_acceptance_claimed':False,
 'native_miku_face_qualification':'UNRUN: historical435 hosts require an explicit new-revision/catalogue port after successful Full.',
 'junko105':'PREFLIGHT_REFUSED before any process/job/assertion; same bytes but Node32/Python64 device identity conventions need versioned bridge.',
 'new_owner_review':'Not ready; prior435 prepared copy remains unverified and has old lesson instructions.'}
(OUT/'IMPORT_OFF_FOLLOWUP_QUALIFIED_20261121.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('routes','scope_completion_pins','modified_functional_files')},indent=2))
