"""Independent readonlyGit52 reconstruction; no currentMain source/native reads."""
from pathlib import Path
import hashlib,json,os,re,subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def need(ok,text):
 if not ok:raise ValueError(text)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def identity(path):
 for item in (path,*path.parents):need(not item.is_symlink() and not getattr(item.lstat(),'st_file_attributes',0)&0x400,'reparse tool path')
 s=path.stat();raw=path.read_bytes();t=path.stat();need((s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns),'tool changed while read');return {'bytes':len(raw),'mtime_ns':s.st_mtime_ns,'sha256':sha(raw)}
def decode(blob,mode):
 if mode=='exact_Git_blob':return blob
 base=blob.replace(b'\r\n',b'\n')
 if mode=='explicit_CRLF_to_LF':return base
 if mode=='explicit_canonical_LF_to_CRLF':return base.replace(b'\n',b'\r\n')
 fields=mode.split(':');need(len(fields)==3 and fields[0]=='explicit_per_newline_CRLF_mask' and fields[1].isdigit() and re.fullmatch('[0-9a-f]*',fields[2]) and len(fields[2])%2==0,'unknown EOL recipe')
 count=int(fields[1]);mask=bytes.fromhex(fields[2]);ends=[i for i,x in enumerate(base) if x==10]
 need(count==len(ends) and len(mask)==(count+7)//8 and (not count%8 or mask[-1]>>(count%8)==0),'invalid EOL mask extent')
 result=bytearray();last=0
 for n,end in enumerate(ends):
  result.extend(base[last:end])
  if mask[n//8]&(1<<(n%8)):result.append(13)
  result.append(10);last=end+1
 result.extend(base[last:]);return bytes(result)
def main():
 raw=(HERE/'HISTORICAL52_MANIFEST.json').read_bytes();need(sha(raw)=='4b1eb25e1da8e510106fe3dd01c4b5014c7cc719133f18e1bbccd386ec9deae7','historical manifest authority changed')
 manifest=json.loads(raw);recipe=json.loads((HERE/'HISTORICAL52_WORKING_RECIPE.json').read_bytes());record=json.loads((HERE/'SOURCE_IDENTITIES.json').read_bytes());need(len(recipe)==1019 and set(recipe)==set(manifest['source_sha256'])==set(record['canonical_Git52_blobs']),'witness membership changed')
 git=Path(record['Git_executable']);need(identity(git)==record['Git_identity'],'exact Git tool changed')
 env=os.environ.copy();env['GIT_OPTIONAL_LOCKS']='0'
 args=[str(git),'--no-optional-locks','-c','core.fsmonitor=false','cat-file','--batch']
 result=subprocess.run(args,input=b''.join(v['git_blob_oid'].encode()+b'\n' for v in record['canonical_Git52_blobs'].values()),cwd=ROOT,env=env,capture_output=True,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 need(result.returncode==0 and not result.stderr,'owned readonlyGit52 read failed');batch=result.stdout;offset=0;raw_map={};content={};modes={}
 for name,item in record['canonical_Git52_blobs'].items():
  end=batch.index(b'\n',offset);oid,kind,size=batch[offset:end].split();start=end+1;stop=start+int(size);blob=batch[start:stop]
  need(oid.decode()==item['git_blob_oid'] and kind==b'blob' and len(blob)==item['bytes'] and sha(blob)==item['sha256'] and batch[stop:stop+1]==b'\n','exact Git52 body differs');offset=stop+1
  row=recipe[name];need(row['git_blob_sha256']==sha(blob),'recipe Git body differs');body=decode(blob,row['mode'])
  need(sha(body)==manifest['source_sha256'][name]==row['tested_working_sha256']==record['raw_working_files'][name]['sha256'] and len(body)==record['raw_working_files'][name]['bytes'],'independent raw reconstruction differs')
  # Source names are the immutable approved functional manifest; same narrow
  # text-domain list as the reviewed witness. No file is opened at those names.
  text=Path(name).suffix in {'.py','.pyw','.gd','.gdshader','.tscn','.tres','.json','.godot','.cfg','.uid','.txt','.md','.svg'} or name in {'tests/blank','tests/krita_fixture/has_fixture.desktop','tools/docker/sourceio_metadata.Dockerfile','tools/docker/sourceio_worker.Dockerfile','tools/krita-runtime.Dockerfile'}
  canonical=body.replace(b'\r\n',b'\n') if text else body;need(sha(canonical)==row['canonical_content_sha256'],'canonical content differs')
  raw_map[name]=sha(body);content[name]=sha(canonical);modes[row['mode'].split(':')[0]]=modes.get(row['mode'].split(':')[0],0)+1
 need(offset==len(batch) and identity(git)==record['Git_identity'],'trailing bytes or changed Git tool')
 report={'format':'has_independent_historical52_recoverability_result_1','passed':True,'files':1019,'all_raw_bytes_reconstruct_to_exact_closed_full_source_hashes':True,'decoder_independent_of_capture_and_future_adapter':True,'mode_counts':modes,'currentMain_functional_or_native_inputs_read':False,'Git_mutations':False,'new_full_or_merge_qualification':False}
 with (HERE/'RECOVERABILITY.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
