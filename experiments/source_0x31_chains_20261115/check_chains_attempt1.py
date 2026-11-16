"""CPU checks with synthetic-only frames; no parser/engine/native arrays."""
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from chain_solver import Bone, ChainActor, Frame, math0 as M, mm, mv, transpose, parent_order

checks = 0
max_error = 0.


def check(ok, label):
    global checks
    checks += 1
    if not ok: raise AssertionError(label)


def close(actual, expected, label, eps=1e-11):
    global max_error
    if isinstance(actual, Frame): actual = (*actual.origin, *sum(actual.basis, ()), actual.scale)
    if isinstance(expected, Frame): expected = (*expected.origin, *sum(expected.basis, ()), expected.scale)
    error = max(abs(a-b) for a,b in zip(actual,expected))
    max_error = max(max_error,error)
    check(error <= eps, label)


def refused(fn, label):
    try: fn()
    except (ValueError, TypeError, OverflowError): check(True,label); return
    check(False,label)


def ry(t):
    c,s = math.cos(t),math.sin(t)
    return ((c,0.,-s),(0.,1.,0.),(s,0.,c))


def rz(t):
    c,s = math.cos(t),math.sin(t)
    return ((c,s,0.),(-s,c,0.),(0.,0.,1.))


def flat(columns): return tuple(x for column in columns for x in column)


def first_tick_closed_form():
    # Analytic two-link fixture: L2, child origin2Z, no mass, parent force3X.
    # a=3/120²=1/4800 is exact rational before the length normalization.
    # Parent f=(a,0,2)/sqrt(a²+4); child goal base=2f,target=4f.
    # child lateral acceleration=50*left·(4f-4Z)=200*f.x*left.
    p = M.Parameters(length=2.,tip_mass=0.)
    bones = {"child":Bone("parent"),"parent":Bone(None)}
    local = {"child":Frame((0.,0.,2.)),"parent":Frame()}
    actor = ChainActor(bones,dict.fromkeys(bones,p),source_scale=1.)
    actor.reset(local)
    result = actor.step(1,local,world_accelerations={"parent":(3.,0.,0.)})
    a = float(Fraction(3,120*120))
    denominator = math.sqrt(a*a+4)
    fx,fz = a/denominator,2/denominator
    parent_direction = (fx,0.,fz)
    left = (fz,0.,-fx)
    acceleration = (200*fx*fz,0.,-200*fx*fx)
    child_unconstrained = (acceleration[0]/14400,0.,4+acceleration[2]/14400)
    base = (2*fx,0.,2*fz)
    separation = tuple(child_unconstrained[i]-base[i] for i in range(3))
    size = math.sqrt(sum(x*x for x in separation))
    child_tip = tuple(base[i]+2*separation[i]/size for i in range(3))
    close(result.outputs["parent"].state.tip,tuple(2*x for x in parent_direction),"rational parent first impulse")
    close(result.goals["child"].origin,base,"same-tick parent moves child origin")
    close(result.outputs["child"].acceleration,acceleration,"independent closed-form child spring force")
    close(result.outputs["child"].unconstrained_tip,child_unconstrained,"independent child Euler position")
    close(result.outputs["child"].state.tip,child_tip,"independent child constrained tip")
    check(abs(result.outputs["child"].acceleration[0]) > .01,"stale authored-world parent negative control would yield zero")
    check(result.goals["child"].basis == result.worlds["parent"].basis,"same-tick solved parent orientation")
    return {"a_rational":"1/4800","parent_tip":list(result.outputs["parent"].state.tip),
            "child_acceleration":list(acceleration),"child_tip":list(child_tip)}


