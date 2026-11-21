"""Record actual scoped results without promoting a failed aggregate."""
from pathlib import Path
import json,hashlib,time
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent;OUT=ROOT/'output'
locations={
 'contact129':BASE/'has-contact-rotation-scoped-1795264307051952500/PUBLIC_RESULT.json',
 'remaining29':BASE/'has-import-off-full-20261121-c31576d/output/remaining-scopes-1795264927106378400/completion.json',
 'media21':BASE/'has-import-off-full-20261121-c31576d/output/final-media-scope-1795266622623306000/RESULT.json',
 'import163':BASE/'has-import-info-headless163-1795265372302394400/PUBLIC_RESULT.json',
 'follow66':BASE/'has-part-follow-skeleton66-v2-1795266904469046600/RESULT.json',
 'maps64':BASE/'has-prepared-map-editor64-1795268002799951700/ROOT_RESULT.json',
 'failed_full':BASE/'has-import-off-full-20261121-c31576d/output/windows-reference-body-1795260488673286600/completion.json',
 'failed_import_component0':BASE/'has-import-info-canonical267-1795267340933340400/ROOT_RESULT.json',
}
pins={}
for name,path in locations.items():
 raw=path.read_bytes();value=json.loads(raw);pins[name]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 if name=='failed_full':assert value['exit']==1 and not value['whole_verifier_pass']
 elif name=='failed_import_component0':assert value['status']=='FAIL' and value['component_checks']==0
 else:assert value['status'].startswith(('PASS','SCOPED'))
record={'format':'has_scoped_continuation_progress_1','date':'2026-11-21','revision':'c31576d0c1d84030d51ec886f2f3976a60a70c7b',
 'aggregate':'FAILED; fresh committed-source Full required','formal_implementation':[52,54],'formal_acceptance':[55,62],
 'source_preserved_during_scopes':True,'completed_scopes':{'contact':129,'remaining_standalone_wrappers':29,'remaining_private_jobs':70,'canonical_movies':21,'import_headless':163,'part_follow_skeleton':66,'prepared_map_editor':64},
 'map_scope':{'maps':['gm_construct','ttt_tiny_spaceship_v3'],'checks_each':32,'parse_checks':0,'owned_headless_jobs_closed':4,'geometry_mesh_nodes':[310,234],'lights':[64,18],'conversion':'replay of earlier prepared output through actual current SourceImport and editor','new_conversion':False,'graphics':False,'artist_appearance_approved':False},
 'part_follow_scope':'Separate actual Model/Skeleton3D controls and 54 generated links. No real Junko binding, SecondaryLive integration or Main adoption.',
 'import_scope':'163 headless pass. New combined public verifier first failed0 on headless receipt classification; corrected version pending actual completion.',
 'failed_and_refused_results_preserved':True,'human_or_device_observations_added':False,'evidence':pins,'recorded_ns':time.time_ns()}
target=ROOT/'docs/benchmarks/components_followup_2026-11-21.json'
assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
