"""Private uploaded SFM corpus: native metadata/textures and production loose lookup.

Linux test tooling only. No mesh conversion or native app
posing/render claim. Never extracts archives, alters fixtures or publishes assets.
"""
from pathlib import Path,PurePosixPath
from zipfile import ZipFile
import argparse,hashlib,json,os,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from tools.source_case import sidecars
from source_installation import conversion_context
PIN='fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
ARCHIVE_SHA='cd44e1d053ac853c5d1628da9faa27a594337ebacb3587744dfa5d60758623de'

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for flag in ['inventory','asset-root','sourceio','sourceio-archive','output']:p.add_argument('--'+flag,type=Path,required=True)
 p.add_argument('--archive-index',type=Path);p.add_argument('--image',default='has-sourceio-metadata:local');o=p.parse_args()
 if sys.platform!='linux':p.error('This corpus runner requires the managed Linux Docker environment')
 folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False);inventory=o.inventory.resolve(strict=True);assets=o.asset_root.resolve(strict=True);decoder=o.sourceio.resolve(strict=True);packages=json.loads(inventory.read_bytes());assert packages
 assert digest(o.sourceio_archive)==ARCHIVE_SHA,'SourceIO archive differs from documented pin'
 with ZipFile(o.sourceio_archive) as z:
  for entry in z.infolist():
   if entry.is_dir():continue
   parts=PurePosixPath(entry.filename).parts;assert parts[0]=='SourceIO-'+PIN and '..' not in parts
   assert digest(decoder.joinpath(*parts[1:]))==hashlib.sha256(z.read(entry)).hexdigest(),'Pinned decoder content differs: '+entry.filename
 frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 env=os.environ.copy()
 for key in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']:env.pop(key,None)
 docker=['docker','--host=unix:///var/run/docker.sock']
 def execute(args,label,timeout=300):
  r=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,timeout=timeout);(folder/(label+'.log')).write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr;return r.stdout
 image_id=execute(docker+['image','inspect','--format','{{.Id}}',o.image],'image').strip()
 def container(script,label,extra=()):
  args=docker+['run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user',str(os.getuid())+':'+str(os.getgid()),'--memory','2g','--cpus','2','--tmpfs','/tmp:rw,size=64m']
  for source,target,readonly in [(decoder,'/sourceio',True),(assets,str(assets),True),(inventory,'/inventory.json',True),(ROOT/'tests'/script,'/probe.py',True),(folder,'/output',False)]:
   args+=['--mount','type=bind,src='+str(source)+',dst='+target+(',readonly' if readonly else '')]
  args += [image_id,'python3','/probe.py','--sourceio','/sourceio','--inventory','/inventory.json','--asset-root',str(assets),'--output','/output/'+label+'.json',*extra]
  execute(args,label);result=json.loads((folder/(label+'.json')).read_bytes());print(label+': completed',flush=True);return result
 metadata=container('source_sfm_metadata_probe.py','metadata');deps=container('source_sfm_dependency_probe.py','dependencies',['--metadata','/output/metadata.json'])
 model_count=sum(len(p['models']) for p in packages);assert metadata['summary']['models']==model_count and metadata['summary']['parsed']==model_count and not metadata['summary']['invalid_hierarchies']
 assert deps['summary']['models']==model_count and deps['summary']['texture_errors']==0 and deps['summary']['material_errors']==0 and deps['summary']['original_extracted_files_unchanged']
 aliases=[];complete=0;first=None;asset_hashes=0
 for package in packages:
  base=Path(package['folder']).resolve(strict=True);assert base.is_relative_to(assets)
  for model in package['models']:
   path=(base/model['path']).resolve(strict=True);assert path.is_relative_to(base);first=first or path
   with path.open('rb') as stream:header=stream.read(164)
   assert header[:4]==b'IDST' and struct.unpack_from('<I',header,76)[0]==path.stat().st_size
   crc=struct.unpack_from('<I',header,8)[0];found=sidecars(path);complete+=('.vvd' in found and any(k.endswith('.vtx') for k in found))
   for suffix,source in found.items():
    if source.name!=path.with_suffix(suffix).name:aliases.append({'archive':package['archive_name'],'model':model['path'],'suffix':suffix,'original_name':source.name})
    if suffix=='.vvd' or suffix.endswith('.vtx'):
     with source.open('rb') as stream:raw=stream.read(24)
     assert struct.unpack_from('<I',raw,8 if suffix=='.vvd' else 16)[0]==crc,'Geometry checksum differs: '+str(source)
  for name,expected in package['members'].items():
   path=(base/name).resolve(strict=True);assert path.is_relative_to(base);assert digest(path)==expected['sha256'];asset_hashes+=1
 assert complete==model_count
 archive_checks=0
 if o.archive_index:
  for row in json.loads(o.archive_index.read_bytes()):assert digest(Path(row['archive']))==row['sha256'];archive_checks+=1
 try:
  context=conversion_context(source=first);preflight={'eligible':True,'profile':context['source_profile']}
 except ValueError as error:preflight={'eligible':False,'error':str(error)}
 sourceio_hash=digest(decoder/'library/utils/pylib/linux/pylib.abi3.so');log=(folder/'dependencies.log').read_text();warnings=[line for line in log.splitlines() if '[WARNING]'in line or '[ERROR]'in line]
 proof=dict(format='has_sfm_uploaded_readonly_1',sourceio_pin=PIN,sourceio_archive_sha256=ARCHIVE_SHA,sourceio_native_sha256=sourceio_hash,docker_image_id=image_id,archives=len(packages),models=model_count,metadata=metadata['summary'],dependencies=deps['summary'],case_resolution=dict(complete_geometry_sets=complete,checksum_mismatches=0,aliases=aliases),extracted_file_hashes_checked=asset_hashes,archive_hashes_checked=archive_checks,material_syntax_diagnostics=warnings,conversion_preflight=preflight,source_sha256=frozen,scope=__doc__.strip())
 assert all(digest(ROOT/name)==sha for name,sha in frozen.items())
 (folder/'verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps({k:v for k,v in proof.items() if k not in ['source_sha256','case_resolution']},indent=2))
if __name__=='__main__':main()
