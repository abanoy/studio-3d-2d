"""Prepare new source-only review successors; never build/replay or query processes."""
from pathlib import Path
import ast,difflib,hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/replay_audio_fix_20261115'
REV='52f63c944ded7a651da871524d23a345b606424d'
FULL=ROOT/'output/windows-canonical-bone-binding-20261116T041518335'
NATIVE=ROOT/'output/sfm-bone-bindings-native-launch-20261114T033026205/run'
TARGET=ROOT.parent/'HAS-Review-20261115-Native-Hair-52f63c9'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
def write(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(raw)
def replace(code,a,b):
    assert code.count(a)==1,a[:100]
    return code.replace(a,b,1)
def functional(name):return (name.split('/')[0] in ('src','tests','tools','data','examples') or name in ('project.godot','main.tscn','run.py','launch.pyw')) and '__pycache__' not in Path(name).parts and not name.endswith('.pyc')
def main():
    assert sha((OLD/'builder/input-lock.json').read_bytes())=='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
    native=json.loads((NATIVE/'verification.json').read_bytes());before=json.loads((FULL/'source-before.json').read_bytes())
    new=before['source_sha256'];old={n:r for n,r in native['source_before']['files'].items() if functional(n)}
    assert len(new)==1019 and len(old)==1008 and before['commit']==REV
    reasons={
      'src/fan_editor.gd':'Bounded native fan target/aim support; old native assets remain data, prior isolated96/102 controls qualify the new path.',
      'src/physics_editor.gd':'Bounded imported five-rule controls and truthful three-strand user text; reviewed hash-manifest successor.',
      'src/secondary_live.gd':'Explicit native backend branch with generic path retained; exact qualified five-rule wrapper.',
      'tests/helper_preview_port_files.json':'Explicit reviewed physics-editor hash successor; no manifest verification gate removed.',
      'tests/wind_review_port_files.json':'Explicit reviewed physics-editor hash successor; no wind gate removed.',
      'tests/verify_helper_preview.py':'Previously qualified test-only source/EOL provenance followup; current full remains required.',
      'tests/test_owner_review_snapshot.py':'Reviewed27CPU bounded-runtime snapshot tests; owner archive default preserved.',
      'tests/verify_world_selection_teardown.py':'Opt-in bounded runtime snapshot; same28shutdown predicates/timeouts.',
      'tools/build_owner_review_snapshot.py':'Reviewed bounded runtime snapshot option; explicit revision owner archive behavior retained.'}
    added={'src/source_chain_math.gd','src/source_jiggle_math.gd','src/source_secondary.gd',
      'tests/source_native_five_capture.gd','tests/source_native_five_live_ui.gd','tests/source_native_five_state_unit.gd',
      'tests/source_native_live_capture.gd','tests/source_native_live_ui.gd','tests/source_native_state_unit.gd',
      'tests/verify_source_native_five_live.py','tests/verify_source_native_live.py'}
    rows=[];changed=set()
    for name in sorted(new):
        b=(ROOT/name).read_bytes();assert sha(b)==new[name]
        a=(NATIVE/'Studio'/name).read_bytes() if name in old else None
        if a is not None:assert sha(a)==old[name]['sha256']
        if a==b:continue
        changed.add(name)
        assert name in reasons or name in added,name
        rows.append({'path':name,'classification':'added' if a is None else 'modified',
          'old_native_sha256':sha(a) if a is not None else None,'new_working_sha256':sha(b),
          'old_content_sha256':sha(a.replace(b'\r\n',b'\n')) if a is not None else None,
          'new_content_sha256':sha(b.replace(b'\r\n',b'\n')),
          'reason':reasons.get(name,'Qualified bounded native5 mathematics/runtime or its explicit retained state/UI/cold/export test successor; no new conversion inferred.')})
    assert changed==set(reasons)|added and not set(old)-set(new)
    core=['src/model.gd','src/source_bone_bindings.gd','src/scene3d.gd']
    assert all(old[n]['sha256']==new[n] for n in core)
    save(HERE/'source-delta.json',{'format':'has_explicit_native_DATA_to_current_runtime_delta_1',
      'old_native_verification_sha256':'10ee4a984c9e54b1acf37d79d5013a10780abe98416b8350f3edf3ee37277c4b',
      'current_revision':REV,'current_source_before_sha256':sha((FULL/'source-before.json').read_bytes()),
      'old_functional_files':1008,'new_functional_files':1019,'removed':[],
      'unchanged_core':core,'changed_or_added':rows,'new_conversion_performed':False,
      'final_current_four_example_replay':'REQUIRED_NOT_OBSERVED'})
    original_builder=(OLD/'builder/build_after_full.py').read_text();code=original_builder
    code=code.replace('f0dd57a2e568089d396fecba819ab987da658bf0',REV).replace('windows-canonical-bone-binding-20261115T225514304',FULL.name)
    code=replace(code,'OLD_REVIEW = WORKSPACE/"HAS-Review-20261113-12071fe"','OLD_REVIEW = WORKSPACE/"HAS-Review-20261115-SFM-Joints-f0dd57a-replay2"')
    code=replace(code,'"HAS-Review-20261115-SFM-Joints-"+args.revision[:7]+"-replay2"','"HAS-Review-20261115-Native-Hair-"+args.revision[:7]')
    code=code.replace('Preserve the existing12071fe review','Preserve the owner f0dd57a replay2 review').replace('Only the reviewed f0dd57a revision and exact225514304 full run are admitted','Only reviewed52f63c9 and exact041518335 complete full run are admitted')
    code=replace(code,'    need(os.name == "nt" and re.fullmatch("[0-9a-f]{40}", args.revision), "Approved Windows/full commit required")','    need(os.name == "nt" and re.fullmatch("[0-9a-f]{40}", args.revision), "Approved Windows/full commit required")\n    need(not args.no_native_sources,"This exact review requires all four complete native families; no partial source build.")')
    code=replace(code,'TEXT_SUFFIXES =','sys.path.insert(0,str(HERE.parent))\nimport admission as Admission\nTEXT_SUFFIXES =')
    code=replace(code,'    full_gate = canonical_gate(args.canonical_run, args.canonical_host_proof, revision)','    full_gate = canonical_gate(args.canonical_run, args.canonical_host_proof, revision)\n    full_gate.update(Admission.require_full_release(identity))')
    prep='    preparation = {str(HERE/name): identity(HERE/name) for name in ("build_after_full.py", "input-lock.json", "README.template.md")}';code=replace(code,prep,prep+'\n    preparation.update({str(HERE.parent/name):identity(HERE.parent/name) for name in ("admission.py","source-delta.json")})')
    start=code.index('    for name, digest in source_before.items():\n        if name.split(');end=code.index('    scope = ',start)
    code=code[:start]+'    source_delta_admission = Admission.admit_source_delta(native,ROOT,source_before)\n'+code[end:]
    code=code.replace('profile = "HAS SFM Joints Review "','profile = "HAS Native Hair Review "')
    code=replace(code,'"native_Source_solver": "not_implemented", "owner_participation_requested": False','"native_Source_solver": {"implementation":"bounded_five_rule_0x31","solved_rules":5,"retained_rules":49,"strands":3,"copy_only_builder_no_runtime_launch":True,"SDK_artist_or_full49_parity":False}, "source_delta_admission":source_delta_admission, "owner_participation_requested": False')
    write(HERE/'builder/build_after_full.py',code.encode())
    write(HERE/'builder/build_after_full.diff',''.join(difflib.unified_diff(original_builder.splitlines(True),code.splitlines(True),fromfile='unchanged_old_builder',tofile='UNRUN_current_native5_builder')).encode())
    for name in ['input-lock.json']:write(HERE/'builder'/name,(OLD/'builder'/name).read_bytes())
    guide=(OLD/'builder/README.template.md').read_text().replace('# SFM joints review','# Native hair review')
    guide=replace(guide,"Junko's 69 bone identities are verified through the exported model and 49 native jiggle records are retained as inactive metadata. The review can offer existing weighted chains for explicit review. Native Source jiggle simulation is **not implemented**. Applying a reviewed HAS helper is a separate edit with Undo; it does not claim a translation of Source's solver values. Hair & clothes and Physics start off.","Junko retains69 verified bone identities and49 original native records. This runtime supports **three strands / five of49 rules**: FrontHair1(native8),17ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢18 and26ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢27. Select the hair and switch **Hair & clothes** on; a fan's **Aim at hair** can target those joints. Off restores the authored pose; Local Record captures ordinary editable joint motion. The other44rules remain inactive. Body Physics on the same actor, full Source SDK behavior and artist fidelity remain unqualified. Applying a reviewed HAS helper is a separate Undoable edit. Hair & clothes and Physics start off; nothing is enabled by opening an example.")
    guide=guide.replace('The original four packed examples passed native import/adoption','These are unchanged copies of the earlier four packed DATA examples, which passed native import/adoption')
    write(HERE/'builder/README.template.md',guide.encode())
    original=(OLD/'replay/validate_after_full.py').read_text();code=original
    code=replace(code,'BUILDER = HERE.parent/"builder"','BUILDER = HERE.parent/"builder"\nsys.path.insert(0,str(HERE.parent))\nimport admission as Admission')
    code=replace(code,'"HAS-Review-20261115-SFM-Joints-"+args.expected_revision[:7]+"-replay2"','"HAS-Review-20261115-Native-Hair-"+args.expected_revision[:7]')
    prep='    preparation = {str(BUILDER/name): identity(BUILDER/name) for name in ("build_after_full.py", "input-lock.json", "README.template.md")}';code=replace(code,prep,prep+'\n    preparation.update({str(HERE.parent/name):identity(HERE.parent/name) for name in ("admission.py","source-delta.json")})')
    code=replace(code,'    full_gate = built.get("full_run_gate", {})','    current_release_gate = Admission.require_full_release(identity)\n    full_gate = built.get("full_run_gate", {})\n    need(all(full_gate.get(path)==row for path,row in current_release_gate.items()), "Builder current full-release artifacts differ")')
    start=code.index('    admitted_changes = set(release_context["test_only_followup_files"])');end=code.index('    native_cases = ',start)
    code=code[:start]+'    source_delta_admission = Admission.admit_source_delta(native,studio,built["source_hashes"])\n    need(source_delta_admission==built["source_delta_admission"],"Explicit builder/replay source delta admission differs")\n    admitted_changes=set(source_delta_admission["explicit_changed_or_added_files"])\n    production_context=[n for n in native["source_before"]["files"] if Admission.functional(n) and n not in admitted_changes]\n'+code[end:]
    code=replace(code,'    output.mkdir(exist_ok=False); save(output/"shipped-before.json", ship_before)','    output.mkdir(exist_ok=False); save(output/"shipped-before.json", ship_before)\n    save(output/"source-delta-admission.json",source_delta_admission)')
    code=replace(code,'        names += ["native_helper."+name for name in ("available", "native_current", "suggested", "existing_mode", "weights_unchanged", "cancelled", "protected_state", "no_simulation")]','        names += ["native_helper."+name for name in ("available", "native_current", "suggested", "existing_mode", "weights_unchanged", "cancelled", "protected_state", "no_simulation")]\n        names += ["native5.capability","native5.five_anchors","native5.no_autoactivation"]')
    code=replace(code,'        names += ["native5.capability","native5.five_anchors","native5.no_autoactivation"]','        names += ["native5.capability","native5.five_anchors","native5.no_autoactivation"]\n        names += ["native5.relocated_on","native5.relocated_fixed_tick","native5.relocated_off_exact","native5.relocated_protected_state"]')
    code=code.replace('"native_solver": "not_implemented"','"native_solver": "bounded_five_of49_runtime; actual_relocated_on_fixed_tick_off_here; prior266state102UI_qualified_separately"').replace('"test_only_followup_files_admitted": sorted(admitted_changes)','"explicit_native_DATA_current_runtime_changes_admitted": sorted(admitted_changes), "source_delta_admission":source_delta_admission')
    write(HERE/'replay/validate_after_full.py',code.encode())
    write(HERE/'replay/validate_after_full.diff',''.join(difflib.unified_diff(original.splitlines(True),code.splitlines(True),fromfile='unchanged_old_validator',tofile='UNRUN_current_native5_validator')).encode())
    original=(OLD/'replay/replay.gd').read_text();code=original
    code=replace(code,'\tif request.native.get("native_helper_preview",false):\n\t\tawait observer.helper(request.native.object_id,extra_snapshot)','\tif request.native.get("native_helper_preview",false):\n\t\tvar native_motion=load("res://src/source_secondary.gd")\n\t\textra_check(native_motion.offered(actor),"native5.capability")\n\t\textra_check(native_motion.anchors(actor).size()==5,"native5.five_anchors")\n\t\textra_check(not app.physics_editor.is_running() and not app.physics_editor.hair_toggle.button_pressed and not app.physics_editor.toggle.button_pressed and actor.live_pose==null and actor.live_world_transform==null,"native5.no_autoactivation")\n\t\tawait observer.helper(request.native.object_id,extra_snapshot)')
    code=replace(code,'\t\tawait observer.helper(request.native.object_id,extra_snapshot)','\t\tawait observer.helper(request.native.object_id,extra_snapshot)\n\t\tawait relocated_native5(actor)')
    code += "\n"+(HERE/"relocated_native5_fragment.gd").read_text()
    write(HERE/'replay/replay.gd',code.encode())
    write(HERE/'replay/replay.diff',''.join(difflib.unified_diff(original.splitlines(True),code.splitlines(True),fromfile='unchanged_old_observer',tofile='UNRUN_current_native5_observer')).encode())
    for name in ['audio_contract.py','reference-lock.json']:write(HERE/'replay'/name,(OLD/'replay'/name).read_bytes())
    save(HERE/'replay/release-context.json',{'format':'has_native5_review_release_context_1','source_commit':REV,'canonical_run':str(FULL),
      'status_at_preparation':'RUNNING_NOT_ELIGIBLE','required_before_execution':'Actual current completePASS, authoritative close, graphics release and fresh root private lease',
      'native_actual_source_context':'Old four-case native results are trusted DATA; exact20-file admitted runtime/test delta and unchanged Model/Bindings/SceneIO; final current replay required',
      'native_Source_solver':'bounded5of49; three_strands; copy_only_build_no_runtime_launch','proposed_checks':187})
    for role in ('builder','replay'):
        command=json.loads((OLD/role/'command.json').read_bytes())
        command['status']='UNRUN_REQUIRE_ACTUAL_52F_FULL_PASS_CLOSE_RELEASE_AND_FRESH_ROOT_LEASE'
        args=command['command'];args[2]=str(HERE/role/('build_after_full.py' if role=='builder' else 'validate_after_full.py'))
        for i,value in enumerate(args):
            if value=='f0dd57a2e568089d396fecba819ab987da658bf0':args[i]=REV
            elif 'windows-canonical-bone-binding-20261115T225514304' in value:args[i]=value.replace('windows-canonical-bone-binding-20261115T225514304',FULL.name)
            elif value.endswith('HAS-Review-20261115-SFM-Joints-f0dd57a-replay2'):args[i]=str(TARGET)
            elif 'sfm-joints-final-validation-f0dd57a-replay2-20261115' in value:args[i]=str(ROOT/'output/native-hair-final-validation-52f63c9-20261116-attempt1')
        save(HERE/role/'command.json',command)
    for p in HERE.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    save(HERE/'PREPARATION.json',{'format':'has_native5_owner_review_source_preparation_1','source_only':True,'builder_replay_executed':False,'Godot_parser_run':False,'native_conversion_performed':False,'new_review_target':str(TARGET),'protected_owner_review':str(ROOT.parent/'HAS-Review-20261115-SFM-Joints-f0dd57a-replay2'),'input_lock_sha256':'3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6','old_native_verification_sha256':'10ee4a984c9e54b1acf37d79d5013a10780abe98416b8350f3edf3ee37277c4b','old_new_functional_counts':[1008,1019],'explicit_source_deltas':20,'unchanged_core':core,'proposed_checks':187})
    print(json.dumps({'source_prepared':True,'deltas':len(rows),'builder_replay_executed':False,'GDScript_unparsed_unrun':True}))
if __name__=='__main__':main()
