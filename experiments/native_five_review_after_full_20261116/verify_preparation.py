"""Read-only source preparation audit; never build, replay or query processes."""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/replay_audio_fix_20261115'
checks=[]
def check(ok,label):
    if not ok:raise AssertionError(label)
    checks.append(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def py_functions(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def gd_functions(path):
    text=path.read_text(encoding='utf-8');parts=re.split(r'(?m)^(?=func )',text)
    def executable(p):return '\n'.join(s for s in p.splitlines() if s.strip() and not s.lstrip().startswith('#'))
    return {re.match(r'func (\w+)',p).group(1):executable(p) for p in parts if p.startswith('func ')}
def main():
    source=load(HERE/'SOURCE_AUDIT.json')
    for path in HERE.rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'));check(True,'Python AST '+path.relative_to(HERE).as_posix())
    for kind,path in [('builder','builder/build_after_full.py'),('replay','replay/validate_after_full.py')]:
        before=py_functions(OLD/path);after=py_functions(HERE/path)
        check(set(before)==set(after),kind+' function inventory retained')
        for name in source['unchanged_functions'][kind]:check(before[name]==after[name],kind+' unchanged '+name)
        actual=sorted(n for n in before if before[n]!=after[n])
        check(actual==sorted(source['changed_functions'][kind]),kind+' only declared function changes')
    before=gd_functions(OLD/'replay/replay.gd');after=gd_functions(HERE/'replay/replay.gd')
    for name in source['unchanged_functions']['GDScript']:check(before[name]==after[name],'GDScript unchanged '+name)
    check(set(after)-set(before)=={'relocated_native5'},'Only new GDScript lifecycle observer')
    check(sorted(n for n in before if before[n]!=after[n])==source['changed_functions']['GDScript'],'Only final_extras modified among old GDScript functions')
    fragment=gd_functions(HERE/'relocated_native5_fragment.gd')['relocated_native5']
    check(after['relocated_native5']==fragment,'Relocated observer exact standalone fragment')
    observer=after['relocated_native5']
    check('editor.hair_toggle.button_pressed=true' in observer and 'editor.hair_toggle.button_pressed=false' in observer,'Ordinary connected checkbox On and Off')
    check('await get_tree().process_frame' in observer and 'runner._tick<1' in observer,'Observe real physics progress')
    check(not re.search(r'(?m)^\s*[^#\n]*(?:\.advance|\.step)\s*\(',observer),'No direct solver advance or step')
    check('var_to_bytes([actor.root.global_transform,bones_after])==world_before' in observer and 'actor.data==authored_before' in observer,'Exact world69/root and authored restoration')
    check('extra_snapshot()==protected_before' in observer and 'FileAccess.get_sha256(actor.data.source)==source_before' in observer,'Protected scene/history and source bytes bound')
    check('common/physics_ticks_per_second=120' in (ROOT/'project.godot').read_text(),'Production fixed clock120Hz')
    native=load(ROOT/'output/sfm-bone-bindings-native-launch-20261114T033026205/run/verification.json')
    admission=module(HERE/'admission.py','native5_review_preparation_admission')
    current=load(admission.FULL/'source-before.json')['source_sha256']
    proof=admission.admit_source_delta(native,ROOT,current)
    check(proof['old_native_functional_files']==1008 and proof['current_functional_files']==1019 and len(proof['explicit_changed_or_added_files'])==20,'Read-only exact DATA/current source admission')
    for role,oid in [('builder/input-lock.json','3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'),('replay/audio_contract.py','4e4351d82293fd6156712c1c81bd532c35cd7a13e0a091f3dca26628a1d0ec93'),('replay/reference-lock.json','e5dbbbd1cc21d143fc9c6d56996b6aec97b1b0f9167f334c274a77d246ab9413')]:
        check(sha(HERE/role)==oid,'Exact retained '+role)
    old_path=list(sys.path);sys.path.insert(0,str(OLD/'replay'))
    try:
        old=module(OLD/'replay/validate_after_full.py','native5_old_replay_names')
        new=module(HERE/'replay/validate_after_full.py','native5_new_replay_names')
        total_added=0
        for row in native['writer']['result']['cases']:
            details=load(Path(row['expected']))
            a=old.extra_names(details);b=new.extra_names(details)
            check(set(a)<=set(b) and len(b)==len(set(b)),row['name']+' all prior unique predicates retained')
            added=len(b)-len(a);check(added==(7 if details.get('native_helper_preview') else 0),row['name']+' declared conditional7-gate addition')
            total_added+=added
        check(total_added==7 and source['old_predicates_retained']==180 and source['proposed_total']==187,'Aggregate proposed187; runtime unrun')
    finally:sys.path[:]=old_path
    return {'format':'has_native5_owner_review_preparation_audit_2','passed':True,'checks':len(checks),'labels':checks,
        'read_only_admission':proof,'GDScript_parser_or_runtime_run':False,'review_build_or_replay_run':False,
        'CIM_Git_network_or_process_queries':False,'product_checks_executed':0,'proposed_final_replay_checks':187}
if __name__=='__main__':print(json.dumps(main(),indent=2))
