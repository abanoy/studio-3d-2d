"""Read-only current checkpoint/shared-tool preflight; write one new receipt."""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import re
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
READER=ROOT/'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'


def functional_files():
    files=[p for name in ('src','tests','tools','data','examples') for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
    files += [ROOT/name for name in ('project.godot','main.tscn','run.py','launch.pyw')]
    return sorted(files)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-commit',required=True,help='Exact full checkpoint SHA after root publication')
    parser.add_argument('--expected-functional-count',required=True,type=int,help='Exact reviewed functional source count; current increment expects1019')
    parser.add_argument('--output',type=Path,help='New evidence JSON inside this checkout/output; never overwrites')
    options=parser.parse_args()
    expected=options.expected_commit.lower()
    assert re.fullmatch('[0-9a-f]{40}',expected),'Expected commit must be a complete40-digit SHA'
    assert options.expected_functional_count>0,'Positive expected functional count required'
    target=(options.output or ROOT/'output'/('native-five-full-preflight-'+str(time.time_ns())+'.json')).resolve()
    assert target.is_relative_to((ROOT/'output').resolve()) and target!=ROOT/'output','Receipt must stay inside this checkout/output'
    assert not target.exists(),'Preflight receipt already exists'
    assert hashlib.sha256(LOCK.read_bytes()).hexdigest()==LOCK_SHA,'Approved shared-input lock changed'
    spec=importlib.util.spec_from_file_location('has_stable_read_identity',READER)
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    lock=json.loads(LOCK.read_bytes())
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==expected,'Checkpoint differs from explicit expected commit'
    assert len(lock['runtime_executables'])==6
    for name,identity in lock['runtime_executables'].items():
        assert reader.identity(Path(name))==identity,'Approved runtime identity differs: '+name
    assert len(lock['sourceio_files'])==574 and reader.metadata_map(reader.SOURCEIO)==lock['sourceio_files'],'Pinned SourceIO catalogue changed'
    assert len(lock['exporter_noncache_sources'])==120 and reader.metadata_map(Path(lock['exporter_root']),'exporter')==lock['exporter_noncache_sources'],'Pinned exporter catalogue changed'
    files=functional_files()
    assert len(files)==options.expected_functional_count,'Functional source count differs from explicit expected count'
    sources={p.relative_to(ROOT).as_posix():reader.identity(p)['sha256'] for p in files}
    assert functional_files()==files,'Functional catalogue changed during preflight'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==expected,'Checkpoint changed during preflight'
    result={'format':'has_native_five_increment_full_preflight_1','passed':True,'source_commit':expected,
            'expected_functional_files':options.expected_functional_count,'functional_files':len(sources),'source_sha256':sources,
            'runtimes':6,'SourceIO_files':574,'exporter_sources':120,'all_shared_tool_identity_fields_preserved':True,
            'approved_lock_sha256':LOCK_SHA,'identity_reader_sha256':hashlib.sha256(READER.read_bytes()).hexdigest(),
            'helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'owner_review_or_original_inputs_modified':False,'process_query_or_runtime_launched':False,'cleanup_authorized':False,
            'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({key:value for key,value in result.items() if key!='source_sha256'}))
    print('Receipt: '+str(target))


if __name__=='__main__':main()
