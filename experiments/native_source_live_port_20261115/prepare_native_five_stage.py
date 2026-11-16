"""PREPARE ONLY: freeze an isolated native5 overlay; never launch/import drivers.

Root runs this after reviewing source and closing its prior runtime lease.
It does not invoke Git, CIM, engines, desktop helpers, parsers or network tools.
No original source/assets are overwritten. A failed preparation is retained.
"""
from pathlib import Path, PureWindowsPath
import argparse
import datetime
import hashlib
import json
import re
import shutil
import stat
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / 'experiments/source_native_five_port_candidate_v2_20261115'
PACKET_INDEX = '460b7719c1bab426aebcc1d04d97bf0d6932b0a6bcadb75db9000147fef6c657'
INPUT_RELATIVE = 'output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685'
BASELINE_RELATIVE = 'output/sfm-bone-bindings-native-launch-20261114T033026205/run/verification.json'
BASELINE_SHA = '10ee4a984c9e54b1acf37d79d5013a10780abe98416b8350f3edf3ee37277c4b'
NATIVE_INPUTS = {'scene.glb':'4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d',
                 'parameters.json':'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'}
TREES = ('src','tests','tools','data','examples')
ENTRYPOINTS = ('main.tscn','project.godot','run.py','launch.pyw')
SUPPORT = ('dependencies.json','THIRD_PARTY_NOTICES.md','docs/licenses.md')
OVERLAYS = {
    'source_secondary.gd':('src/source_secondary.gd','dcf861f26ff7829ec25e2616e56416dd68fa4bb6a32d5340c969b9c946d84e47'),
    'source_chain_math.gd':('src/source_chain_math.gd','31491fbde49b635edadda5e661fa3eecabf0f7e3598f0dc448c0d944ffa6f844'),
    'secondary_live.gd':('src/secondary_live.gd','2613b19ce53b3a50fd001fe4e5b39bca2814165148b036993549490aa96c33a9'),
    'test_drafts/source_native_five_state_unit.gd':('tests/source_native_five_state_unit.gd','ab40f406e7b2ececc719761f0f0246ecb347bf853d711c3901671c8b8d6d7174'),
    'test_drafts/source_native_five_live_ui.gd':('tests/source_native_five_live_ui.gd','ee14e069a6e9606edb1338aac1c91397d47fad9797148da09868babbc27c3a0a'),
    'test_drafts/source_native_five_capture.gd':('tests/source_native_five_capture.gd','b1dc120815f9e56b79ca4406dd3a04ddd5b0978510c6e5ca8234b11ae88ff58b'),
    'test_drafts/verify_source_native_five_live.py':('tests/verify_source_native_five_live.py','07c3c2e7403af0096753c1c8c2b6e8516cb3bd3b74b46cfdc29bb00fca90d3e0'),
    'test_drafts/run_five_state_owned.py':('experiments/native_source_live_port_20261115/run_five_state_owned.py','7c124269ae07e81e52c19901a61d941c1f977ab6a2691265bba5c63948b31cdc')}
BAD_PARTS = {'.git','.godot','__pycache__'}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def no_links(path):
    for item in (path,*path.parents):
        info = item.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400, str(item)


def identity(path):
    no_links(path)
    before = path.stat()
    assert path.is_file() and before.st_nlink == 1, str(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream,'sha256').hexdigest()
    after = path.stat()
    assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino), str(path)
    return {'bytes':after.st_size,'sha256':digest,'mtime_ns':after.st_mtime_ns,'file_id':after.st_ino}


def safe_relative(name):
    windows = PureWindowsPath(name)
    assert not windows.drive and not windows.root and not windows.anchor
    parts = name.split('/')
    assert parts and all(part and part not in {'.','..'} and part==part.rstrip(' .') for part in parts)
    assert all(not any(ord(char)<32 or char in '\\:<>"|?*' for char in part) for part in parts)
    assert not any(part in BAD_PARTS for part in parts)
    return Path(*parts)


def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def load(path):
    assert path.stat().st_size <= 16*1024*1024
    return json.loads(path.read_bytes())


def current_source():
    paths = []
    for tree in TREES:
        base = ROOT/tree;no_links(base)
        for path in base.rglob('*'):
            if '__pycache__' in path.parts or path.suffix=='.pyc':continue
            no_links(path)
            if path.is_dir():continue
            assert path.is_file(),str(path)
            paths.append(path)
    paths.extend(ROOT/name for name in ENTRYPOINTS)
    paths.extend(ROOT/name for name in SUPPORT if (ROOT/name).exists())
    names = [path.relative_to(ROOT).as_posix() for path in paths]
    assert len(names)==len(set(name.casefold() for name in names))
    return {name:identity(ROOT/name) for name in sorted(names)}


