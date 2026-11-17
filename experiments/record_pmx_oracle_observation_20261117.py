"""Select only scalar facts from a failed native-input oracle batch."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'output/PRIVATE-pmx-observation-oracle-attempt1'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
phase=load(folder/'PRIVATE_ORACLE_PHASE.json');rows=phase['cases']
assert len(rows)==4 and sum(r['completed'] for r in rows)==1 and all(r['preserved'] for r in rows)
assert not phase['all_cases_completed_and_preserved'] and phase['native_protocol_qualified'] is False
assert all(not r['unconfirmed_child_closure'] and not r['unstarted'] for r in rows)
witness=load(folder/'case-3/PRIVATE_ORACLE.json')
assert {k:len(v) for k,v in witness['records'].items()}=={'body':107,'bone':277,'joint':92}
for i in range(3):assert 'oracle table-count budget' in (folder/f'case-{i}/PRIVATE_FAILURE.log').read_text()
record={'observed_utc':datetime.now(timezone.utc).isoformat(),'format':'has_selected_pmx_oracle_native_input_observation_1',
 'phase':'independent_oracle_only','cases':4,'completed_cases':1,'preserved_original_copy_pairs':4,'unconfirmed_closure_cases':0,
 'refused_cases':3,'refusal':'oracle table-count budget; table/count diagnostic still required',
 'completed_case_counts':{'bones':277,'bodies':107,'joints':92},'candidate_reader_or_archive_executed':False,
 'compare_phase_blocked':True,'native_protocol_qualified':False,'physical_validity_simulation_or_production_adoption':False,
 'max_observed_python_allocation_peak_bytes':max(r['python_tracemalloc_peak_bytes'] for r in rows),
 'Windows_peak_RSS_measured':False,'hard_memory_or_IO_confinement_claimed':False,
 'private_phase_sha256':sha(folder/'PRIVATE_ORACLE_PHASE.json'),'raw_model_names_words_paths_witnesses_included':False}
dest=ROOT/'experiments/pmx_oracle_native_observation_actual_20261117';dest.mkdir(exist_ok=False)
(dest/'OBSERVATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
(dest/'README.md').write_text('One of four native inputs completed the independent oracle; three refused a table-size budget. All original/copy pairs were preserved and children closed. No candidate comparison, native-protocol qualification, model conversion or simulation is claimed. Native witnesses remain private.\n',encoding='utf-8')
files=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dest.iterdir())]
(dest/'INDEX.json').write_text(json.dumps({'format':'has_scalar_native_input_observation_packet_1','files':files},indent=2)+'\n',encoding='utf-8')
paragraph='''
### November 17, 2026 — first native PMX oracle observations

Root ran the sealed two-phase harness's oracle phase on four exact owner originals
and staged byte-equal copies. All four pairs were preserved, all owned children
closed, with no timeouts or ownership intervention. One independent witness
completed: 277 bones, 107 body declarations and 92 joints. The other three stopped
at the oracle table-count budget. Which table/count caused those refusals remains
to be measured; no limit has been widened or expected witness fitted.

The all-four freeze gate correctly prevents the candidate/comparison phase.
No candidate reader, archive roundtrip, native-protocol/physical/simulation/
production qualification is claimed. Maximum measured Python allocation peak
was 16,467,425 bytes; Windows RSS/hard-memory/I/O enforcement remain unmeasured
or unclaimed. All native words, names, witnesses and raw logs stay private.
'''
for name in ('LLM.md','docs/progress_memo.md'):
 with (ROOT/name).open('a',encoding='utf-8',newline='\n') as stream:stream.write(paragraph)
print(json.dumps({'cases':4,'completed':1,'refused':3,'native_qualified':False,'INDEX_sha256':sha(dest/'INDEX.json')}))
