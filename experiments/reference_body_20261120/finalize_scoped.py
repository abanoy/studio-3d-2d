"""Publish scalar observations only; never copy private model or image payloads."""
from pathlib import Path
import argparse,hashlib,json

ROOT=Path(__file__).resolve().parents[2]
PACKET=Path(__file__).resolve().parent


def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scoped',type=Path,required=True)
    parser.add_argument('--units',type=Path,required=True)
    args=parser.parse_args()
    scope=args.scoped.resolve(strict=True);units=args.units.resolve(strict=True)
    assert scope.is_relative_to(ROOT/'output') and units.is_relative_to(ROOT/'output')
    scoped=read(scope/'verification.json');unit=read(units/'verification.json')
    assert scoped['passed'] is True and scoped['sources_unchanged'] is True
    assert unit['passed'] is True and unit['sources_unchanged'] is True
    sources=read(scope/'source-before.json');assert sources==read(scope/'source-after.json')
    for name,row in sources.items():assert sha(ROOT/name)==row['sha256']
    native=scoped['results']['reference-body-native']['result']
    assert native['passed'] and len(native['results'])==6
    workflows={};receipts=[]
    for theme in ('neon','light'):
        row=scoped['results']['reference-body-'+theme]['result']
        names=('writer','cold_reader','parent_writer','parent_cold_reader')
        assert [row[name]['checks'] for name in names]==[72,21,18,6]
        workflows[theme]=dict(folder=row['folder'],checks={name:row[name]['checks'] for name in names},
                body_metrics=row['writer']['metrics'],parent_metrics=row['parent_writer']['metrics'],
                parent_cold_metrics=row['parent_cold_reader']['metrics'],
                exact_packed_authored_definitions=len(row['packed_authored_data']['cases']),
                native_float32_pose_bytes_exact=True,root_scale_exact=True,
                exact_preview_export_input_and_cold_pixels=True,functional_files_unchanged=row['functional_files_unchanged'])
        receipts += [row[name]['private_receipt'] for name in names]
    height={}
    for theme in ('neon','light'):
        row=scoped['results']['human-reference-'+theme]['result']
        assert row['writer']['checks']==44 and row['cold_reader']['checks']==3
        height[theme]={'writer':44,'cold_reader':3,'failures':0,'functional_files_unchanged':row['functional_files_unchanged']}
        receipts += [row[name]['private_receipt'] for name in ('writer','cold_reader')]
    native_rows=[]
    for row in native['results']:
        assert row['writer']['passed'] and row['reader']['passed']
        assert row['writer']['result']['checks']==23 and row['reader']['result']['checks']==9
        native_rows.append(dict(role=row['role'],scale=row['scale'],writer_checks=23,cold_reader_checks=9,
                metrics=row['writer']['result']['metrics'],failures=0))
        receipts += [row[name]['private_receipt'] for name in ('writer','reader')]
    private=[]
    for name in receipts:
        path=Path(name).resolve(strict=True);assert path.is_relative_to(ROOT/'output')
        row=read(path)
        assert row['exit']==0 and row['child_desktop_confirmed'] is True
        assert row['job_closed'] is True and row['desktop_closed'] is True
        assert row['foreground_child_observed'] is False and row['desktop_switch_requested'] is False
        private.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),**row))
    assert len(private)==len({row['desktop'] for row in private})==24
    content={name:{key:row[key] for key in ('sha256','bytes','git_sha1')} for name,row in sources.items()}
    source_tree=hashlib.sha256(json.dumps(content,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    product=('src/physics_rig.gd','src/physics_recording.gd','src/reference_body_plan.gd')
    tools=[r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe',r'C:\Program Files\Python313\python.exe',
           r'C:\Program Files\Python313\pythonw.exe',r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',r'C:\Program Files\ffmpeg\bin\ffprobe.exe']
    result=dict(format='has_reference_body_scoped_packet_1',date_local='2026-11-20',
            status='SCOPED_PASS_FULL_WINDOWS_PENDING',parent_commit='ab62adff5f6961d8605f15c79a01a0215c9c5425',
            source_tree_sha256=source_tree,source_and_driver_files_unchanged=len(content),
            product_source_sha256={name:sources[name]['sha256'] for name in product},
            tool_sha256={name:sha(Path(name)) for name in tools},
            units={name:row['result'] for name,row in unit['results'].items()},
            workflows=workflows,native_cases=native_rows,human_reference_regressions=height,
            scoped_seconds=scoped['seconds'],source_proof_sha256=dict(before=sha(scope/'source-before.json'),after=sha(scope/'source-after.json')),
            native_original_fixture_hash_size_mtime_unchanged=native['original_fixture_hash_size_mtime_unchanged'],
            native_staged_fixture_hash_size_mtime_unchanged=native['staged_fixture_hash_size_mtime_unchanged'],
            native_raw_bytes_read=False,native_fidelity_claimed=False,private_art_uploaded=False,
            private_jobs=private,formal_scores_unchanged=dict(implementation=[52,54],acceptance=[55,62]),
            failed_predecessors=[
                dict(case='test gravity API parse',scope='test-only',folder='output/body-physics-unit-1795192473250310500'),
                dict(case='test missing metadata getter errors',checks=785,assertion_failures=0,strict_pass=False,folder='output/body-physics-unit-1795192506660961900'),
                dict(case='workflow test Variant inference parse',scope='test-only',folder='output/body-workflow-first-1795192561753200600'),
                dict(case='actual parented recording drift',checks=14,failures=2,world_root_error_metres=.2100105732679367,folder='output/body-parent-first-1795193016777930600'),
                dict(case='corrected parent geometry but cold path assumption',checks=14,failures=1,world_root_error_metres=5.364418029785156e-7,folder='output/body-parent-fixed-1795193171286588400'),
                dict(case='Godot JSON expected-double parser mismatch',scope='test oracle; file data exact',folder='output/reference-body/neon-1795193360601077800'),
                dict(case='Godot loaded-double string mismatch',scope='test oracle; raw packed poses equal writer exactly',folder='output/reference-body/neon-1795193598937032800'),
                dict(case='packed parent extra path field assumption',scope='test-only; public72/21 pass',folder='output/reference-body/neon-1795193857807082800'),
                dict(case='unit driver expected18, actual unchanged17 recording checks',scope='test driver count corrected without changing assertions',folder='output/reference-body-units-1795193639984797000')])
    (PACKET/'SCOPED_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (PACKET/'SOURCE_CONTENT.json').write_text(json.dumps(content,indent=2)+'\n',encoding='utf-8')
    benchmark={key:value for key,value in result.items() if key not in ('private_jobs','workflows')}
    benchmark['workflows']={theme:{key:value for key,value in row.items() if key!='body_metrics'} for theme,row in workflows.items()}
    benchmark['private_desktop_summary']=dict(jobs=24,all_exit_zero=True,all_placed_closed_no_foreground_or_switch=True)
    (ROOT/'docs/benchmarks/reference_body_2026-11-20.json').write_text(json.dumps(benchmark,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],source_files=len(content),private_jobs=24,packet=str(PACKET),source_tree_sha256=source_tree),indent=2))


if __name__=='__main__':main()