def hierarchy_and_overlay():
    # Arbitrary names/order, nonidentity bases, nonzero authored local delta,
    # root prefix != actor root, plus a nonsimulated intermediate and branch.
    bones = {"leaf":Bone("middle",Frame((0.,0.,1.3),ry(.2))),
             "branch":Bone("anchor",Frame((-.7,.1,0.),rz(.4))),
             "middle":Bone("root",Frame((.1,.2,.6),rz(-.3))),
             "root":Bone("anchor",Frame((.2,0.,.3),ry(.35))),
             "anchor":Bone(None,Frame((0.,.2,0.),rz(.17)))}
    local = {k:v.base for k,v in bones.items()}
    local["leaf"] = Frame((.03,.02,1.33),mm(bones["leaf"].base.basis,rz(.23)))
    prefix = Frame((2.,-3.,1.),mm(ry(.6),rz(-.4)),1.7)
    p = M.Parameters(length=20.,tip_mass=20.)
    actor = ChainActor(bones,{"root":p,"leaf":p})
    actor.reset(local,prefix)
    original = actor.baseline_worlds(local,prefix)
    result = actor.step(1,local,prefix,{"root":(4.,-2.,1.),"leaf":(-3.,1.,.5)})
    check(parent_order(bones).index("root") < parent_order(bones).index("middle") < parent_order(bones).index("leaf"),"topological order independent of names/input order")
    close(result.worlds["middle"],result.worlds["root"].compose(local["middle"]),"unsimulated intermediate follows solved ancestor")
    close(result.goals["leaf"],result.worlds["middle"].compose(local["leaf"]),"descendant goal composed from authored local")
    check(result.worlds["branch"] == original["branch"],"unaffected branch exact")
    for key in actor.parameters:
        parent = prefix if bones[key].parent is None else result.worlds[bones[key].parent]
        # Independent Model equation reconstructs the target using base*delta.
        absolute_local = Frame(local[key].origin,mm(bones[key].base.basis,result.delta_bases[key]),local[key].scale)
        rebuilt = parent.compose(absolute_local)
        close(rebuilt,result.worlds[key],"base*delta and effective parent reconstruct desired world")
        doubled = parent.compose(Frame(local[key].origin,mm(bones[key].base.basis,absolute_local.basis),local[key].scale))
        check(max(abs(a-b) for a,b in zip(flat(doubled.basis),flat(rebuilt.basis))) > .1,"double-rest negative control fails materially")
    reversed_actor = ChainActor(dict(reversed(list(bones.items()))),dict(reversed(list(actor.parameters.items()))))
    reversed_actor.reset(local,prefix)
    again = reversed_actor.step(1,dict(reversed(list(local.items()))),prefix,{"leaf":(-3.,1.,.5),"root":(4.,-2.,1.)})
    check(dict(again.worlds)==dict(result.worlds) and dict(again.outputs)==dict(result.outputs),"input and sibling order invariant")
    # Returned objects cannot mutate solver state; caller dictionary reuse is safe.
    before = actor.snapshot()
    refused(lambda: result.worlds.__setitem__("root",Frame()),"world result mapping read-only")
    # MappingProxyType lacks mutators, so exercise AttributeError separately below.
    return actor,local,prefix,result,before


