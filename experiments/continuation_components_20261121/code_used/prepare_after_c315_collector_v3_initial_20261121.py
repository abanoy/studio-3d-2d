"""Additive collector authoring; does not run collection, engines or Git."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
src=R/'output/collect_after_c315_continuation_v2_20261121.py';raw=src.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='084a92851c3315cb9557b7cb60450fc845256a9664afb89c1b0b588c57e0b38f'
text=raw.decode().replace('AFTER_C315_COLLECTION_ALLOWLIST_DRAFT_V2_20261121','AFTER_C315_COLLECTION_ALLOWLIST_DRAFT_V3_20261121')
anchor='DENIED={'
assert text.count(anchor)==1
text=text.replace(anchor,"""SCRIPTS.extend('''prepare_import_info_canonical267_v2_driver_20261121.py run_import_info_canonical267_v2_scoped_20261121.py
prepare_import_info_metadata_driver_20261121.py prepare_import_info_metadata_v2_driver_20261121.py prepare_import_info_metadata_v3_driver_20261121.py
run_import_info_metadata163_20261121.py run_import_info_metadata163_v2_20261121.py run_import_info_metadata163_v3_20261121.py
prepare_import_info_legacy_v3_driver_20261121.py run_import_info_legacy_scopes_20261121.py run_import_info_legacy_v3_scopes_20261121.py
prepare_map_info64_driver_20261121.py run_prepared_map_info64_20261121.py
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
        for leaf in ('stdout.log','stderr.log','engine.log','private-receipt.json'):
            add(comp/'Cases'/case/leaf,'root-evidence/canonical267-pass/Cases/'+case+'/'+leaf,'actual-synthetic-labels-and-receipts')
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
    # Legacy v3 and final adoption plan are deliberately not guessed here.
    # Root adds exact closed paths/pins through a versioned successor if ready.
    add(Path(__file__).resolve(),'code_used/'+Path(__file__).name,'collector-source')
    for leaf in ('collect_after_c315_continuation_20261121.py','collect_after_c315_continuation_v2_20261121.py','prepare_after_c315_collector_v2_20261121.py','prepare_after_c315_collector_v3_20261121.py'):
        add(ROOT/'output'/leaf,'code_used/'+leaf,'historical-source-collector')
""")
dst=R/'output/collect_after_c315_continuation_v3_20261121.py';assert not dst.exists()
dst.write_text(text,encoding='utf-8');print(dst)
