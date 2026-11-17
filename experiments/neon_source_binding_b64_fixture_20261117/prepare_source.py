"""Prepare one fixture-only source substitution; no engines, native files or Git."""
from pathlib import Path
import hashlib,json,re
HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
REL='tests/source_bone_bindings_unit.gd'
BEFORE=b'GOLDEN_GLB.replace("\\n", "")'
AFTER=b'GOLDEN_GLB.replace("\\r", "").replace("\\n", "")'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(name,raw):
 with (HERE/name).open('xb') as f:f.write(raw)
def main():
 old=(MAIN/REL).read_bytes();original=(REVIEW/REL).read_bytes()
 assert old.replace(b'\r\n',b'\n')==original.replace(b'\r\n',b'\n')
 blob=(HERE/'original-candidate-git-blob.gd').read_bytes()
 assert blob==old==original.replace(b'\r\n',b'\n')
 blob_oid=hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()
 assert blob_oid=='66f6af2b9236aefcab46ba29c4e7b63b01e7e144'
 assert original.count(BEFORE)==1 and AFTER not in original
 proposed=original.replace(BEFORE,AFTER,1);assert proposed.replace(AFTER,BEFORE,1)==original
 for name,raw in [('main52-source_bone_bindings_unit.gd',old),('original-source_bone_bindings_unit.gd',original),('source_bone_bindings_unit.proposed.gd',proposed)]:
  write(name,raw)
 unchanged={}
 for rel in ('tests/source_native_helper_choice_unit.gd','tests/verify_source_bone_bindings.py'):
  raw=(REVIEW/rel).read_bytes();write('original-'+Path(rel).name,raw);unchanged[rel]=sha(raw)
 rows=[];literal_candidates=[]
 for p in sorted((REVIEW/'tests').rglob('*')):
  if not p.is_file() or p.suffix not in ('.gd','.py'):continue
  raw=p.read_bytes()
  if p.suffix=='.gd':
   for m in re.finditer(rb'Marshalls\.base64_to_raw\(([^\r\n]*)',raw):
    rows.append({'path':p.relative_to(REVIEW).as_posix(),'line':raw[:m.start()].count(b'\n')+1,'call_prefix':m[1][:120].decode('ascii','replace'),'source_sha256':sha(raw)})
   for m in re.finditer(rb'(?:const|var)\s+(\w+)\s*:?=\s*"""(.*?)"""',raw,re.S):
    payload=m[2].replace(b'\r',b'').replace(b'\n',b'')
    if len(payload)>128 and re.fullmatch(rb'[A-Za-z0-9+/=]+',payload):
     literal_candidates.append({'path':p.relative_to(REVIEW).as_posix(),'symbol':m[1].decode(),'literal_source_bytes':len(m[2]),'CR':m[2].count(b'\r'),'LF':m[2].count(b'\n')})
 scan={'scope':'Source pattern scan across all candidate tests .gd/.py; only exact GDScript multiline-base64-constant/newline-removal pattern is classified. No general dataflow or runtime proof.','Godot_raw_decode_calls':rows,'multiline_base64_literal_candidates':literal_candidates,'same_embedded_newline_sensitive_constructs':[r for r in rows if 'GOLDEN_GLB.replace' in r['call_prefix']],'other_decode_sites':'Four Godot call sites consume expected.audio loaded/generated metadata, not a physical multiline constant. Python b64decode sites consume runtime JSON/object values; Python literal newline semantics are separate.','other_files_modified':False}
 write('LATENT_PATTERN_SCAN.json',(json.dumps(scan,indent=2)+'\n').encode())
 log=REVIEW/'output/canonical-spikes/1794886264394629400/source-choices/bindings-headless/bindings/run-engine.log'
 rawlog=log.read_bytes();rawlog.decode('utf-8-sig');write('closed375-bindings-run-engine.log',rawlog)
 proof={'format':'has_authored_GLB_fixture_EOL_source_proposal_1','main52_sha256':sha(old),'candidate375_working_sha256':sha(original),'working_sources_LF_bytes_exact':True,'candidate_working_CRLF_lines':original.count(b'\r\n'),'proposed_sha256':sha(proposed),'exact_one_expression_byte_inverse':True,'original_expression':BEFORE.decode(),'proposed_expression':AFTER.decode(),'unchanged_sources':unchanged,'expected_original_checks':{'bindings':79,'helper':17},'GLB_SHA_unchanged':'39637fa34e53c81708329ab963659e8100a285a92e25a22a92ab5e708c0154c1','BAD_CHUNKS_SHA_unchanged':'95e0c8785860cfce8ad34a60ff58feef6c65d22ea6a6d318d9523ddfdd0ff934','closed_failure_log':{'original':str(log),'sha256':sha(rawlog)},'literal_Git_blob_comparison':{'path':'original-candidate-git-blob.gd','bytes':len(blob),'sha256':sha(blob),'git_blob_oid_independently_recomputed':blob_oid,'main52_and_candidate375_Git_body_bytes_exact':True,'origin':'Root supplied immutable Gitshow375 blob; this source task did not run Git.'},'Godot_parse_or_execution':'UNRUN_ROOT_OWNED','product_code_or_predicate_or_threshold_changed':False,'native_input_files_or_engines_CIM_Git_read_or_run_by_preparation':False}
 write('SOURCE_PROOF.json',(json.dumps(proof,indent=2)+'\n').encode())
 print(json.dumps({'proposed_sha256':sha(proposed),'Godot_decode_sites':len(rows),'same_constructs':len(scan['same_embedded_newline_sensitive_constructs']),'multiline_base64_literals':len(literal_candidates),'no_runtime_execution':True},indent=2))
if __name__=='__main__':main()
