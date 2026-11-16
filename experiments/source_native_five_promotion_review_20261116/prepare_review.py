"""CPU/source-only bounded promotion packet builder; never applies or launches."""
from pathlib import Path
import ast
import copy
import difflib
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STAGE = ROOT / 'output/native-five-stage-attempt3/Studio'
PINS = {
    'src/source_secondary.gd': '3b2c29dc11b60e68306f858a32d03271e30a039b8451916df2ff9324e7da4f84',
    'src/source_chain_math.gd': '31491fbde49b635edadda5e661fa3eecabf0f7e3598f0dc448c0d944ffa6f844',
    'src/secondary_live.gd': '2613b19ce53b3a50fd001fe4e5b39bca2814165148b036993549490aa96c33a9',
    'tests/source_native_five_state_unit.gd': 'ab40f406e7b2ececc719761f0f0246ecb347bf853d711c3901671c8b8d6d7174',
    'tests/source_native_five_capture.gd': 'b1dc120815f9e56b79ca4406dd3a04ddd5b0978510c6e5ca8234b11ae88ff58b',
    'tests/source_native_five_live_ui.gd': 'bea7c6b9d512583f05fe88f63f3113c34e3bc9dbf05ac31ce0961402ed704a12',
    'tests/verify_source_native_five_live.py': '543da7be754ef8e748215ff6e39eaa897de458c3ea1eeeb8b51bf1c375bfc96e',
}
PHYSICS_SHA = 'e351c0f5e2be18c33793a0ae6234b049095c923b35ca8ec1c6c7aaeb36bb8b6a'
REPLACEMENTS = {
    'src/source_secondary.gd': [(b'# source report. SOURCE-ONLY strict2 capture deduplication; UNPARSED/UNRUN.',
        b'# source report. Qualified bounded five-joint backend; capture checks deduplicated.')],
    'src/source_chain_math.gd': [(b'# SOURCE ONLY, UNPARSED/UNRUN. Parent-first HAS policy, not SDK client parity.\n# Stage the unchanged qualified scalar solver as res://leaf_candidate.gd.',
        b'# Qualified parent-first HAS policy for the admitted five-joint subset.\n# Uses the unchanged qualified scalar solver; SDK client parity is not claimed.')],
}
PHYSICS_REPLACEMENTS = [
    (b'Use imported settings for the front-hair strand. This first supported subset moves1of49 imported joints. Other loose parts can use Set up loose parts. Body Physics must be off. Off restores the authored pose; Record keeps motion.',
     b'Use imported settings for three supported hair strands. Other loose parts can use Set up loose parts. Body Physics must be off. Off restores the authored pose; Record keeps motion.'),
    (b'Imported front-hair motion on (1of49 imported joints). Move a fan or choose Aim at hair; Record keeps the motion. Other loose parts can use Set up loose parts.',
     b'Imported motion on for three supported hair strands. Move a fan or choose Aim at hair; Record keeps the motion. Other loose parts can use Set up loose parts.'),
]
MANIFESTS = ['tests/helper_preview_port_files.json', 'tests/wind_review_port_files.json']
LEGACY = ['tests/source_native_state_unit.gd', 'tests/source_native_live_ui.gd',
          'tests/source_native_live_capture.gd', 'tests/verify_source_native_live.py',
          'experiments/native_source_live_port_20261115/run_state_owned.py']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def identity(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)}

def write(name, raw):
    p = HERE / name
    assert not p.exists(), p
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(raw)

def doc(name, value):
    write(name, (json.dumps(value, indent=2, allow_nan=False) + '\n').encode())

def gd_without_full_line_comments(raw):
    # This exact recipe is used only where the changed lines are full comments.
    return b'\n'.join(line for line in raw.split(b'\n') if not line.lstrip().startswith(b'#'))

def exact_replace(raw, replacements):
    for old, new in replacements:
        assert raw.count(old) == 1, old
        raw = raw.replace(old, new, 1)
    return raw

def source_ref(name):
    return identity(ROOT / name)

def virtual_row_ok(row, data):
    return sha(data) == row['sha256'] or sha(data.replace(b'\r\n', b'\n')) == row['lf_sha256']

