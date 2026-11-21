"""Additive collector authoring; does not run collection, engines or Git."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
src=R/'output/collect_after_c315_continuation_v2_20261121.py';raw=src.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='084a92851c3315cb9557b7cb60450fc845256a9664afb89c1b0b588c57e0b38f'
text=raw.decode().replace('\r\n','\n').replace('AFTER_C315_COLLECTION_ALLOWLIST_DRAFT_V2_20261121','AFTER_C315_COLLECTION_ALLOWLIST_DRAFT_V3_20261121')
anchor='DENIED={'
assert text.count(anchor)==1
text=text.replace(anchor,"""SCRIPTS.extend('''prepare_import_info_canonical267_v2_driver_20261121.py run_import_info_canonical267_v2_scoped_20261121.py
prepare_import_info_metadata_driver_20261121.py prepare_import_info_metadata_v2_driver_20261121.py prepare_import_info_metadata_v3_driver_20261121.py
run_import_info_metadata163_20261121.py run_import_info_metadata163_v2_20261121.py run_import_info_metadata163_v3_20261121.py
prepare_import_info_legacy_v3_driver_20261121.py run_import_info_legacy_scopes_20261121.py run_import_info_legacy_v3_scopes_20261121.py
prepare_map_info64_driver_20261121.py run_prepared_map_info64_20261121.py
prepare_import_info_legacy_v4_driver_20261121.py run_import_info_legacy_v4_scopes_20261121.py IMPORT_LEGACY_V3_ROOT_POSTCHECK_FAILURE_20261121.json
IMPORT_METADATA_INITIAL_PREFLIGHT_REFUSAL_20261121.json IMPORT_METADATA_SECOND_STARTUP_REFUSAL_20261121.json
adopt_import_info_increment_20261121.py'''.split())
DENIED={""")
anchor="    add(Path(__file__).resolve(),'code_used/'+Path(__file__).name,'collector-source')\n"
assert text.count(anchor)==1
text=text.replace(anchor,"""    # Additional closed component proofs: no fixture/project/cache/model files.
    passed=STAGES['canonical267-pass'];comp=passed/'Studio/output/component267'
    report_raw=read(comp/'verification.json')
    assert digest(report_raw)=='d02f87482ff1d5adcf2cdb0442ed56898158068ebf9a5cd5e3002a45e6d92129'
    report=json.loads(report_raw);assert report['status']=='PASS' and report['checks']==267 and len(report['cases'])==21
    add(comp/'verification.json','root-evidence/canonical267-pass/verification.json','actual-component-report')
    expected={'legacy43'}|{'app-'+a+'-'+b for a in ('classic','neon') for b in ('simple','advanced')}
    expected|={role+'-'+theme+'-'+str(scale)+'-'+mode for role in ('writer','reader') for theme in ('classic','neon') for scale in (100,150) for mode in ('simple','advanced')}
    assert {row['name'] for row in report['cases']}==expected
    for case in sorted(expected):
        for leaf in ('stdout.log','stderr.log','engine.log'):
            add(comp/'Cases'/case/leaf,'root-evidence/canonical267-pass/Cases/'+case+'/'+leaf,'actual-synthetic-labels-and-receipts')
        row=next(r for r in report['cases'] if r['name']==case);receipt=Path(row['private_receipt'])
        assert receipt.is_relative_to(comp)
        proof=json.loads(read(receipt));assert proof.get('format')=='studio_private_desktop_1' and proof.get('job_closed') is True and proof.get('desktop_closed') is True and type(proof.get('exit')) is int and proof['exit']==0
        add(receipt,'root-evidence/canonical267-pass/Cases/'+case+'/private-receipt.json','actual-owned-physical-receipt')
    for leaf in ('stdout.log','stderr.log','launch.json'):
        add(passed/leaf,'root-evidence/canonical267-pass/'+leaf,'actual-component-launch-or-log')
    maps=PARENT/'has-prepared-map-editor-info64-1795268686541791900'
    add(maps/'ROOT_RESULT.json','root-evidence/map-info64/ROOT_RESULT.json','actual-import-info-map64')
    for mapname in ('gm_construct','ttt_tiny_spaceship_v3'):
        for mode in ('parse','actual'):
            lane=mapname+'-'+mode
            add(maps/mapname/(lane+'.engine.log'),'root-evidence/map-info64/'+lane+'.engine.log','raw-labels-no-map-data')
            for leaf in ('CASE_RESULT.json','OWNERSHIP.json','wrapper-receipt.json','godot-stdout.log','godot-stderr.log','wrapper-stdout.log','wrapper-stderr.log'):
                add(maps/lane/'jobs/unit'/leaf,'root-evidence/map-info64/'+lane+'/'+leaf,'raw-labels-or-ownership')
    policy=PARENT/'has-import-info-metadata163-v3-1795269001576627300'
    closed=json.loads(read(policy/'ROOT_RESULT.json'));assert closed['status']=='PASS' and closed['reaped'] is True and closed['actual_headless_receipts_independently_admitted']==5
    for leaf in ('ROOT_RESULT.json','POLICY47_RESULT.json','policy-stdout.log','policy-stderr.log','stdout.log','stderr.log','launch.json'):
        add(policy/leaf,'root-evidence/metadata47-cpu163/'+leaf,'actual-policy-and-metadata-component')
    old_legacy=PARENT/'has-import-info-legacy-scopes-1795268756730492500'
    for leaf in ('ROOT_RESULT.json','mmd-stderr.log','mmd-stdout.log','owner.engine.log'):
        add(old_legacy/leaf,'root-evidence/legacy53-native-viewport-failure/'+leaf,'owner53-PASS-native-wrapper-FAIL')
    for leaf in ('CASE_RESULT.json','OWNERSHIP.json','wrapper-receipt.json','godot-stdout.log','godot-stderr.log','wrapper-stdout.log','wrapper-stderr.log'):
        add(old_legacy/'jobs/unit'/leaf,'root-evidence/legacy53-native-viewport-failure/owner/'+leaf,'owner53-raw-labels-and-closure')
    legacy_v3=PARENT/'has-import-info-legacy-v3-scopes-1795269018717888300'
    for leaf in ('ROOT_RESULT.json','mmd-stderr.log','mmd-stdout.log'):
        add(legacy_v3/leaf,'root-evidence/legacy-v3-postcheck-failure/'+leaf,'Root-postcheck-FAIL-native-wrapper-PASS')
    legacy_v4=PARENT/'has-import-info-legacy-v4-scopes-1795269105700452700'
    for leaf in ('ROOT_RESULT.json','mmd-stderr.log','mmd-stdout.log','owner.engine.log'):
        add(legacy_v4/leaf,'root-evidence/legacy-v4-owner53-native-wrapper-pass/'+leaf,'actual-owner53-and-native-wrapper-PASS')
    for leaf in ('CASE_RESULT.json','OWNERSHIP.json','wrapper-receipt.json','godot-stdout.log','godot-stderr.log','wrapper-stdout.log','wrapper-stderr.log'):
        add(legacy_v4/'jobs/unit'/leaf,'root-evidence/legacy-v4-owner53-native-wrapper-pass/owner/'+leaf,'owner53-raw-labels-and-closure')
    plan_folder=ROOT/'output/source-import-info-adoption-plan-prep-20261121'
    assert digest(read(ROOT/'output/adopt_import_info_increment_20261121.py'))=='c5091e098051b6169e9740b7af13c061a4ef6a4af2bec2fbb2351a86c45b5285'
    assert digest(read(plan_folder/'READY_ADOPTION_PLAN.json'))=='40a218e075be3a297fd359cb60258d65ae1f0b6e19ce1e5faf889f53505fd03c'
    for leaf in ('DRAFT_ADOPTION_PLAN.json','READY_ADOPTION_PLAN.json'):
        add(plan_folder/leaf,'source/source-import-info-adoption-plan-prep-20261121/'+leaf,'pinned-plan-source-not-adoption-result')
    meta_reports=list((policy/'Studio/output/import-capability-canonical').glob('*/verification.json'))
    assert len(meta_reports)==1 and digest(read(meta_reports[0]))=='6029b46eec043636d10360ce70f866aee7ed684efc74228cd81d4fa6f879316b'
    add(meta_reports[0],'root-evidence/metadata47-cpu163/verification.json','actual-physical-cpu163-report')
    cpu_names={'legacy43'}|{'app-'+a+'-'+b for a in ('classic','neon') for b in ('simple','advanced')}
    for case in sorted(cpu_names):
        for leaf in ('stdout.log','stderr.log','engine.log','private-receipt.json'):
            add(meta_reports[0].parent/'Cases'/case/leaf,'root-evidence/metadata47-cpu163/Cases/'+case+'/'+leaf,'actual-cpu-labels-and-receipts')
    # Root adds exact closed paths/pins through a versioned successor if ready.
    add(Path(__file__).resolve(),'code_used/'+Path(__file__).name,'collector-source')
    for leaf in ('collect_after_c315_continuation_20261121.py','collect_after_c315_continuation_v2_20261121.py','prepare_after_c315_collector_v2_20261121.py','prepare_after_c315_collector_v3_20261121.py','prepare_after_c315_collector_v3_initial_20261121.py'):
        add(ROOT/'output'/leaf,'code_used/'+leaf,'historical-source-collector')
""")
dst=R/'output/collect_after_c315_continuation_v3_20261121.py';assert not dst.exists()
dst.write_text(text,encoding='utf-8');print(dst)
