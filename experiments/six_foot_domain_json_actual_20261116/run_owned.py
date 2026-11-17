"""ROOT ONLY: stage and sequentially run the reviewed windowless domain successor.

Source preparation does not import this module or execute main(). No CLI options.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PACKET = ROOT/'experiments/six_foot_domain_json_transport_20261116'
BOUNDARY_PACKET = ROOT/'experiments/six_foot_import_basis_gd_candidate_20261116'
PACKET_SHA = 'efa55eb23cd69ee7410059c9e01da8414b1b50a454db7bc6ba40a40984120147'
BOUNDARY_PACKET_SHA = '921579101eb9e97feeb62e8f7b0f22a392fe6536fa8fa9006ecb58650ead7125'
REVISION = '52f63c944ded7a651da871524d23a345b606424d'
FOLDER = ROOT/'output/six-foot-domain-20261116-attempt2'
ENGINE = Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
ENGINE_SHA = '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
OBSERVER = ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py'
OBSERVER_SHA = 'd6fc7ab7dba85c69658ce01e463f81c95912abbfeb16375e62a34be6db23096b'
FREEZER = ROOT/'tools/build_owner_review_snapshot.py'
FREEZER_SHA = '48d6fc852ae16c946431addd39ec152e5db45c7f887bc1ddc941fc332911a0ce'
PWSH = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PWSH_SHA = '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
RUNTIME_FILES = ('basis_domain_unit.gd','import_basis_domain.gd','PARITY_CORPUS_v3.json')
# Exact 1,029-file runtime closure from the preserved first attempt's 52f63c9 snapshot.
RUNTIME_SCOPE_TABLE_SHA = 'e13bb105840c76c6114763087746e81281a3e315fd3de2d7f8d94dfc078875c6'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def module(path,name):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def validate_packet(packet,digest):
    assert not packet.is_symlink() and sha(packet/'INDEX.json') == digest
    rows = load(packet/'INDEX.json')['files']
    assert isinstance(rows,list) and len({r['path'] for r in rows}) == len(rows)
    expected = {'INDEX.json'}
    for row in rows:
        path = packet/row['path']
        assert not path.is_symlink() and path.resolve().is_relative_to(packet.resolve())
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes']
        expected.add(row['path'])
    actual = {p.relative_to(packet).as_posix() for p in packet.rglob('*') if p.is_file()}
    assert actual == expected, 'Unexpected packet file'
    return rows


def stage(packet,names,studio,sources):
    target = studio/'experiments'/packet.name
    target.mkdir(parents=True,exist_ok=False)
    for name in names:
        original = packet/name
        to = target/name
        assert not original.is_symlink() and to.resolve().is_relative_to(target.resolve())
        to.parent.mkdir(parents=True,exist_ok=True)
        to.write_bytes(original.read_bytes())
        assert sha(to) == sha(original)
        sources[to.relative_to(studio).as_posix()] = sha(to)
    return target


def observe_sources(names):
    return {name:sha(ROOT/name) for name in sorted(names)}


def result_passes(result,label,count,job):
    expected_format = 'has_six_foot_gd_domain_result_1' if label == 'domain' else 'has_six_foot_boundary_result_1'
    named = result.get('named_checks',{})
    good = (result.get('format') == expected_format and result.get('checks') == count and
        result.get('expected_checks') == count and result.get('failures') == 0 and
        result.get('complete_assertion_set') is True and isinstance(named,dict) and
        len(named) == count and all(value is True for value in named.values()) and
        result.get('classification_run') is False and result.get('application_import_activation') is False)
    if label == 'domain':
        raw = result.get('raw_corpus_named_checks',{})
        failed = sorted(k for k,v in raw.items() if v is False) if isinstance(raw,dict) else []
        good = (good and result.get('synthetic_only') is True and result.get('native_assets_read') is False and
            result.get('job_script_sha256') == job['script_sha256'] and result.get('corpus_sha256') == job['corpus_sha256'] and
            result.get('comparison_contract') == 'exact_json_numbers_bounded_cross_type_1' and result.get('encoder_unchanged') is True and
            isinstance(raw,dict) and len(raw) == 434 and all(type(v) is bool for v in raw.values()) and
            failed == ['corpus.schema_encode_'+str(i) for i in range(7)] and
            len(result.get('strict_encode_differences',{})) == 7)
    else:
        good = good and result.get('owner_native_assets_read') is False
    return good


def main():
    # These checks precede helper imports, staging and all process creation.
    assert sha(ENGINE) == ENGINE_SHA and sha(PWSH) == PWSH_SHA
    assert sha(OBSERVER) == OBSERVER_SHA and sha(FREEZER) == FREEZER_SHA
    successor_rows = validate_packet(PACKET,PACKET_SHA)
    boundary_rows = validate_packet(BOUNDARY_PACKET,BOUNDARY_PACKET_SHA)
    assert sha(PACKET/'import_basis_domain.gd') == sha(BOUNDARY_PACKET/'import_basis_domain.gd')
    assert sha(PACKET/'PARITY_CORPUS_v3.json') == sha(BOUNDARY_PACKET/'PARITY_CORPUS_v3.json')
    assert FOLDER.resolve().is_relative_to((ROOT/'output').resolve()) and not FOLDER.exists()
    observer = module(OBSERVER,'six_foot_json_process_observer')
    freeze = module(FREEZER,'six_foot_json_frozen_runtime')
    FOLDER.mkdir(exist_ok=False)
    # The same observer provides retained handles, no-window creation and closure.
    observer.closure(FOLDER,'before')
    studio = FOLDER/'Studio'
    revision,sources = freeze.freeze_source(ROOT,studio,REVISION,runtime_scope=True)
    assert revision == REVISION
    assert len(sources) == 1029 and hashlib.sha256(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()).hexdigest() == RUNTIME_SCOPE_TABLE_SHA
    source_names = set(sources)
    source_names.update((PACKET.relative_to(ROOT)/row['path']).as_posix() for row in successor_rows)
    source_names.update((BOUNDARY_PACKET.relative_to(ROOT)/row['path']).as_posix() for row in boundary_rows)
    source_names.update(p.relative_to(ROOT).as_posix() for p in (PACKET/'INDEX.json',BOUNDARY_PACKET/'INDEX.json',Path(__file__),OBSERVER,FREEZER))
    source_before = observe_sources(source_names)
    observer.save(FOLDER/'SOURCE-BEFORE.json',source_before)
    target = stage(PACKET,RUNTIME_FILES,studio,sources)
    stage(BOUNDARY_PACKET,['INDEX.json']+[row['path'] for row in boundary_rows],studio,sources)
    override = studio/'override.cfg'
    override.write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS Six Foot JSON '+str(time.time_ns())+'"\n',encoding='utf-8')
    sources['override.cfg'] = sha(override)
    observer.save(FOLDER/'SOURCE.json',{'source_revision':revision,'source_sha256':sources,
        'prototype_packet_sha256':PACKET_SHA,'boundary_packet_sha256':BOUNDARY_PACKET_SHA,
        'root_driver_sha256':sha(Path(__file__)),'observer_sha256':OBSERVER_SHA,'freezer_sha256':FREEZER_SHA,
        'runtime_scope':True,'main_source_modified':False})
    results=[]
    passed=True
    error=None
    preserved=False
    originals_preserved=False
    after={}
    try:
        for label,packet,script,count in [('domain',PACKET,'basis_domain_unit.gd',480),('boundary',BOUNDARY_PACKET,'basis_boundary_unit.gd',21)]:
            out=studio/'output'/label
            out.mkdir(parents=True,exist_ok=False)
            relative='experiments/'+packet.name+'/'+script
            job={'format':'has_six_foot_'+label+'_job_1','phase':'ROOT_APPROVED_SIX_FOOT_'+label.upper(),
                'root_closed_all':True,'expires_unix':time.time()+600,'script_sha256':sha(studio/relative),'folder':out.as_posix()}
            if label=='domain':
                job.update(corpus=(target/'PARITY_CORPUS_v3.json').as_posix(),corpus_sha256=sha(target/'PARITY_CORPUS_v3.json'))
            observer.save(out/'job.json',job)
            for phase,extra in [('parse',['--check-only']),('run',[])]:
                name=label+'-'+phase
                command=[str(ENGINE),'--headless','--audio-driver','Dummy','--path',str(studio),
                    '--log-file',str(FOLDER/(name+'-engine.log')),'--script','res://'+relative,*extra,'--',str(out/'job.json')]
                process,stdout=observer.invoke(FOLDER,name,command,35 if phase=='parse' else 180)
                stderr=(FOLDER/(name+'-stderr.log')).read_text(encoding='utf-8',errors='replace')
                engine_log=FOLDER/(name+'-engine.log')
                logs=stdout+stderr+(engine_log.read_text(encoding='utf-8',errors='replace') if engine_log.exists() else '')
                errors=[s for s in logs.splitlines() if any(t in s for t in ('SCRIPT ERROR','ERROR:','WARNING:','ObjectDB instances leaked','resources still in use','FAIL basis_'))]
                good=process['exit']==0 and not process['timed_out'] and process['retained_Popen_reaped'] is True and not errors
                results.append({'label':name,'process':process,'passed':good,'error_markers':errors})
                if not good:
                    passed=False
                    break
            if not passed: break
            result=load(out/'result.json')
            good=result_passes(result,label,count,job)
            results[-1].update(assertion_set_passed=good,checks=result.get('checks'),expected_checks=count,
                result_format=result.get('format'),result_sha256=sha(out/'result.json'))
            if not good:
                passed=False
                break
    except Exception:
        passed=False
        error=traceback.format_exc()
    finally:
        # Source evidence and closure are attempted even after a probe/refusal error.
        try:
            preserved=all(sha(studio/name)==digest for name,digest in sources.items())
            source_after=observe_sources(source_names)
            originals_preserved=source_before==source_after
            observer.save(FOLDER/'SOURCE-AFTER.json',source_after)
        except Exception:
            error=(error or '')+'\nSOURCE CHECK: '+traceback.format_exc()
        try:
            after=observer.closure(FOLDER,'after')
        except Exception:
            error=(error or '')+'\nCLOSURE: '+traceback.format_exc()
    record={'format':'has_root_six_foot_domain_execution_1',
        'passed':passed and len(results)==4 and preserved and originals_preserved and after.get('owned_count')==0 and error is None,
        'results':results,'frozen_sources_preserved':preserved,'original_sources_preserved':originals_preserved,
        'runtime_lease_released':after.get('owned_count')==0,'headless_no_graphical_window_requested':True,
        'actual_import_activation':False,'main_source_modified':False,'successor_packet_sha256':PACKET_SHA,
        'boundary_packet_sha256':BOUNDARY_PACKET_SHA,'error':error}
    observer.save(FOLDER/'verification.json',record)
    print(json.dumps(record))
    return 0 if record['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