def main():
    assert ROOT.name == 'has-acceptance-session-20261111'
    source_before = {name: source_ref(name) if (ROOT/name).is_file() else None for name in [*PINS, 'src/physics_editor.gd', *MANIFESTS]}
    promotions, recipes, staged_refs = [], [], []
    for name, pin in PINS.items():
        raw = (STAGE/name).read_bytes()
        assert sha(raw) == pin, name
        staged_refs.append(identity(STAGE/name))
        write('qualified-stage/'+name, raw)
        proposed = exact_replace(raw, REPLACEMENTS.get(name, []))
        if name in REPLACEMENTS:
            assert gd_without_full_line_comments(proposed) == gd_without_full_line_comments(raw)
            recipes.append({'path': name, 'recipe': 'Exact recorded full-line-comment replacements only',
                            'qualified_sha256': pin, 'proposed_sha256': sha(proposed),
                            'non_full_line_comment_bytes_identical': True,
                            'replacements': [{'before': a.decode(), 'after': b.decode()} for a,b in REPLACEMENTS[name]]})
        write('proposed/'+name, proposed)
        promotions.append({'path': name, 'qualified_stage_sha256': pin, 'proposed_sha256': sha(proposed),
                           'bytes': len(proposed), 'runtime_equivalent_comment_only': name in REPLACEMENTS,
                           'exact_qualified_bytes': proposed == raw})
    raw = (ROOT/'src/physics_editor.gd').read_bytes()
    assert sha(raw) == PHYSICS_SHA
    write('before/src/physics_editor.gd', raw)
    proposed = exact_replace(raw, PHYSICS_REPLACEMENTS)
    # Reversing only the two recorded string replacements must restore every byte.
    assert exact_replace(proposed, [(b,a) for a,b in PHYSICS_REPLACEMENTS]) == raw
    assert proposed.count(b'1of49') == 0
    write('proposed/src/physics_editor.gd', proposed)
    physics_new_sha = sha(proposed)
    promotions.append({'path':'src/physics_editor.gd','before_sha256':PHYSICS_SHA,'proposed_sha256':physics_new_sha,
                       'bytes':len(proposed),'recipe':'Exactly two user-facing string literal replacements',
                       'reverse_recipe_restores_every_byte':True})
    recipes.append({'path':'src/physics_editor.gd', 'replacements':[{'before':a.decode(),'after':b.decode()} for a,b in PHYSICS_REPLACEMENTS]})
    manifest_proofs = []
    for name in MANIFESTS:
        raw = (ROOT/name).read_bytes()
        old = json.loads(raw)
        assert raw.count(PHYSICS_SHA.encode()) == 2, name
        after = raw.replace(PHYSICS_SHA.encode(), physics_new_sha.encode())
        new = json.loads(after)
        row_old = [row for row in old['files'] if row['path'] == 'src/physics_editor.gd']
        row_new = [row for row in new['files'] if row['path'] == 'src/physics_editor.gd']
        assert len(row_old) == len(row_new) == 1
        expected = copy.deepcopy(old)
        target = [row for row in expected['files'] if row['path'] == 'src/physics_editor.gd'][0]
        target.update(sha256=physics_new_sha, lf_sha256=physics_new_sha)
        assert expected == new
        assert after.replace(physics_new_sha.encode(),PHYSICS_SHA.encode()) == raw
        assert len(old['files']) == (25 if 'helper' in name else 16)
        matches=[]
        for row in new['files']:
            data = proposed if row['path'] == 'src/physics_editor.gd' else (ROOT/row['path']).read_bytes()
            assert virtual_row_ok(row, data), row['path']
            matches.append({'path':row['path'], 'exact':sha(data)==row['sha256'],
                            'actual_sha256':sha(data),'lf_sha256':sha(data.replace(b'\r\n',b'\n'))})
        assert not virtual_row_ok(row_new[0], raw), 'Old UI bytes must be refused by successor'
        assert not virtual_row_ok(row_old[0], proposed), 'Old manifest must refuse successor UI bytes'
        assert not virtual_row_ok(row_new[0], proposed+b'# corrupt\n'), 'Unreviewed bytes must refuse'
        write('before/'+name, raw)
        write('proposed/'+name, after)
        promotions.append({'path':name,'before_sha256':sha(raw),'proposed_sha256':sha(after),'bytes':len(after),
                           'recipe':'Replace exactly two occurrences of physics_editor SHA; no other byte changes'})
        manifest_proofs.append({'path':name,'row_count':len(new['files']),'before_sha256':sha(raw),
            'proposed_sha256':sha(after),'only_changed_row':'src/physics_editor.gd',
            'all_other_rows_metadata_pathsets_and_bytes_preserved':True,'reviewed_rows':matches,
            'negative_controls':{'successor_rejects_old_ui':True,'old_rejects_successor_ui':True,'successor_rejects_corrupt_ui':True}})
    # Inspect only verification code and metadata; no fixture/model inputs.
    verifiers = [source_ref(n) for n in ['tests/verify.py','tests/native_fixture_plans.py',
                   'tests/verify_helper_preview.py','tests/verify_wind_review.py','tests/test_helper_preview_driver.py']]
    legacy_refs = [source_ref(name) for name in LEGACY]
    verify_raw = (ROOT/'tests/verify.py').read_text(encoding='utf-8')
    assert not any(Path(name).name in verify_raw for name in LEGACY)
    assert 'source_native_five' not in verify_raw and 'verify_source_native_live' not in verify_raw
    for file in ['tests/verify_helper_preview.py','tests/verify_wind_review.py','tests/verify.py']:
        ast.parse((ROOT/file).read_text(encoding='utf-8'))
    for file in ['tests/verify_source_native_five_live.py']:
        ast.parse((HERE/'proposed'/file).read_text(encoding='utf-8'))
    stage_gui=STAGE/'output/native-five-gui-attempt1/verification.json'
    stage_state=STAGE/'output/source-native-five-state-20261116T040011702334/verification.json'
    gui=json.loads(stage_gui.read_bytes());state=json.loads(stage_state.read_bytes())
    assert gui['passed'] and gui['checks_observed']==102 and gui['phase_expected']=={'writer':83,'reader-packed':11,'reader-linked':8}
    assert state['passed'] and state['checks_observed']==266 and state['failures_observed']==0
    assert all(gui['preservation'].values()) and all(state['preservation'].values())
    proofs={'format':'has_native_five_promotion_source_review_1','status':'UNAPPLIED_SOURCE_REVIEW_ONLY',
        'qualified_stage_root':STAGE.relative_to(ROOT).as_posix(),'selected_native_ids':[8,17,18,26,27],
        'selected_rule_count':5,'retained_native_rules':49,'hair_strand_count':3,
        'actual_qualification_references':[identity(stage_state),identity(stage_gui)],
        'qualified_stage_sources':staged_refs,'promotion_files':promotions,'exact_edit_recipes':recipes,
        'manifest_successors':manifest_proofs,'unchanged_verifier_sources':verifiers,
        'legacy_one_rule_sources':legacy_refs,'legacy_absent_from_default_verify_entrypoint':True,
        'default_verify_registration_unchanged':True,
        'driver_legacy_field':'native8_editor_backend_tested remains byte-identical to actual102 qualification; it is a historical label, not the selected-rule inventory. Actual five result has native_rules_solved=5 and selected indices are listed here.',
        'scope_limit':'Only this exact admitted profile and five rules. All49/full SDK client/body coupling are unqualified. Same-actor reverse body case remains UNQUALIFIED_PARTIAL_SOURCE_RIG.',
        'source_before':source_before,'main_files_modified':False,'engines_or_CIM_or_Git_or_network_run':False}
    for name, before in source_before.items():
        assert (source_ref(name) if (ROOT/name).is_file() else None) == before, name
    doc('REVIEW.json',proofs)
    patches=[]
    for row in promotions:
        name=row['path']; before=(STAGE/name).read_bytes() if name in PINS else (ROOT/name).read_bytes()
        after=(HERE/'proposed'/name).read_bytes()
        patches.extend(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),
                      fromfile='qualified-stage/'+name if name in PINS else 'main-before/'+name,tofile='proposed/'+name))
    write('promotion.patch',''.join(patches).encode())
    doc('CPU_PREFLIGHT.json',{'passed':True,'manifest_reviewed_rows':41,'manifest_negative_controls':6,
        'comment_only_sources':2,'exact_ui_string_replacements':2,'promoted_test_runtime_bytes_unchanged':True,
        'default_verify_registration_changed':False,'main_functional_files_unchanged':True,
        'runtime_tests_run_by_packet_builder':0})
    print(json.dumps({'prepared':True,'files_to_promote':len(promotions),'physics_editor_new_sha256':physics_new_sha,
                      'source_secondary_new_sha256':promotions[0]['proposed_sha256']}))

if __name__ == '__main__':
    main()
