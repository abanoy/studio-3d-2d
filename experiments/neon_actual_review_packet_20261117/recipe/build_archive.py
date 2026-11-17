"""ROOT ONLY: build a new compact exact-evidence packet after reviewing this recipe.

No engine, CIM, Git, networking or source edits. Do not import/execute during preparation.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    options=parser.parse_args()
    plan=json.loads((HERE/'INPUTS.json').read_bytes())
    output=options.output.resolve()
    boundary=(MAIN/'experiments').resolve()
    assert output.parent==boundary and output.name.startswith('neon_actual_review_packet_') and not output.exists()
    # Fully validate all sources, destination names and scalar case evidence before writing.
    roots={name:Path(path).resolve() for name,path in plan['roots'].items()}
    catalogue=[]
    pending=[]
    for row in plan['files']:
        source=roots[row['root']]/row['path']
        assert source.resolve().is_relative_to(roots[row['root']]) and not source.is_symlink()
        target=output/row['archive_path']
        assert target.resolve().is_relative_to(output) and '..' not in Path(row['archive_path']).parts
        assert source.suffix in {'.json','.log','.gd','.py','.ps1','.md','.patch'}
        raw=source.read_bytes()
        assert len(raw)==row['bytes'] and sha(raw)==row['sha256'],source
        raw.decode('utf-8','strict')
        body=gzip.compress(raw,compresslevel=9,mtime=0) if row['gzip_exact_original'] else raw
        if row['gzip_exact_original']:assert gzip.decompress(body)==raw
        pending.append((target,body))
        catalogue.append({**row,'archive_sha256':sha(body),'archive_bytes':len(body)})
    assert len({str(path).casefold() for path,_ in pending})==len(pending)
    evidence={row['archive_path']:roots[row['root']]/row['path'] for row in plan['files']}
    load=lambda name:json.loads(evidence[name].read_bytes())
    original=load('original-full/state.json')
    closed=load('original-full/authoritative-host-closure.json')
    original_failure=load('original-full/object-timing-original-result.json')
    assert original['status']=='failed' and original['suite_exit']==1 and original['source_unchanged'] is True
    assert original_failure['checks']==28 and original_failure['failures']==2
    assert closed['physical_jobs']==24 and closed['all_jobs_and_desktops_closed'] is True and closed['exclusive_graphics_lease_released'] is True
    for label,failures in [('original-behavior',13),('candidate-v1',1),('diagnostic-only',1),('fixture-v2',1),('boundary-v3',0)]:
        result=load(label+'/result.json');verify=load(label+'/verification.json')
        assert result['checks']==32 and result['failures']==failures and result['complete_assertion_set'] is True
        assert sum(value is False for value in result['named_checks'].values())==failures
        assert verify['source_unchanged'] is True and verify['receipt']['job_closed'] is True and verify['receipt']['desktop_closed'] is True
        assert verify['receipt']['foreground_child_observed'] is False
    v3=load('boundary-v3/result.json')
    assert v3['refresh_preserved_faded_context'] is True
    six=load('separate-six-foot/verification.json')
    assert six['passed'] is True and six['frozen_sources_preserved'] is True and six['original_sources_preserved'] is True and six['runtime_lease_released'] is True
    geometry=load('geometry/verification.json')
    assert geometry['passed'] is True and [row['result']['checks'] for row in geometry['rows']]==[12384,14,45]
    recipe_index=json.loads((HERE/'INDEX.json').read_bytes())
    recipe_payloads=[]
    for row in recipe_index['files']:
        recipe_source=HERE/row['path']
        assert recipe_source.resolve().is_relative_to(HERE.resolve()) and recipe_source.suffix in {'.json','.py','.md'}
        data=recipe_source.read_bytes()
        assert len(data)==row['bytes'] and sha(data)==row['sha256']
        recipe_payloads.append((row['path'],data))
    recipe_payloads.append(('INDEX.json',(HERE/'INDEX.json').read_bytes()))
    # Store raw selected evidence exactly. No whole directories, images, projects, media or native arrays.
    output.mkdir(exist_ok=False)
    for target,body in pending:
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(body)
    for name,data in recipe_payloads:
        target=output/'recipe'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(data)
    (output/'EXACT_SOURCE_BINDINGS.json').write_text(json.dumps({'format':'has_neon_actual_archive_source_bindings_1','files':catalogue},indent=2)+'\n',encoding='utf-8')
    summary={'format':'has_neon_actual_review_archive_1','original_redesign_full_suite':'FAILED_28_CHECKS_2_FAILURES_RAW_RETAINED',
        'original_private_jobs':24,'original_jobs_and_desktops_closed':True,
        'original_behavior':'32/13','first_corrected_behavior':'32/1','diagnostic_only':'32/1','fixture_v2':'32/1','boundary_v3':'32/0',
        'geometry_inset':'12384/0','geometry_compact':'14/0','geometry_rail':'45/0',
        'separate_main_six_foot_domain':'480/0','separate_main_six_foot_boundary':'21/0',
        'six_foot_qualifies_neon_full_suite':False,'corrected_full_suite':'PENDING_SEPARATE_EXECUTION',
        'manual_owner_result':'DEFERRED_NO_RESULT','merge_or_product_completion_claimed':False,
        'cases':plan['cases'],'candidate_context_at_recipe_preparation':plan['candidate_context_at_recipe_preparation'],
        'selected_exact_files':len(catalogue),'owner_art_media_projects_or_native_arrays_included':False}
    (output/'ACTUAL_RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    (output/'README.md').write_text(
        '# Exact Neon review evidence\n\n'
        'The original full suite failed 28/2 in its final object-timing fixture after24 private jobs; its raw failed report, log, receipts and physical closure are retained. '
        'Original behavior32/13, corrected32/1, diagnostic32/1 and fixture-v2 32/1 remain separate exact failures. '
        'The boundary-corrected v3 passed32/0. Geometry checks passed12384/0,14/0 and45/0. '
        'Separate main six-foot tests passed480/0 and21/0; they do not qualify the Neon full suite.\n\n'
        'The corrected full Windows suite remains a separate required gate; no merge, complete-product or manual-owner acceptance is claimed here. '
        'The owner check is deferred. Gzip files decompress to exact originals; EXACT_SOURCE_BINDINGS.json records both hashes. '
        'All original failures are preserved rather than replaced by a later success. No images, native arrays, model/project files or media are included.\n',encoding='utf-8')
    rows=[]
    for path in sorted(output.rglob('*')):
        if path.is_file():rows.append({'path':path.relative_to(output).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())})
    index={'format':'has_source_experiment_index_1','packet':output.name,'files':rows,'file_count':len(rows),
        'bytes':sum(row['bytes'] for row in rows),'excludes':['INDEX.json'],'exact_failures_retained':True,
        'media_native_arrays_or_projects_included':False,'corrected_full_suite_claimed':False}
    (output/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    # Re-read every payload and every compressed original before declaring archival success.
    for row in rows:
        data=(output/row['path']).read_bytes();assert len(data)==row['bytes'] and sha(data)==row['sha256']
    for row in catalogue:
        data=(output/row['archive_path']).read_bytes()
        raw=gzip.decompress(data) if row['gzip_exact_original'] else data
        assert sha(raw)==row['sha256'] and len(raw)==row['bytes']
    print(json.dumps({'archive':str(output),'index_sha256':sha((output/'INDEX.json').read_bytes()),'files':len(rows),
        'bytes':index['bytes'],'verified_exact_originals':len(catalogue),'corrected_full_suite_pending':True}))


if __name__=='__main__':main()
