"""Read-only Git/blob/EOL verification for the hash-bound readback cleanup plan.

Reads the plan and Git objects; writes JSON only to stdout. It never reads,
changes, moves or deletes any planned source file.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,re,subprocess

PLAN_SHA='2030b3c4f6b838fa874a2cb93ad2a990f6b6d14d8e2088138f9c6065cf7c08ab'
PUBLISHED='c6782d2f0f7b6ebbe868214ceb975e42afd129dd'
GZIP_PATH='docs/benchmarks/readback_reconstructible_cleanup_plan_2026-11-12.json.gz'
GZIP_SHA='911f895858bf75b35021f037679a758e1bee5bccebfff05557b3d8da9ffade15'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    options=parser.parse_args(); root=options.workspace.resolve()
    def git(*args):return subprocess.check_output(['git',*args],cwd=root)
    def ancestor(older,newer):
        if subprocess.run(['git','merge-base','--is-ancestor',older,newer],cwd=root,capture_output=True).returncode:
            raise RuntimeError('Required revision is not reachable: '+older)
    raw=options.plan.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PLAN_SHA:raise RuntimeError('Raw plan SHA256 mismatch')
    packed=git('cat-file','blob',PUBLISHED+':'+GZIP_PATH)
    if hashlib.sha256(packed).hexdigest()!=GZIP_SHA:raise RuntimeError('Published gzip blob SHA256 mismatch')
    if gzip.decompress(packed)!=raw:raise RuntimeError('Published gzip content differs from exact raw plan')
    origin=git('rev-parse','origin/main').decode().strip(); ancestor(PUBLISHED,origin)
    plan=json.loads(raw); entries=plan['delete_individual_files']
    sources=[entry for entry in entries if entry['category']=='reconstructible_source']
    caches=[entry for entry in entries if entry['category']=='regenerable_python_bytecode']
    if (len(entries),sum(x['bytes'] for x in entries),len(sources),len(caches))!=(16875,224835913,16862,13):raise RuntimeError('Unexpected exact plan scope')
    revisions=sorted({entry['git_revision'] for entry in sources}); trees={}
    for revision in revisions:
        if not re.fullmatch('[a-f0-9]{40}',revision):raise RuntimeError('Invalid Git revision')
        ancestor(revision,PUBLISHED); tree={}
        for record in git('ls-tree','-rz',revision).split(b'\0'):
            if not record:continue
            metadata,name=record.split(b'\t',1);mode,kind,oid=metadata.split()
            tree[name.decode('utf-8')]=(mode.decode(),kind.decode(),oid.decode())
        trees[revision]=tree
    objects=sorted({entry['git_object'] for entry in sources})
    if any(not re.fullmatch('[a-f0-9]{40}',oid) for oid in objects):raise RuntimeError('Invalid Git object')
    batch=subprocess.check_output(['git','cat-file','--batch'],cwd=root,input=b''.join(oid.encode()+b'\n' for oid in objects))
    blobs={};offset=0
    for wanted in objects:
        end=batch.index(b'\n',offset);oid,kind,size=batch[offset:end].split()
        if oid.decode()!=wanted or kind!=b'blob':raise RuntimeError('Unexpected Git object response')
        start=end+1;finish=start+int(size);blobs[wanted]=batch[start:finish]
        if batch[finish:finish+1]!=b'\n':raise RuntimeError('Truncated Git object')
        offset=finish+1
    if offset!=len(batch):raise RuntimeError('Unexpected trailing Git object data')
    recipes={}
    for entry in sources:
        record=trees[entry['git_revision']].get(entry['relative_path'])
        if not record or record[0] not in ['100644','100755'] or record[1]!='blob' or record[2]!=entry['git_object']:
            raise RuntimeError('Git path/object/mode mismatch: '+entry['relative_path'])
        key=(entry['git_object'],entry['exact_eol_recipe'])
        if key not in recipes:
            data=blobs[key[0]]
            if key[1]=='git_blob_crlf_to_lf':data=data.replace(b'\r\n',b'\n')
            elif key[1]=='git_blob_normalized_crlf':data=data.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
            elif key[1]!='exact_git_blob':raise RuntimeError('Unknown source byte recipe')
            recipes[key]=(len(data),hashlib.sha256(data).hexdigest())
        if recipes[key]!=(entry['bytes'],entry['sha256']):raise RuntimeError('Git byte recipe mismatch: '+entry['path'])
    print(json.dumps({'format':'has_read_only_cleanup_git_verification_1','passed':True,'raw_plan_sha256':PLAN_SHA,'published_checkpoint':PUBLISHED,'published_gzip_git_path':GZIP_PATH,'published_gzip_sha256':GZIP_SHA,'published_gzip_matches_exact_raw_plan':True,'origin_main_at_check':origin,'published_checkpoint_reachable_from_origin':True,'source_revisions_reachable_from_checkpoint':revisions,'source_files':len(sources),'regenerable_caches':len(caches),'git_objects':len(objects),'byte_recipes':len(recipes),'all_git_paths_modes_objects_sizes_sha_and_eol_recipes_match':True,'source_files_read_or_changed':False},indent=2))

if __name__=='__main__':main()