def copy_exact(source,target,expected,*,replace=False):
    assert identity(source)==expected
    target.parent.mkdir(parents=True,exist_ok=True);no_links(target.parent)
    assert replace or not target.exists()
    if target.exists():no_links(target)
    shutil.copy2(source,target)
    result = identity(target)
    assert result['bytes']==expected['bytes'] and result['sha256']==expected['sha256'] and result['mtime_ns']==expected['mtime_ns']
    assert identity(source)==expected
    return result


def packet_files():
    assert identity(PACKET/'INDEX.json')['sha256']==PACKET_INDEX
    index = load(PACKET/'INDEX.json')
    assert index['format']=='has_native_five_v2_unapplied_draft_index_1' and index['files_count']==32
    assert len(index['files'])==32 and sum(row['bytes'] for row in index['files'])==362609==index['bytes']
    rows = {}
    for row in index['files']:
        relative = safe_relative(row['path'])
        assert row['path'] not in rows
        found = identity(PACKET/relative)
        assert found['bytes']==row['bytes'] and found['sha256']==row['sha256']
        rows[row['path']] = found
    for source,(_destination,pin) in OVERLAYS.items():assert rows[source]['sha256']==pin
    return rows


def verify_preservation(folder,tag):
    assert re.fullmatch('[a-z0-9][a-z0-9-]{0,31}',tag)
    no_links(folder)
    manifest = load(folder/'STAGE-MANIFEST.json')
    assert manifest['format']=='has_native_five_isolated_stage_1' and Path(manifest['original_root'])==ROOT
    assert manifest['sealed_packet_index_sha256']==PACKET_INDEX
    for name,pin in manifest['metadata_sha256'].items():assert identity(folder/name)['sha256']==pin
    before = load(folder/'ROOT-FUNCTIONAL-BEFORE.json')
    after = current_source()
    assert before==after, 'Original root changed; retain evidence and stop before promotion.'
    for name,row in manifest['inputs'].items():assert identity(Path(row['original']))==row['original_identity']
    baseline = manifest['UI_baseline_reference_only_not_copied']
    assert identity(Path(baseline['path']))==baseline['identity']
    packet_files()
    result = {'format':'has_native_five_original_root_preservation_1','passed':True,'observed_utc':utc(),
              'stage_manifest_sha256':identity(folder/'STAGE-MANIFEST.json')['sha256'],
              'original_functional_files_exact':len(after),'original_two_inputs_exact':True,
              'baseline_verification_exact':True,'sealed_packet_exact':True,
              'no_runtime_or_lease_claim':'Read-only hashes only; root separately validates every terminal receipt/closure.'}
    path = folder/('ROOT-PRESERVATION-'+tag+'.json');save(path,result)
    print(json.dumps({'preservation_only':True,'passed':True,'report':str(path),'sha256':identity(path)['sha256']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare',action='store_true')
    action.add_argument('--verify-preservation',action='store_true')
    parser.add_argument('--attempt',type=int,default=1)
    parser.add_argument('--verification-tag',default='after-runs')
    parser.add_argument('--base-head-context',default='dbf0bc1145f74b5bbff814ec6a417ccd23ce0885')
    options = parser.parse_args()
    assert 1 <= options.attempt <= 99 and re.fullmatch('[a-f0-9]{40}',options.base_head_context)
    started = utc();original_root = ROOT.resolve(strict=True);no_links(original_root)
    output_parent = ROOT/'output';no_links(output_parent)
    folder = output_parent/('native-five-stage-attempt'+str(options.attempt))
    if options.verify_preservation:
        verify_preservation(folder,options.verification_tag);return
    assert not folder.exists() and folder.resolve().parent==output_parent.resolve()
    packet_before = packet_files()
    source_before = current_source()
    base = load(PACKET/'PROVENANCE.json')
    assert source_before['src/source_secondary.gd']['sha256']==base['base_sha256']
    assert source_before['src/secondary_live.gd']['sha256']==base['wrapper_source_sha256']
    for row in load(PACKET/'DEPENDENCIES.json')['files']:
        assert source_before[row['path']]['bytes']==row['bytes'] and source_before[row['path']]['sha256']==row['sha256']
    input_folder = ROOT/safe_relative(INPUT_RELATIVE)
    input_before = {name:identity(input_folder/name) for name in NATIVE_INPUTS}
    assert all(input_before[name]['sha256']==pin for name,pin in NATIVE_INPUTS.items())
    baseline = ROOT/safe_relative(BASELINE_RELATIVE)
    baseline_before = identity(baseline);assert baseline_before['sha256']==BASELINE_SHA
    folder.mkdir();studio = folder/'Studio';studio.mkdir()
    save(folder/'ROOT-FUNCTIONAL-BEFORE.json',source_before)
    copied = {}
    for name,row in source_before.items():
        copied[name] = copy_exact(ROOT/safe_relative(name),studio/safe_relative(name),row)
    overlays = []
    for source,(destination,pin) in OVERLAYS.items():
        target = studio/safe_relative(destination)
        previous = identity(target) if target.exists() else None
        copied_row = copy_exact(PACKET/safe_relative(source),target,packet_before[source],replace=True)
        assert copied_row['sha256']==pin
        overlays.append({'packet_source':source,'staged':destination,'sha256':pin,'bytes':copied_row['bytes'],
                         'preimage':previous,'identity':copied_row})
        copied[destination] = copied_row
    staged_inputs = {}
    for name,row in input_before.items():
        target = studio/safe_relative(INPUT_RELATIVE)/name
        staged_inputs[name] = {'original':str(input_folder/name),'staged':str(target),
                               'original_identity':row,'staged_identity':copy_exact(input_folder/name,target,row)}
    save(folder/'STUDIO-SOURCE-MAP.json',copied)
    source_after = current_source()
    save(folder/'ROOT-FUNCTIONAL-AFTER.json',source_after)
    assert source_after==source_before, 'Original root functional files changed; retain stage and stop.'
    assert {name:identity(input_folder/name) for name in NATIVE_INPUTS}==input_before
    assert identity(baseline)==baseline_before
    assert packet_files()==packet_before
    assert not (studio/'.git').exists() and not (studio/'.godot').exists()
    for name,row in copied.items():assert identity(studio/safe_relative(name))==row
    state_driver = studio/'experiments/native_source_live_port_20261115/run_five_state_owned.py'
    ui_driver = studio/'tests/verify_source_native_five_live.py'
    # These are command DATA only. No command/import/subprocess is executed here.
    commands = {
        'state_after_fresh_exclusive_lease':[str(Path(sys.executable).resolve()),'-B',str(state_driver)],
        'GUI_after_state_terminal_closure_and_new_exclusive_lease':[
            str(Path(sys.executable).resolve()),'-B',str(ui_driver),
            '--glb',str(input_folder/'scene.glb'),'--parameters',str(input_folder/'parameters.json'),
            '--baseline-verification',str(baseline),'--output',str(studio/'output/native-five-gui-attempt1'),
            '--run-gpu','--lease-confirmed'],
        'preservation_after_both_terminal_closures_before_main_promotion':[
            str(Path(sys.executable).resolve()),'-B',str(Path(__file__).resolve()),
            '--verify-preservation','--attempt',str(options.attempt),'--verification-tag','after-runs']}
    save(folder/'ROOT-ONLY-COMMANDS.json',commands)
    manifest = {'format':'has_native_five_isolated_stage_1','phase':'PREPARED_ONLY_NOT_PARSED_OR_EXECUTED',
                'started_utc':started,'finished_utc':utc(),'original_root':str(ROOT),'studio':str(studio),
                'base_HEAD_context_declared_not_checked_by_this_helper':options.base_head_context,
                'source_is_overlay_not_equal_to_nearest_Git_HEAD':True,'Git_CIM_engine_network_or_driver_executed':False,
                'runtime_lease_not_checked_or_granted_by_preparation':True,
                'sealed_packet_index_sha256':PACKET_INDEX,'base_functional_files':len(source_before),
                'staged_source_files':len(copied),'original_functional_before_after_exact':True,
                'product_overlays':3,'test_driver_overlays':5,'overlays':overlays,
                'protected_input_files_copied':2,'inputs':staged_inputs,
                'UI_baseline_reference_only_not_copied':{'path':str(baseline),'identity':baseline_before},
                'state_driver_binding':{'path':str(state_driver),'sha256':copied[state_driver.relative_to(studio).as_posix()]['sha256'],
                                        'observer_sha256':copied['tests/source_native_five_state_unit.gd']['sha256'],'proposed_checks':266},
                'UI_driver_binding':{'path':str(ui_driver),'sha256':copied['tests/verify_source_native_five_live.py']['sha256'],
                                     'observer_sha256':copied['tests/source_native_five_live_ui.gd']['sha256'],
                                     'capture_sha256':copied['tests/source_native_five_capture.gd']['sha256'],
                                     'proposed_writer_packed_linked_checks':[82,11,8]},
                'UI_label_scope':'Private experimental overlay still has original one-rule support text; semantic product text change is deferred until qualification.',
                'preservation':{'original_functional':True,'original_two_inputs':True,'baseline_verification':True,'sealed_packet':True},
                'metadata_sha256':{name:identity(folder/name)['sha256'] for name in [
                    'ROOT-FUNCTIONAL-BEFORE.json','ROOT-FUNCTIONAL-AFTER.json','STUDIO-SOURCE-MAP.json','ROOT-ONLY-COMMANDS.json']},
                'retention':'Keep failed and successful stages/proofs; preparation never deletes or closes anything.'}
    save(folder/'STAGE-MANIFEST.json',manifest)
    print(json.dumps({'prepared_only':True,'studio':str(studio),'manifest':str(folder/'STAGE-MANIFEST.json'),
                      'manifest_sha256':identity(folder/'STAGE-MANIFEST.json')['sha256'],
                      'source_files':len(copied),'overlays':8,'native_inputs_copied':2,'root_unchanged':True}))


if __name__=='__main__':main()
