from pathlib import Path
import hashlib,json
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
CANDIDATE=ROOT/'output/source-import-owner-candidate-20261114'
def stamp(path):
 data=Path(path).read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
expected='f7374de647d6029b02b0d1054fdaeb53f9eb5b3a6120f82c1b9d91eece0414b0'
assert stamp(CANDIDATE/'INDEX.json')['sha256']==expected
index=json.loads((CANDIDATE/'INDEX.json').read_bytes())
assert all(stamp(CANDIDATE/row['path'])=={'bytes':row['bytes'],'sha256':row['sha256']} for row in index['files'])
value={'format':'has_source_import_owner_negative_exit_readonly_review_1','decision':'Remove sentinel guard before port; frozen unrun candidate unchanged','frozen_candidate_index_sha256':expected,'candidate_files_verified_unchanged':len(index['files']),'guard_line':105,'effect':'Reservation retained, public pid dropped; next import allowed and overwrites old private reservation, leaking old entry','blocks_next_import':False,'future_change':'Remove only cached exit==-1 guard; keep sole actual creator/pinned engine/reservation/exited child/exactly-once release invariant','proposed_owned_child_case':'Authored gated Python SystemExit(-1) refusal; actual runtime test UNRUN','negative_exit_getter_alone_proves_map_disappearance':False,'runtime_or_WinAPI_probe':False,'main_docs_HEAD_or_frozen_candidate_mutation':False}
(BASE/'AUDIT.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
outer={'format':'has_metadata_source_packet_index_1','files':[{'path':p.name,**stamp(p)} for p in sorted(BASE.iterdir()) if p.is_file() and p.name!='INDEX.json']}
(BASE/'INDEX.json').write_text(json.dumps(outer,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(BASE),'index_sha256':stamp(BASE/'INDEX.json')['sha256'],'candidate_unchanged':True},indent=2))
