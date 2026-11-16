"""CPU synthetic full69/subset14 equivalence; no native coordinates or apps."""
from dataclasses import replace
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PYCORE=ROOT/'experiments/source_0x31_chains_20261115/chain_solver.py'
PYCORE_SHA='8d8f061c2c7603d2b1101c78f70588fef0a556b8878795187e95d60b3ae8abec'
TOPOLOGY=ROOT/'experiments/source_native_all49_plan_20261115/PROFILE_TOPOLOGY.json'
TOPOLOGY_SHA='9d2e4fe25ed17866281b60531bf3a4f294392214e83d0449de3ceb35a26b7863'
SELECTED=(8,17,18,26,27)
EXPECTED=(0,1,2,3,4,5,6,7,8,17,18,25,26,27)
EPS=0.00002
PROFILES=((0,.5),(1,1.),(2,2.),(3,1.3),(4,.75),(5,1.75))
TICKS=120


def sha(body):return hashlib.sha256(body).hexdigest()


def load_core():
    assert sha(PYCORE.read_bytes())==PYCORE_SHA
    spec=importlib.util.spec_from_file_location('pinned_projection_full_core',PYCORE)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def main():
    C=load_core();M=C.math0
    assert sha(TOPOLOGY.read_bytes())==TOPOLOGY_SHA
    topology=json.loads(TOPOLOGY.read_bytes())
    parents={row['native_index']:row['parent_native_index'] for row in topology['bone_topology']}
    assert set(parents)==set(range(69))
    closure=set()
    for index in SELECTED:
        seen=set();current=index
        while current>=0:
            assert current not in seen
            seen.add(current);closure.add(current);current=parents[current]
    assert tuple(sorted(closure))==EXPECTED
    descendants=set(SELECTED)
    while True:
        expanded=descendants|{index for index,parent in parents.items() if parent in descendants}
        if expanded==descendants:break
        descendants=expanded
    assert descendants==set(SELECTED)
    checks=0;exact_zero=True;trace=hashlib.sha256()
    def require(condition,label):
        nonlocal checks
        checks+=1
        if not condition:raise AssertionError(label)
    def key(index):return 'synthetic-%02d'%index
    def rz(angle):
        c,s=math.cos(angle),math.sin(angle)
        return ((c,s,0.),(-s,c,0.),(0.,0.,1.))
    def ry(angle):
        c,s=math.cos(angle),math.sin(angle)
        return ((c,0.,-s),(0.,1.,0.),(s,0.,c))
    def frame_tuple(frame):return frame.origin,frame.basis,frame.scale
    rows=[]
    for seed,size in PROFILES:
        # Every coordinate/pose below is a formula-generated synthetic value.
        # Topology/selected IDs alone are retained public native metadata.
        bones={key(i):C.Bone(None if parents[i]<0 else key(parents[i]),C.Frame((.004*math.sin(i*.63+seed),.003*math.cos(i*.37),.018+.002*math.sin(i*.19)),C.mm(rz(.003*i+.01*seed),ry(-.002*i)),1.+.0001*(i%3))) for i in reversed(range(69))}
        subset={id:bone for id,bone in bones.items() if int(id.split('-')[1]) in closure}
        p={key(i):M.Parameters(yaw_stiffness=100. if i==8 else 50.,pitch_stiffness=100. if i==8 else 50.) for i in SELECTED}
        full=C.ChainActor(bones,p);small=C.ChainActor(subset,p)
        full_order=C.parent_order(bones);small_order=C.parent_order(subset)
        require(tuple(id for id in full_order if id in subset)==small_order,'relative parent-first order is unchanged')
        def locals_at(tick):
            return {id:C.Frame((bone.base.origin[0]+.0007*math.sin(.019*tick+i*.13+seed),bone.base.origin[1]+.0004*math.cos(.013*tick+i*.23),bone.base.origin[2]+.0006*math.sin(.017*tick+i*.31)),C.mm(bone.base.basis,C.mm(ry(.05*math.sin(.01*tick+i*.11+seed)),rz(.03*math.cos(.009*tick+i*.17)))),bone.base.scale) for i,(id,bone) in enumerate(bones.items())}
        def prefix_at(tick):return C.Frame((.2*math.sin(.013*tick+seed),.1*math.cos(.011*tick),.15*math.sin(.007*tick)),C.mm(ry(.2*math.sin(.008*tick+seed)),rz(.17*math.cos(.005*tick+seed))),size)
        initial=locals_at(0);prefix=prefix_at(0)
        selected_initial={id:initial[id] for id in subset}
        full.reset(initial,prefix);small.reset(selected_initial,prefix)
        require(full.snapshot()==small.snapshot(),'same five initial states and scales')
        # Static expected scales follow exactly the same parent product order;
        # neither current authored origin nor rotation enters this cache.
        expected_sizes={}
        for id in full_order:
            parent=bones[id].parent
            expected_sizes[id]=(size if parent is None else expected_sizes[parent])*bones[id].base.scale
        for tick in range(1,TICKS+1):
            local=locals_at(tick);prefix=prefix_at(tick);projected={id:local[id] for id in subset}
            forces={key(i):(12.*math.sin(tick*.031+slot*.41+seed),4.*math.cos(tick*.023+slot*.37),9.*math.sin(tick*.017-slot*.23)) for slot,i in enumerate(SELECTED)}
            baseline=full.baseline_worlds(local,prefix)
            for id in full_order:require(baseline[id].scale==expected_sizes[id],'all69 cached exact scalar world scales')
            large=full.step(tick,local,prefix,forces);narrow=small.step(tick,projected,prefix,forces)
            for id in subset:require(large.worlds[id]==narrow.worlds[id],'exact projected world')
            for id in p:
                require(large.goals[id]==narrow.goals[id],'exact selected goal')
                require(large.outputs[id]==narrow.outputs[id],'exact selected solver output/state')
                require(large.delta_bases[id]==narrow.delta_bases[id],'exact selected FK delta')
            require(full.snapshot()==small.snapshot(),'exact five committed states')
            for id in bones:
                if id not in p:require(large.worlds[id]==baseline[id],'all64 unselected synthetic worlds remain authored')
            trace.update(repr(tuple((id,frame_tuple(narrow.worlds[id]),narrow.outputs[id].state) for id in p)).encode())
        rows.append({'synthetic_seed':seed,'prefix_uniform_scale':size,'ticks':TICKS,'selected_rule_evaluations':TICKS*5,'exact_state_and_projection_equal':True})
    # Meaningful topology counterexample: omitting authored nonrule25 changes
    # selected26 even though the four other selected IDs still exist.
    bad=dict(subset);bad.pop(key(25));bad[key(26)]=C.Bone(key(7),bones[key(26)].base)
    bad_actor=C.ChainActor(bad,p);full_ref=C.ChainActor(bones,p)
    initial=locals_at(0);prefix=prefix_at(0)
    full_ref.reset(initial,prefix);bad_actor.reset({id:initial[id] for id in bad},prefix)
    good=full_ref.step(1,locals_at(1),prefix_at(1));wrong=bad_actor.step(1,{id:locals_at(1)[id] for id in bad},prefix_at(1))
    require(good.goals[key(26)].origin!=wrong.goals[key(26)].origin,'dropping authored25 is observably wrong')
    # Explicit refusal-domain counterexample, purely synthetic. All old prefix
    # length/dot checks pass, but old Gram-Schmidt correction exceeds EPS.
    c=math.sqrt(.5);a=.9*EPS
    raw=((c,c,0.),(-c,c,0.),(0.,math.sqrt(2.)*a,1.))
    lengths=tuple(M.length(v) for v in raw);units=tuple(M.multiply(v,1./lengths[i]) for i,v in enumerate(raw))
    shear=max(abs(M.dot(units[i],units[j])) for i,j in ((0,1),(0,2),(1,2)))
    x=units[0];y=M.unit(M.subtract(raw[1],M.multiply(x,M.dot(x,raw[1]))));z=M.cross(x,y)
    correction=max(abs(raw[i][j]/lengths[0]-(x,y,z)[i][j]) for i in range(3) for j in range(3))
    require(max(abs(length-lengths[0]) for length in lengths)<=EPS*lengths[0] and shear<=EPS,'counterexample passes unchanged raw uniform/shear prefix')
    require(correction>EPS,'counterexample fails old GS correction guard')
    result={
        'format':'native_five_projection_synthetic_cpu_1','checks':checks,'failures':0,
        'status':'SYNTHETIC_PYTHON_EXACT_EQUIVALENCE_NOT_GDSCRIPT_OR_RUNTIME_QUALIFICATION',
        'source_sha256':{'python_chain_core':sha(PYCORE.read_bytes()),'pinned_leaf_math':C.REFERENCE_SHA,'public_topology':sha(TOPOLOGY.read_bytes())},
        'selected_native':list(SELECTED),'ancestor_closure_native':list(EXPECTED),'excluded':55,'unselected':64,
        'profiles':rows,'total_ticks':len(PROFILES)*TICKS,'total_selected_rule_evaluations':len(PROFILES)*TICKS*5,
        'comparison':'Exact dataclass/tuple/double equality, no numerical tolerance substituted.',
        'synthetic_trace_sha256':trace.hexdigest(),
        'negative_controls':{'drop_authored25_changes_goal':True,'raw_prefix_accepts_old_correction_refusal':{'shear_dot_max':shear,'old_correction':correction,'EPS_unchanged':EPS}},
        'unqualified':['Actual GDScript variants unparsed/unrun.','No actual Model/native geometry, skin or64world comparison performed here.','Hybrid intentionally omits old full scalar canonical origin/orientation/correction/goal checks for55 unrelated bones.','No measured runtime improvement; existing GUI82/1 remains failed.'],
    }
    (HERE/'CPU_EQUIVALENCE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key!='profiles'},indent=2))


if __name__=='__main__':main()