def main():
    analytic = first_tick_closed_form()
    # Read-only mutation raises AttributeError rather than solver ValueError.
    global refused
    old_refused = refused
    def all_refused(fn,label):
        try: fn()
        except (ValueError,TypeError,OverflowError,AttributeError): check(True,label); return
        check(False,label)
    refused = all_refused
    actor,local,prefix,result,before = hierarchy_and_overlay()
    refused(lambda: result.outputs.__setitem__("root",None),"output mapping cannot mutate states")
    check(actor.snapshot()==before,"returned result mutation leaves actor state exact")
    metadata = {"inactive":[False]}
    a = ChainActor(actor.bones,actor.parameters,raw_metadata=metadata)
    metadata["inactive"][0] = True
    copy = a.metadata_copy();copy["inactive"][0] = True
    check(a.metadata_copy()=={"inactive":[False]},"metadata copies do not alias")
    # Complete baseline is copied into immutable Frame inputs; replacing caller
    # values after the prior result cannot retroactively alter recorded worlds.
    saved_world = result.worlds["leaf"]
    changed = dict(local);changed["leaf"]=Frame((.01,.01,1.),ry(.31))
    changed_result = actor.step(2,changed,prefix)
    check(result.worlds["leaf"]==saved_world,"reused caller baseline does not mutate prior result")
    check(changed_result.goals["leaf"].origin != result.goals["leaf"].origin,"fresh authored translations sampled on next tick")
    snap = actor.snapshot()
    for fn,label in [
        (lambda:actor.step(4,local,prefix),"clock skips refused"),
        (lambda:actor.step(3,local,prefix,{"ghost":(0,0,0)}),"unknown force owner refused"),
        (lambda:actor.step(3,local,prefix,{"root":(math.inf,0,0)}),"nonfinite input refused"),
        (lambda:actor.step(3,{k:v for k,v in local.items() if k!='leaf'},prefix),"missing baseline refused"),
        (lambda:actor.step(3,local,replace(prefix,scale=2.)),"size edit requires reset"),
    ]:
        refused(fn,label);check(actor.snapshot()==snap,"refusal preserves entire state atomically")
    refused(lambda:parent_order({"a":Bone("b"),"b":Bone("a")}),"parent cycle refused")
    refused(lambda:parent_order({"a":Bone("absent")}),"missing parent refused")
    refused(lambda:M.Parameters(raw_rule_flags=0x33),"unsupported flags remain refused")
    refused(lambda:Frame(basis=((1,0,0),(0,2,0),(0,0,1))),"raw float32 or scaled basis is not strict scalar goal")
    # A late child failure must not commit the already computed parent state.
    b = ChainActor({"p":Bone(None),"c":Bone("p")},{"p":M.Parameters(length=1,tip_mass=0),"c":M.Parameters(length=1,tip_mass=0)},source_scale=1.)
    ordinary={"p":Frame(),"c":Frame((0,0,2))};b.reset(ordinary)
    snap=b.snapshot()
    refused(lambda:b.step(1,{"p":Frame((1e308,0,0)),"c":Frame((1e308,0,2))}),"late child overflow refused")
    check(b.snapshot()==snap,"late child failure rolls back all rule states")
    # Determinism, actor isolation, positive uniform unit covariance. Neither
    # translated GLB positions nor wind receive native source_scale twice.
    bones={"a":Bone(None),"b":Bone("a"),"other":Bone(None)}
    local={"a":Frame(),"b":Frame((0,0,.3),ry(.1)),"other":Frame((2,1,0),rz(.2))}
    params={k:M.Parameters() for k in ("a","b")}
    runners=[ChainActor(bones,params),ChainActor(bones,params),ChainActor(bones,params)]
    prefixes=[Frame(),Frame(),Frame(scale=2.)]
    for runner,prefix_i in zip(runners,prefixes):runner.reset(local,prefix_i)
    trace=[]
    for tick in range(1,241):
        force=(math.sin(tick*.03)*3.,.5,-.25)
        out=[runner.step(tick,local,prefix_i,{"a":M.multiply(force,prefix_i.scale),"b":M.multiply(force,-prefix_i.scale)}) for runner,prefix_i in zip(runners,prefixes)]
        check(dict(out[0].outputs)==dict(out[1].outputs),"independent actors deterministic")
        for key in params:
            close(out[2].outputs[key].state.tip,M.multiply(out[0].outputs[key].state.tip,2.),"root-size covariance of chain tips",eps=1e-10)
            close(flat(out[2].outputs[key].basis),flat(out[0].outputs[key].basis),"root-size covariance of orientations",eps=1e-10)
            close(out[2].goals[key].origin,M.multiply(out[0].goals[key].origin,2.),"descendant origins scale once",eps=1e-10)
            check(abs(M.length(M.subtract(out[0].outputs[key].state.tip,out[0].goals[key].origin))-.381) < 1e-11,"retained20 native length scales once by.01905")
        if tick in (1,120,240):trace.append({"tick":tick,"tips":{k:list(out[0].outputs[k].state.tip) for k in params}})
    final=runners[0].snapshot(); runners[0].reset(local)
    for tick in range(1,241):
        force=(math.sin(tick*.03)*3.,.5,-.25)
        runners[0].step(tick,local,world_accelerations={"a":force,"b":M.multiply(force,-1)})
    check(runners[0].snapshot()==final,"reset/replay deterministic exact")
    isolated=runners[1].snapshot();runners[0].stop()
    check(runners[1].snapshot()==isolated,"stopping one actor leaves other exact")
    refused(lambda:runners[0].step(241,local),"stopped actor cannot continue")
    # Zero-cone + strong finite input coverage preserves exact analytical edge.
    for i in range(1,101):
        p=M.Parameters(length=20.,tip_mass=0.,angle_limit=0.)
        runner=ChainActor(bones,{"a":p,"b":p})
        tilted={**local,"a":Frame(basis=ry(i*.0031))};runner.reset(tilted)
        out=runner.step(1,tilted,world_accelerations={"a":(1e6,0,0),"b":(-1e6,0,0)})
        for key in ("a","b"):
            close(out[key].basis[2] if False else out.outputs[key].basis[2],out.goals[key].basis[2],"exact zero-cone chain direction",eps=1e-12)
            check(all(math.isfinite(x) for x in (*out.outputs[key].state.tip,*out.outputs[key].state.velocity)),"strong-input finite")
    result={"status":"PASSED_CPU_SYNTHETIC_CHAIN_CHECKS_ONLY","checks":checks,"failures":0,"maximum_numeric_error":max_error,
            "analytical_first_tick":analytic,"synthetic_trace":trace,"dynamic_ticks":820,"scope":{"native_geometry":False,"Godot_parsed_or_run":False,"SDK_executed":False,"actual_native_chains_qualified":False}}
    target=Path(__file__).with_name("CPU_RESULT.json")
    with target.open("x",encoding="utf-8",newline="\n") as f:json.dump(result,f,indent=2,allow_nan=False);f.write("\n")
    print(json.dumps({k:result[k] for k in ("status","checks","failures","maximum_numeric_error")}))


if __name__=="__main__": main()
