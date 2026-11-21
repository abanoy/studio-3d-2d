"""Independent read-only source archive audit. Executes no archived program."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,re,stat,time
BASE=Path(r'C:/a/Programming/cloudflare/has-body-addition-20261120/experiments/continuation_components_20261121')
OUT=Path(__file__).resolve().parent
EXPECTED='7c55df063b99ecef1b0634690f884a2233ae9ead6a8218d8fa2f24c8de06b83d'
def need(ok,why):
 if not ok:raise RuntimeError(why)
def sha(data):return hashlib.sha256(data).hexdigest()
def signature(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode,getattr(s,'st_file_attributes',0))
def read(p):
 s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not getattr(s,'st_file_attributes',0)&0x400,'nonregular/link')
 b=p.read_bytes();need(signature(s)==signature(p.lstat()),'read drift');return b
def rel(n):
 need(type(n) is str and n,'path string');p=PurePosixPath(n)
 need(not p.is_absolute() and p.as_posix()==n and '..' not in p.parts and all(not re.search(r'[\\:<>"|?*]',x) and x==x.rstrip(' .') and not re.fullmatch(r'(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',x) for x in p.parts),'alias/noncanonical path');return Path(*p.parts)
def pairs(items):
 result={}
 for k,v in items:need(k not in result,'duplicate JSON key');result[k]=v
 return result
def load(b):return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(RuntimeError('nonfinite JSON')))
def walk(base):
 rows={};case=set()
 for here,dirs,files in os.walk(base,followlinks=False):
  for name in dirs+files:
   p=Path(here)/name;s=p.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'reparse/symlink');n=p.relative_to(base).as_posix();rel(n);need(n.casefold() not in case,'case collision');case.add(n.casefold())
  for name in files:
   p=Path(here)/name;rows[p.relative_to(base).as_posix()]=p
 return rows
raw=read(BASE/'CONTENTS.json');need(sha(raw)==EXPECTED,'contents pin');inventory=load(raw);rows=inventory['files'];actual=walk(BASE)
need(len(rows)==len({r['path'] for r in rows})==1108,'inventory rows/duplicates');need(set(actual)=={'CONTENTS.json'}|{r['path'] for r in rows},'exact membership')
allowed={'.gd','.json','.py','.md','.log','.godot','.cfg'}
private_keys={'raw_bones','raw_skin','raw_source_weights','normalized_source_weights','imported_weights','inverse_bind_matrices','vertex_positions','skin_vertices','bone_matrices','joint_indices','source_slot_ids','imported_slot_ids','raw_samples','calibration_failure','influence_failure'}
json_docs={};bytes_total=0;numeric_lists=[];embedded=[];closures=[];schema_counts={};inner_refs=0
for row in rows:
 n=row['path'];rel(n);p=actual[n];data=read(p);need(len(data)==row['bytes'] and sha(data)==row['sha256'],'payload mismatch '+n);bytes_total+=len(data)
 need(p.suffix.lower() in allowed,'unexpected extension');text=data.decode('utf-8-sig');need(chr(0) not in text,'binary NUL')
 need(not data.startswith((b'MZ',b'PK\x03\x04',b'glTF',b'\x89PNG',b'Rar!')),'binary magic')
 need(not re.search(r'data:[^\s\"\x27]{0,90};base64,[A-Za-z0-9+/=]{256,}',text),'encoded asset')
 if p.suffix=='.json':
  value=load(data);json_docs[n]=value
  def screen(v,trail='$'):
   if type(v) is dict:
    for k,x in v.items():need(not(k in private_keys and type(x) in (dict,list) and x),'private native array key '+n+' '+k);screen(x,trail+'/'+k)
   elif type(v) is list:
    if len(v)>32 and all(type(x) in (int,float) for x in v):numeric_lists.append({'path':n,'field':trail,'length':len(v)})
    for i,x in enumerate(v):screen(x,trail+'/'+str(i))
   elif type(v) is str and len(v)>4096 and re.fullmatch('[A-Za-z0-9+/=]+',v):embedded.append({'path':n,'field':trail,'length':len(v)})
  screen(value)
 if p.name=='SOURCE_PINS.json':
  m=json_docs[n]
  if type(m.get('files')) is list:declared=m['files'];schema='files'
  else:need(m.get('format')=='has_import_capability_diagnostics_source_candidate_1' and type(m.get('entries')) is list,'unnamed legacy schema');declared=m['entries'];schema='named_legacy_entries'
  names=[]
  for child in declared:
   q=p.parent/rel(child['path']);b=read(q);need(len(b)==child['bytes'] and sha(b)==child['sha256'],'nested pin mismatch');names.append(child['path']);inner_refs+=1
  need(len(names)==len(set(names))==len({x.casefold() for x in names}),'inner collision')
  need(set(walk(p.parent))=={'SOURCE_PINS.json'}|set(names),'exact nested closure')
  closures.append({'path':n,'format':m.get('format'),'schema':schema,'files':len(names)});schema_counts[schema]=schema_counts.get(schema,0)+1
need(bytes_total==inventory['payload_bytes']==14700087,'byte total');need(len(closures)==35,'closure count');need(not numeric_lists and not embedded,'privacy candidate requires review')
need(read(BASE/'CONTENTS.json')==raw and set(walk(BASE))==set(actual),'final preservation')
result={'format':'has_independent_components_archive_audit_1','status':'PASS','archive':'experiments/continuation_components_20261121','contents_bytes':len(raw),'contents_sha256':EXPECTED,'payload_files':1108,'payload_bytes':bytes_total,'files_including_inventory':len(actual),'nested_SOURCE_PINS_closures':len(closures),'nested_payload_references':inner_refs,'schema_counts':schema_counts,'exact_membership_hashes_singlelink_regular_UTF8_case_and_alias_checks':True,'duplicate_JSON_keys_or_nonfinite_values':False,'binary_or_native_asset_extensions_or_magic':False,'private_native_array_key_findings':0,'numeric_JSON_arrays_over32':numeric_lists,'encoded_asset_candidates':embedded,'archived_programs_executed':False,'source_or_archive_mutated':False,'new_Full_claimed':False,'human_or_native_appearance_acceptance_claimed':False,'privacy_limit':'Mechanical screen plus explicit source/evidence review; not a certification of every possible confidential phrase inside arbitrary source text. Synthetic vectors inside source programs are code, not observed private model arrays.','nested_closure_details':closures}
with (OUT/'AUDIT.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='nested_closure_details'},indent=2))
