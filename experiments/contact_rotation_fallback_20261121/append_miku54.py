"""Append scalar-only actual Miku54 evidence; no source/runtime/engine writes."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT)]
import verify_import_capability as V
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    folder=ROOT/'output/secondary-body-contact/1795309533330650500'
    pins={}
    def read(p):
        raw=V.read(p);pins[p]=(V.identity(p.lstat()),sha(raw));return raw
    raw=read(folder/'verification.json');r=json.loads(raw)
    assert r['status']=='PASS' and type(r['checks']) is int and r['checks']==r['expected_checks']==54
    flags=('all_admitted_sources_unchanged','all_runtime_sources_unchanged','original_inputs_preserved','parent_environment_preserved','all_private_jobs_and_desktops_closed')
    assert all(r[k] is True for k in flags) and r['source_preservation_failures']==[] and r['runtime_source_preservation_failures']==[]
    assert r['graphics_used'] is False and r['source_arrays_published'] is False
    inventory_raw=read(folder/'SOURCE_HASHES.json');inventory=json.loads(inventory_raw)['files']
    assert sha(inventory_raw)==r['source_hash_manifest_sha256'] and len(inventory)==r['source_files']
    skin=read(ROOT/'src/secondary_skin_contact.gd');skin_sha=sha(skin)
    assert skin_sha=='8aac05c4b3bbb132ff104a71bdc448b9b800f29c55496a53d78929384d568f65'
    matches=[x for x in inventory if x['path']=='src/secondary_skin_contact.gd']
    assert matches==[{'path':'src/secondary_skin_contact.gd','bytes':len(skin),'sha256':skin_sha}]
    cases=[]
    assert len(r['cases'])==5 and sum(c['checks'] for c in r['cases'])==54
    for c in r['cases']:
        assert c['status']=='PASS' and type(c['checks']) is int and c['checks']==c['expected_checks']
        assert c['report']['checks']==c['checks'] and c['report']['failures']==0
        assert c['headless'] is True and c['launcher_exit']==0
        assert all(c[k] is True for k in ('launcher_reaped','launcher_handle_closed','private_resources_closed'))
        assert c['private_receipt_mode']=='headless_lifecycle_only' and c['graphical_placement_proven'] is False
        receipt=Path(c['private_receipt']);assert receipt.is_relative_to(folder)
        receipt_raw=read(receipt);assert sha(receipt_raw)==c['private_receipt_sha256']
        proof=json.loads(receipt_raw)
        assert V.private_receipt_closed(proof,c['launcher_exit'],True,c['engine_command'])
        # Numeric/bool report fields only. In particular flow.initial/final,
        # user_profile, commands, paths and every nested pose/array are omitted.
        report={k:v for k,v in c['report'].items() if type(v) in (int,float,bool)}
        stats=c['report'].get('contact_stats')
        if isinstance(stats,dict):report['contact_stats']={k:v for k,v in stats.items() if type(v) in (int,float,bool)}
        cases.append({'name':c['name'],'status':'PASS','checks':c['checks'],'expected_checks':c['expected_checks'],'headless':True,'launcher_exit':0,'launcher_reaped':True,'launcher_handle_closed':True,'private_resources_closed':True,'private_receipt_mode':'headless_lifecycle_only','graphical_placement_proven':False,'receipt_sha256':sha(receipt_raw),'closure':{k:proof[k] for k in ('exit','job_closed','desktop_closed','private_window_seen','child_desktop_confirmed','foreground_child_observed','desktop_switch_requested')},'report':report})
    value={'format':'rotation_fallback_saved_miku54_scalar_projection_1','status':'PASS','checks':54,'expected_checks':54,'scope':r['scope'],'owner_assets_read_by_test':r['owner_assets_read'],'private_assets_copied_to_packet':False,'graphics_used':False,'whole_full_claimed':False,'whole_hair_complete':False,'native_junko_cause_demonstrated':False,'source_files':r['source_files'],'source_hash_manifest_sha256':sha(inventory_raw),'current_skin_sha256':skin_sha,'manifest_skin_row_matches_current_source':True,'original_receipt':{'path':(folder/'verification.json').relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':sha(raw)},**{k:r[k] for k in flags},'cases':cases}
    destination=HERE/'current/miku54.json'
    V.new(destination,(json.dumps(value,indent=2,allow_nan=False)+'\n').encode())
    # Preserve the previous cutoff metadata outside the updated packet.
    backup=ROOT/'output/contact-rotation-evidence-before-miku-20261121';backup.mkdir()
    for name in ('CONTENTS.json','summary.json','README.md','ORIGINS.json'):V.new(backup/name,V.read(HERE/name))
    summary=json.loads(V.read(HERE/'summary.json'))
    summary.update(miku54_included=True,saved_miku_regression_checks=54,saved_miku_regression_source_sha256=skin_sha,saved_miku_test_owner_assets_read=True,packet_private_assets_read_or_copied=False)
    # This field originally described the generated-only cutoff; make its scope
    # explicit now that the separate saved-model regression is included.
    summary.pop('private_assets_read')
    summary['rotation_generated_controls_private_assets_read']=False
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    with (HERE/'README.md').open('a',encoding='utf-8',newline='\n') as stream:stream.write('\n## Completed saved-Miku follow-up\n\nThe earlier cutoff above is retained as history. `current/miku54.json` now records the separate actual54-check saved-Miku regression on the same8aac source. Its five headless cases, physical receipts, source-manifest leaf, source/runtime preservation, original-input preservation and parent-environment preservation were checked. All five launchers were reaped/handles closed and private Jobs/desktops closed. This test read protected owner assets locally; no asset, user profile, request, command, path-rich report, flow pose, geometry or skin array is copied here. It is a separate existing-model regression, not a Junko diagnosis or graphical/full-hair completion.\n')
    origins=json.loads(V.read(HERE/'ORIGINS.json'));origins['files'].append({'archive':'current/miku54.json','root':'PRIMARY','path':(folder/'verification.json').relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':sha(raw),'projection':'Only numeric/bool aggregate and case reports plus physical closure/hash references; flow.initial/final and profiles/commands/paths/arrays omitted'})
    (HERE/'ORIGINS.json').write_text(json.dumps(origins,indent=2)+'\n',encoding='utf-8')
    for p,pin in pins.items():assert (V.identity(p.lstat()),sha(V.read(p)))==pin
    print(json.dumps({'status':'PASS','checks':54,'case_checks':{c['name']:c['checks'] for c in cases},'skin_sha256':skin_sha,'protected_inputs_preserved':True,'all_five_physical_closures_verified':True,'original_bytes_preserved':True}))
if __name__=='__main__':main()
