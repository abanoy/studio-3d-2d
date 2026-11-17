"""ROOT ONLY filesystem archive builder; never call engines, CIM or Git."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
sha=lambda data:hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=['setter','failed381'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    plan=json.loads((HERE/'INPUTS.json').read_bytes())
    rows=plan['plans'][args.kind]
    target=args.output.resolve()
    prefix='normal_setter_actual_packet_' if args.kind=='setter' else 'neon_failed_381_actual_packet_'
    assert target.parent==(MAIN/'experiments').resolve() and target.name.startswith(prefix) and not target.exists()
    roots={name:Path(value) for name,value in plan['roots'].items()}
    payloads=[];bindings=[]
    for row in rows:
        source=roots[row['root']]/row['path']
        assert source.resolve().is_relative_to(roots[row['root']].resolve()) and not source.is_symlink()
        assert not source.name.startswith('PRIVATE') and source.suffix in {'.json','.log','.py','.md'}
        raw=source.read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
        raw.decode('utf-8','strict')
        body=gzip.compress(raw,compresslevel=9,mtime=0) if row['gzip_exact_original'] else raw
        if row['gzip_exact_original']:assert gzip.decompress(body)==raw
        path=target/row['archive_path'];assert path.resolve().is_relative_to(target)
        payloads.append((path,body));bindings.append({**row,'archive_sha256':sha(body),'archive_bytes':len(body)})
    index=json.loads((HERE/'INDEX.json').read_bytes())
    for row in index['files']:
        source=HERE/row['path'];raw=source.read_bytes()
        assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
        payloads.append((target/'recipe'/row['path'],raw))
    payloads.append((target/'recipe/INDEX.json',(HERE/'INDEX.json').read_bytes()))
    # No existing evidence or source file is changed. Every selected payload was pinned before writing.
    target.mkdir(exist_ok=False)
    for path,body in payloads:
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(body)
    (target/'EXACT_SOURCE_BINDINGS.json').write_text(json.dumps({'format':'has_public_archive_exact_sources_1','files':bindings},indent=2)+'\n',encoding='utf-8')
    if args.kind=='setter':
        summary={'format':'has_actual_setter_scalar_archive_1','measurement_completed':True,
            'measurement':'Exact native payload differs at first immediate setter readback; later validate readbacks and unobserved control match.',
            'models':plan['setter_scalar_summary'],'normal_fidelity':'FAILED_UNQUALIFIED','normal_reconstruction_implemented':False,
            'specific_Cpp_implementation_cause_proven':False,'native_arrays_or_private_logs_included':False,
            'private_result_hash_reference_only':plan['setter_private_hash_reference_only'],'private_result_bytes_reference_only':plan['setter_private_bytes_reference_only']}
        text='# Actual setter-boundary scalar evidence\n\nActual isolated measurement completed. Native setter payload words are exact; first immediate readback differs. Later validate readbacks retain the same normal words, and the unobserved control matches the saved readback. This narrows the observed boundary without proving a particular C++ cause or repairing the original failed GLB-normal gate.\n\nOnly the two public scalar reports, strict physical receipt, retained-process/closure metadata, exact staged command/context and source hashes/code are included. The private native result and all PRIVATE logs remain excluded. Gzip payloads decompress to exact originals.\n'
    else:
        summary={'format':'has_neon_381_failed_partial_archive_1','source_commit':'381d5a974d34eb4dc10208a44c1a54d178c72fbb',
            'suite_passed':False,'failed_fixture_checks':47,'failed_fixture_failures':1,'native_sample_cases_reported':3,
            'physical_jobs':27,'normal_exit0':25,'registered_Krita_cancel_exit2':1,'registered_animated_assertion_exit1':1,
            'closed_failed_lease_released':True,'root_process_termination_used':False,'final_full_report_used':False,
            'receipt_inventory_sha256':plan['failed381_inventory_sha256'],'failure_replaced_by_later_success':False,
            'native_arrays_media_projects_or_private_logs_included':False}
        text='# Closed failed Neon 381d5a9 run\n\nThe full suite failed in animated channels:47 checks,1 failure, all three native cases reported. Exact raw failure, canonical log,1028-file source catalogues and all27 physical receipts remain intact.25 jobs exited0, one registered Krita cancellation exited2, and the assertion-failing animated job exited1. Root observed exact original identities absent, handled PID reuse by birth and released only this closed failed partial lease without terminating processes.\n\nNo full PASS, later-suite result or unrun phase is inferred. The stale final full report is excluded. Gzip payloads decompress to exact originals.\n'
    (target/'ACTUAL_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    (target/'README.md').write_text(text,encoding='utf-8')
    files=[]
    for path in sorted(target.rglob('*')):
        if path.is_file():files.append({'path':path.relative_to(target).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())})
    index={'format':'has_source_experiment_index_1','packet':target.name,'files':files,'file_count':len(files),'bytes':sum(row['bytes'] for row in files),
        'excludes':['INDEX.json'],'private_native_arrays_media_or_projects_included':False,'source_kind':args.kind}
    (target/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    for row in bindings:
        body=(target/row['archive_path']).read_bytes()
        raw=gzip.decompress(body) if row['gzip_exact_original'] else body
        assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
    for row in files:
        body=(target/row['path']).read_bytes();assert len(body)==row['bytes'] and sha(body)==row['sha256']
    print(json.dumps({'kind':args.kind,'output':str(target),'files':len(files),'bytes':index['bytes'],'index_sha256':sha((target/'INDEX.json').read_bytes()),'exact_inputs_verified':len(rows)}))


if __name__=='__main__':main()
