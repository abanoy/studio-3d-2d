"""Root-authorized read-only historical52 source/Git witness; no native assets."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
EXEC=ROOT/'experiments/neon_owner_review_executor_20261117'
sys.path.insert(0,str(EXEC))
import copy_executor as C
import qualified_inputs as Q
import admission_core as A

def save(name,raw):
 with (HERE/name).open('xb') as stream:stream.write(raw)
def doc(name,value):save(name,(json.dumps(value,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def main():
 H=C.helpers(ROOT)
 source=ROOT/'output/windows-canonical-bone-binding-20261116T041518335/source-before.json'
 H.no_links(source);before=H.identity(source);raw=source.read_bytes();H.need(H.identity(source)==before and A.digest(raw)==A.SOURCE52_SHA,'exact named CLOSED52source manifest differs')
 manifest=A.parse(raw);H.need(manifest['commit']==Q.SOURCE52 and len(manifest['source_sha256'])==1019,'historical52 scope differs')
 expected=manifest['source_sha256'];H.need(H.source_map()==expected,'currentMainfunctional1019 is not exact52testedraw')
 identities={};working={};total=0
 for name,digest in expected.items():
  H.need(Q.functional(name),'nonfunctional witness name refused');Q.validate_git_name(name)
  path=H.guarded(ROOT/name,ROOT);row=H.identity(path);H.need(row['bytes']<=128*1024*1024 and row['sha256']==digest,'source witness before identity differs')
  total+=row['bytes'];H.need(total<=512*1024*1024,'bounded source witness total exceeded')
  body=path.read_bytes();H.need(len(body)==row['bytes'] and A.digest(body)==digest and H.identity(path)==row,'source changed during witness')
  identities[name]=row;working[name]=body
 git_path=Path(shutil.which('git') or '').absolute();H.no_links(git_path);git_identity=H.identity(git_path)
 Git=Q.ApprovedGit(H,git_path,git_identity);H['subprocess']=Git
 blobs=H.git_blobs(Q.SOURCE52,list(expected));recipe={};git_rows={}
 for name,body in working.items():
  blob=blobs[name]
  mode=Q.infer_historical_eol_mode(blob,body,name)
  recipe[name]={'mode':mode,'git_blob_sha256':A.digest(blob),'tested_working_sha256':expected[name],'canonical_content_sha256':A.digest(A.canonical(body,name))}
  git_rows[name]={'bytes':len(blob),'sha256':A.digest(blob),'git_blob_oid':hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()}
 reconstructed=Q.reconstruct_historical52(blobs,manifest,recipe)
 H.need(all(reconstructed[n]==working[n] for n in expected),'reconstructable exact52raw witness differs')
 H.need(H.source_map()==expected and H.identity(source)==before and all(H.identity(ROOT/n)==row for n,row in identities.items()) and H.identity(git_path)==git_identity,'source/Git changed before witness seal')
 lock=(Q.OLD/'builder/input-lock.json').read_bytes();delta=(Q.OLD/'source-delta.json').read_bytes();historical=A.check_historical_predecessors(lock,delta,raw,reconstructed)
 H.need(historical['historical52_target_map_joined'] is True,'actual historical52 raw/content join missing')
 save('HISTORICAL52_MANIFEST.json',raw);doc('HISTORICAL52_WORKING_RECIPE.json',recipe)
 doc('SOURCE_IDENTITIES.json',{'format':'has_actual_historical52_raw_working_source_witness_1','source_revision':Q.SOURCE52,'source_count':1019,'source_bytes':total,'source_manifest_path':str(source),'source_manifest_identity':before,'raw_working_files':identities,'canonical_Git52_blobs':git_rows,'Git_executable':str(git_path),'Git_identity':git_identity,'currentMainHEAD_not_queried':True,'main_functional_before_after_exact52':True,'source_or_Git_or_EOL_bytes_written':False,'native_assets_other_outputs_REVIEW_or_engines_read':False})
 doc('RESULT.json',{'format':'has_historical52_recoverable_source_witness_result_1','passed':True,'scope':'ACTUAL_SOURCE_BYTES_AND_READONLY_GIT52_ONLY_NOT_NEW_FULL_OR_MERGE_QUALIFICATION','source_count':1019,'source_bytes':total,'source_manifest_sha256':A.digest(raw),'recipe_sha256':A.digest(A.encoded(recipe)),'historical_bridge_join':historical,'main_source_identities_before_after_exact':True,'Git_executable_identity_before_after_exact':True,'Git_mutations_native_or_other_full_output_reads':False,'raw_source_files_duplicated':False,'reconstruction_verified_all1019_byte_exact':True})
 print(json.dumps({'source_count':1019,'source_bytes':total,'all1019_raw_reconstruct_exact':True,'historical_raw_map_sha256':historical['old52_raw_source_map_sha256'],'historical_content_map_sha256':historical['old52_content_source_map_sha256'],'new_full_or_merge_claim':False},indent=2))
if __name__=='__main__':main()
