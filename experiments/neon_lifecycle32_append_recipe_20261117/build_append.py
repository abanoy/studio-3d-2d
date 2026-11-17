"""ROOT ONLY: append standalone32 metadata; no native/runtime/query/Git actions."""
from pathlib import Path
import argparse
import gzip
import hashlib
import importlib.util
import json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
PRIOR=MAIN/'experiments/neon_fix_sequence_archive_recipe_20261117'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def admission():
    assert sha((PRIOR/'INDEX.json').read_bytes())=='eda61664e18d73d630820d44a3d7a63cb9d5e9710772f5516fc4e4e06d74621b'
    assert sha((PRIOR/'build_archive.py').read_bytes())=='a7aca86e1d64a20f4323f67a0d2c9b04203b1445d6cd424bece90360b2671a9e'
    spec=importlib.util.spec_from_file_location('sealed_neon_metadata_admission',PRIOR/'build_archive.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--recipe-index-sha256',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    raw_index=(HERE/'INDEX.json').read_bytes();assert sha(raw_index)==args.recipe_index_sha256;index=json.loads(raw_index)
    for row in index['files']:
        raw=(HERE/row['path']).read_bytes();assert sha(raw)==row['sha256'] and len(raw)==row['bytes']
    gate=admission();target=gate.safe(args.output)
    assert target.parent==gate.safe(MAIN/'experiments') and target.name.startswith('neon_world_lifecycle32_actual_packet_') and not target.exists()
    plan=json.loads((HERE/'INPUTS.json').read_bytes());payloads,bindings,jobs=gate.prepare_payloads(plan);assert len(jobs)==1
    target.mkdir(exist_ok=False)
    for name,raw in payloads.items():
        path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    for row in index['files']:
        path=target/'recipe'/row['path'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((HERE/row['path']).read_bytes())
    (target/'recipe/INDEX.json').write_bytes(raw_index)
    def save(name,value):(target/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    save('EXACT_SOURCE_BINDINGS.json',{'format':'has_neon_lifecycle32_exact_bindings_1','files':bindings})
    save('ACTUAL_RESULT.json',{'format':'has_neon_standalone32_append_actual_1','ROOT_verification':plan['verification'],'report':plan['report'],'formal12504_changed':False,'full_Windows_PASS_claimed':False,'unique_physical_jobs':1,'parent_recipe_sha256':plan['prior_sequence_recipe_index_sha256'],'native_arrays_art_media_or_projects_included':False})
    (target/'README.md').write_bytes((HERE/'README.md').read_bytes())
    files=[{'path':path.relative_to(target).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())} for path in sorted(target.rglob('*')) if path.is_file()]
    save('INDEX.json',{'format':'has_neon_lifecycle32_actual_append_packet_1','files':files,'file_count':len(files),'bytes':sum(row['bytes'] for row in files),'exact_bindings':len(bindings),'excludes':['INDEX.json']})
    for row in bindings:
        raw=(target/row['archive_path']).read_bytes();raw=gzip.decompress(raw) if row['gzip_exact_original'] else raw
        assert sha(raw)==row['sha256'] and len(raw)==row['bytes']
    print(json.dumps({'output':str(target),'INDEX_sha256':sha((target/'INDEX.json').read_bytes()),'exact_bindings':len(bindings),'physical_jobs':1}))


if __name__=='__main__':main()
