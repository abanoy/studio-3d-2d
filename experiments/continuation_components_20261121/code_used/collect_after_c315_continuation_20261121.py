"""Explicit source/evidence collection; audits by default, never finalizes/publishes."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, stat, time

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent
ALLOW = ROOT/'output/AFTER_C315_COLLECTION_ALLOWLIST_DRAFT_V1_20261121.json'
PACKETS = {
 'source-full-c315-failed-prep-20261121':'89e7e0165a7b7b1bc5051c64f253545831d706f67b07af026601340fd7661ec1',
 'source-miku-contact-c315-1103-successor-prep-20261121':'7a7fa46b26ff626d6f3a157679523c92192bdc48af39649239eca770e95bc60b',
 'source-posed-head-native-c315-1103-qualification-prep-20261121':'6830cf03f2432c75757bae67e88cfd1c6b518eef84ea600de2f8e01e5f2f4aba',
 'source-keyframe-easing-c315-graphics-v2-prep-20261121':'b8d482e75aeca185a56abcdf87ae42af2d5f98b0a28fe2cb1675e7e75d0d4ab3',
 'source-easing-c315-graphics-qualification-prep-20261121':'71f1ea3af625b2032639ef4837c4a195d086b31e94a72d81a82aa7b31a9a8466',
 'source-editor-camera-owner-review-c315-prep-20261121':'fc300f4772a88a310b86d640fffe94230b8bbcd5387d48cde7d922c93c56a21f',
 'source-owner-review-c315-replay-prep-20261121':'9fdf8e5dc25724816ea081b64305ab95e424cbc721080c96baeb36bfdb5eef2f',
 'source-easing-cpu-cleanup-readiness-prep-20261121':'66e6b911c56f61b5adcc95ef1978e95578e74e74b2365eb4a9b204847d17ad29',
 'source-junko-composed-qualification-evidence-prep-20261121':'db3df2204a5317bdd2f1966accb1ba6ddc32934f8f76d44c48fe622b395573f8',
 'source-character-pose-follow-prep-20261121':'9070c635a32b7379adbece0236e5cfa4b76532d3c5b30f95b031c17b977f4232',
 'source-character-pose-follow-controller-prep-20261121':'98e123065b42cdccd38e8e5348b27ac6fcc6db50517789786bbf3a7ea0a94963',
 'source-character-pose-follow-controller-v2-prep-20261121':'36d195a0bf9cc2a22053e3de53ddd937b9a54562acda64005053c36f01f5afa5',
 'source-part-follow-skeleton66-evidence-prep-20261121':'95c72ef1f8e20429732a5895207f7fc361d71e02278ead0d63b8369096ac6d8d',
 'source-import-capability-c315-prep-20261121':'5cb9ea727f550857ccb005a1a6c47bdda2eb1979ec4e11c6cae64903062f0812',
 'source-import-capability-headless163-c315-prep-20261121':'913b27870fe44329f2a271f743ce132eb405a87176f7a209787e085f2b084561',
 'source-import-capability-headless163-c315-v2-prep-20261121':'ada960adee5a02eeb29b42c0ac82df6ddc43209303b931883db51c059039d6c4',
 'source-import-capability-canonical-c315-prep-20261121':'2bb5e13801a10583d72470bcc58ab87b696248946fdc961c83a5f7e894155643',
 'source-import-capability-canonical-c315-v2-prep-20261121':'0cc2240218def0037cfe0377d22a0c22f772805dc07f967c5144b0d0dce66977',
 'source-contact-rotation-gesture-v2-prep-20261121':'5c8eef061c8e025197899db01292a3d7b5f1a21a6f7c0246e5565c11576a6f51',
 'source-software-evidence-ledger-plan-c315-prep-20261121':'db795ff1c0c61cb214b6caf28edecb4c35cd91175b714f6c720ad31942ab0332',
 'source-software-evidence-ledger-plan-c315-v2-prep-20261121':'efebdb13f6fef23ed05a2bb569c9798c3eb606833bfe4b4ced23847c93190690',
 'source-prepared-map-editor-prep-20261121':'66a091596faa2c4531a2e27c4ba95c6ca7118f62bddaf1fb6753ffe1a44cb804',
 'source-import-info-legacy-tests-v2-prep-20261121':'879849943eda7f6fb036dd126db81020f49dea162a6f41889148b9ecc760187c',
 'source-import-info-full-receipts-prep-20261121':'a460d911b587e17251fa4bade39ec11a3b44f6b5ee47fe2ad31bf9b6fc1c3bdb',
}
SCRIPTS = '''run_import_info_canonical267_scoped_20261121.py run_import_info_path_controls6_20261121.py
run_part_follow_skeleton66_20261121.py prepare_follow66_v2_driver_20261121.py run_part_follow_skeleton66_v2_20261121.py
run_prepared_map64_20261121.py run_c315_final_media_scope_20261121.py run_c315_remaining_scopes_20261121.py
run_contact_rotation_gesture_scoped_20261121.py prepare_contact_rotation_gesture_20261121.py
prepare_contact_rotation_gesture_v2_20261121.py prepare_contact_rotation_gesture_initial_20261121.py
preserve_failed_full_c315_20261121.py record_c315_live_pickup_20261121.py record_c315_terminal_pickup_20261121.py
C315_TERMINAL_FOLLOWUP_PICKUP_20261121.json IMPORT_CAPABILITY_SOURCE_PEER_RECEIPT_20261121.json
run_weight_engine_synthetic13_20261121.py run_part_follow_math21_20261121.py run_easing_gate_files3_20261121.py
run_source1103_synthetic60_20261121.py verify_import_off_full182_root_20261121.py
verify_cleanup_repository_art_20261121.py EASING_CLEANUP_REPOSITORY_ART_BINDING_20261121.json
run_junko_reader15_controls_20261121.py run_junko_reader25_controls_20261121.py record_component_progress_20261121.py'''.split()
STAGES = {
 'map64':PARENT/'has-prepared-map-editor64-1795268002799951700',
 'canonical267-pass':PARENT/'has-import-info-canonical267-v2-1795268189715451800',
 'canonical267-fail0':PARENT/'has-import-info-canonical267-1795267340933340400',
 'headless163-fail0':PARENT/'has-import-info-headless163-1795264650399290900',
 'headless163-pass':PARENT/'has-import-info-headless163-1795265372302394400',
 'contact129':PARENT/'has-contact-rotation-scoped-1795264307051952500',
 'weight13':PARENT/'has-weight-engine-synthetic13-1795263168895144200',
 'follow-math21':PARENT/'has-part-follow-math21-1795262753455184600',
 'follow-parser-fail0':PARENT/'has-part-follow-skeleton66-1795266369537426500',
 'follow66-parse':PARENT/'has-part-follow-skeleton66-v2-parse-1795266897970998700',
 'follow66-pass':PARENT/'has-part-follow-skeleton66-v2-1795266904469046600',
 'source-policy60':ROOT/'output/source1103-synthetic60-1795261109398094500',
 'easing-files3':ROOT/'output/easing-gate-files3-1795262041497312700',
 'path-controls6':ROOT/'output/import-info-path-controls6-1795265354817153200',
}
DENIED={'.has','.glb','.gltf','.png','.jpg','.jpeg','.wav','.mp4','.webm','.bin','.gma','.mdl','.rar','.zip','.vpk','.dll','.exe','.pyc','.pyo','.blend','.kra','.vtf','.vtx','.vvd'}
EXT={'.py','.gd','.md','.json','.txt','.log','.ps1','.cpp','.h','.tscn','.cfg','.bat','.godot','.sh','.svg'}
ARRAY_KEYS={'raw_bones','raw_skin','raw_source_weights','normalized_source_weights','imported_weights','inverse_bind_matrices','vertex_positions','skin_vertices','bone_matrices','joint_indices','source_slot_ids','imported_slot_ids','raw_samples','calibration_failure','influence_failure'}
def digest(data):return hashlib.sha256(data).hexdigest()
def rel(value):
    p=PurePosixPath(value)
    assert value==p.as_posix() and p.parts and not p.is_absolute() and all(x not in ('.','..') and ':' not in x and '\\' not in x and x.rstrip(' .')==x for x in p.parts),value
    return Path(*p.parts)
def stamp(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,getattr(s,'st_file_attributes',0))
def read(path):
    assert path.is_absolute() and path.is_relative_to(PARENT),path
    for p in (path,*path.parents):
        s=p.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400, p
        if p==PARENT:break
    a=path.lstat();assert stat.S_ISREG(a.st_mode) and a.st_nlink==1 and a.st_size<=16*1024*1024,path
    raw=path.read_bytes();assert stamp(a)==stamp(path.lstat()),path
    return raw
def privacy(path,raw):
    assert path.suffix.lower() not in DENIED and (path.suffix.lower() in EXT or path.name in ('LICENSE','COPYING')),path
    # The exact map packet's PRIVATE_INPUT_REFERENCE is scalar external provenance,
    # not the actual input manifest. No arbitrary PRIVATE_* standalone is admitted.
    references={'source-prepared-map-editor-prep-20261121/PRIVATE_INPUT_REFERENCE.json',
                'source-character-pose-follow-prep-20261121/PRIVATE_REFERENCE.json'}
    if path.name.startswith('PRIVATE_'):
        assert any(path==ROOT/'output'/name for name in references) or (path.name=='PRIVATE_REFERENCE.json' and raw==read(ROOT/'output/source-character-pose-follow-prep-20261121/PRIVATE_REFERENCE.json')),path
    text=raw.decode('utf-8-sig');assert '\x00' not in text and ('data:'+'image/') not in text and ('data:application/'+'octet-stream;base64,') not in text,path
    if path.suffix.lower()=='.json':
        def pairs(items):
            out={}
            for key,val in items:assert key not in out,(path,key);out[key]=val
            return out
        value=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        def walk(v):
            if isinstance(v,dict):
                for k,x in v.items():
                    assert k not in ARRAY_KEYS or x in (None,False,[],{}),(path,k)
                    walk(x)
            elif isinstance(v,list):
                assert not(len(v)>512 and all(type(x) in (int,float) for x in v)),path
                for x in v:walk(x)
        walk(value)
def tree_files(folder):
    result=[]
    def error(e):raise e
    for base,dirs,files in os.walk(folder,followlinks=False,onerror=error):
        for d in dirs:
            s=(Path(base)/d).lstat();assert stat.S_ISDIR(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400
        result.extend(Path(base)/name for name in files)
    return result
def prepare():
    assert not ALLOW.exists(),'Version existing allowlist rather than rewriting it'
    rows=[];packets=[];missing=[]
    def add(source,target,kind):
        raw=read(source);privacy(source,raw);rel(target)
        rows.append({'path':target,'source':str(source),'bytes':len(raw),'sha256':digest(raw),'kind':kind})
    for name,pin in PACKETS.items():
        folder=ROOT/'output'/name;raw=read(folder/'SOURCE_PINS.json');assert digest(raw)==pin,name
        data=json.loads(raw);names={'SOURCE_PINS.json'}
        for row in data['files']:
            p=rel(row['path']);assert row['path'] not in names;names.add(row['path'])
            blob=read(folder/p);assert len(blob)==row['bytes'] and digest(blob)==row['sha256'],p
        assert {p.relative_to(folder).as_posix() for p in tree_files(folder)}==names,name
        assert len({p.casefold() for p in names})==len(names)
        for p in sorted(names):add(folder/rel(p),'source/'+name+'/'+p,'frozen-source-or-evidence')
        packets.append({'path':name,'manifest_sha256':pin,'files':len(names)})
    for foldername in ('source-keyframe-easing-c315-graphics-prep-20261121','source-contact-rotation-gesture-prep-20261121'):
        for p in tree_files(ROOT/'output'/foldername):add(p,'authoring-refusals/'+foldername+'/'+p.relative_to(ROOT/'output'/foldername).as_posix(),'unfrozen-authoring-refusal')
    for name in SCRIPTS:
        p=ROOT/'output'/name
        if p.is_file():add(p,'root-code/'+name,'source-driver-or-compact-record')
        else:missing.append(str(p))
    add(ROOT/'docs/benchmarks/components_followup_2026-11-21.json','root-evidence/components_followup_2026-11-21.json','scoped-progress-not-Full')
    for tag,folder in STAGES.items():
        found=False
        for leaf in ('ROOT_RESULT.json','PUBLIC_RESULT.json','RESULT.json'):
            if (folder/leaf).is_file():add(folder/leaf,'root-evidence/'+tag+'/'+leaf,'actual-compact-result');found=True
        if not found:missing.append(str(folder/'{ROOT_RESULT,PUBLIC_RESULT,RESULT}.json'))
    # Native map evidence is restricted to four exact lane log/ownership filenames.
    m=STAGES['map64']
    for mapname in ('gm_construct','ttt_tiny_spaceship_v3'):
        for mode in ('parse','actual'):
            lane=mapname+'-'+mode
            add(m/mapname/(lane+'.engine.log'),'root-evidence/map64/'+lane+'.engine.log','raw-labels-no-map-data')
            for leaf in ('CASE_RESULT.json','OWNERSHIP.json','wrapper-receipt.json','godot-stdout.log','godot-stderr.log','wrapper-stdout.log','wrapper-stderr.log'):
                add(m/lane/'jobs/unit'/leaf,'root-evidence/map64/'+lane+'/'+leaf,'raw-labels-or-ownership')
    old=PARENT/'has-import-off-full-20261121-c31576d'/'output'
    add(old/'remaining-scopes-1795264927106378400/completion.json','root-evidence/remaining29/completion.json','29-scopes-not-Full')
    finals=sorted(old.glob('final-media-scope-*/RESULT.json'));assert len(finals)==1,finals
    add(finals[0],'root-evidence/media21/RESULT.json','21-movies-not-Full')
    add(Path(__file__).resolve(),'code_used/'+Path(__file__).name,'collector-source')
    assert len({r['path'].casefold() for r in rows})==len(rows)
    value={'format':'has_after_c315_explicit_allowlist_1','status':'DRAFT_NOT_FINALIZED_NOT_PUBLISHED','files':rows,'packets':packets,'missing_optional_records':missing,'copied_files_planned':len(rows),'logical_bytes':sum(r['bytes'] for r in rows),'scope_notes':['Failed c315 Full remains failed. Scoped129,29wrappers,21movies,163,66,map64 and actual267 are independent.','All c315 successful-Full-gated native/review/easing hosts remain UNRUN. Native inputs, arrays, art, owner projects, generated fixtures and caches are excluded.','Source freeze-time UNRUN fields are historical and unchanged. Collector performs structural privacy screening plus explicit source review, not general semantic certification.','Pending coordinator/owner53/map-info64 successors and actual results require a new versioned allowlist after closure; this cutoff does not imply completeness.']}
    ALLOW.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    return value
def audit(value,copy_stage=None):
    assert value['format']=='has_after_c315_explicit_allowlist_1'
    names=set();saved=[]
    for row in value['files']:
        key=row['path'];rel(key);assert key.casefold() not in names;names.add(key.casefold())
        p=Path(row['source']);raw=read(p);privacy(p,raw)
        assert len(raw)==row['bytes'] and digest(raw)==row['sha256'],p
        saved.append((row,raw,stamp(p.lstat())))
    if copy_stage:
        dest=Path(copy_stage);assert dest.is_absolute() and dest.parent==ROOT/'output' and dest.name.startswith('after-c315-archive-staging-') and not dest.exists()
        dest.mkdir();(dest/'BUILDING.json').write_text(json.dumps({'publication_ready':False,'started_ns':time.time_ns()})+'\n')
        for row,raw,_ in saved:
            p=dest/rel(row['path']);p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as out:assert out.write(raw)==len(raw)
            assert read(p)==raw,p
        (dest/'PENDING_CONTENTS.json').write_bytes(ALLOW.read_bytes())
    for row,raw,before in saved:
        p=Path(row['source']);assert stamp(p.lstat())==before and read(p)==raw,p
    return {'status':'PASS','files':len(saved),'logical_bytes':sum(len(raw) for _,raw,_ in saved),'source_packet_closures':len(value['packets']),'allowlist_sha256':digest(read(ALLOW)),'copied_to':str(copy_stage) if copy_stage else None,'finalized':False,'runtime_or_GPU_executed':False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepare-allowlist',action='store_true');p.add_argument('--copy-stage',type=Path);o=p.parse_args()
    value=prepare() if o.prepare_allowlist else json.loads(read(ALLOW))
    result=audit(value,o.copy_stage)
    receipt=ROOT/'output'/('AFTER_C315_COLLECTION_AUDIT_'+str(time.time_ns())+'.json');receipt.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({**result,'receipt':str(receipt)},indent=2))
if __name__=='__main__':main()
