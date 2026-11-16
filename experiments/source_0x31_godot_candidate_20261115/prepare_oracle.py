"""CPU-only PUBLIC synthetic oracle preparation. Never invokes/parses Godot."""
from pathlib import Path
from dataclasses import asdict
import ast
import hashlib
import importlib.util
import json
import math
import struct
import sys
import time

sys.dont_write_bytecode = True
CODE = Path(__file__).resolve().parent
ROOT = CODE.parents[1]
REFERENCE = ROOT / "experiments/source_0x31_candidate_20261115"
REFERENCE_SHA = "dd472f2b4de64adebc83a03c2e812ac2e14805c752b220c26c53dd58bf99519c"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def json_copy(value): return json.loads(json.dumps(value, allow_nan=False))


def main():
    target = CODE / "PUBLIC_SYNTHETIC_ORACLE.json"
    if target.exists(): raise ValueError("Fresh synthetic oracle required")
    reference_path = REFERENCE / "candidate.py"
    if sha(reference_path) != REFERENCE_SHA: raise ValueError("Reviewed corrected Python reference changed")
    ast.parse(reference_path.read_text(encoding="utf-8-sig"))
    spec = importlib.util.spec_from_file_location("has_source0x31_godot_oracle_math", reference_path)
    reference = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = reference
    spec.loader.exec_module(reference)
    Params, Goal, Actor = reference.Parameters, reference.Goal, reference.Actor
    def columns(angle):
        c, s = math.cos(angle), math.sin(angle)
        return ((c,0.,-s), (0.,1.,0.), (s,0.,c))
    def goal_at(tick):
        t = tick/120
        return Goal((.25*math.sin(.7*t), .1*math.sin(.9*t), .13*math.cos(.4*t)), columns(.25*math.sin(.8*t)))
    def c_map(v): return (v[0],v[2],-v[1])
    def params_dict(value): return {key: v for key,v in asdict(value).items() if key != "raw_rule_flags"}
    def goal_dict(value): return {"base":value.base,"basis":value.basis}
    sequences = []
    def sequence(name, parameters, seed, steps, sample_ticks, gravity=(0.,0.,-1.)):
        actor = Actor(parameters, {"public_synthetic":True}, gravity_down=gravity)
        actor.reset(seed)
        frames = []
        for tick, goals, forces in steps:
            output = actor.step(tick,goals,forces)
            row = {"tick":tick,"goals":{key:goal_dict(value) for key,value in goals.items()},"external":forces}
            if tick in sample_ticks: row["expected"] = {key:asdict(value) for key,value in output.items()}
            frames.append(row)
        result = {"id":name,"parameters":{key:params_dict(value) for key,value in parameters.items()},
                  "seed":{key:goal_dict(value) for key,value in seed.items()},"gravity_down":gravity,
                  "kind":"Independent synthetic goals; no native-parent recomposition", "frames":frames}
        sequences.append(result)
        return result
    # One rule with Junko-like coefficients; poses and accelerations are invented.
    sequence("synthetic_front_one",{"front":Params()}, {"front":Goal()},
             ((tick,{"front":goal_at(tick)},{"front":(50/.01905*(1+.2*math.sin(tick/19)),3.,0.)}) for tick in range(1,241)),
             {1,2,12,24,60,120,180,240})
    two = sequence("known_two_independent_rule_replay",{"a":Params(),"b":Params(yaw_stiffness=100.,pitch_stiffness=100.)},
                   {"a":Goal(),"b":Goal((.3,.2,.1))},
                   ((tick,{"a":goal_at(tick),"b":Goal((.3,.2,.1),columns(.12*math.sin(tick/90)))},{"a":(7*math.sin(tick/31),3.,0.)}) for tick in range(1,361)),
                   {1,2,12,24,60,120,240,360})
    trace_path = REFERENCE / "SYNTHETIC_TRACE-zero-cone-fix.json"
    old_trace = json.loads(trace_path.read_bytes())
    sample_lookup = {int(row["tick"]): row for row in two["frames"] if "expected" in row}
    for row in old_trace["reset_samples"]:
        expected = sample_lookup[int(row["tick"])]["expected"]
        if json_copy(expected["a"]) != row["a"] or json_copy(expected["b"]) != row["b"]:
            raise AssertionError("Known immutable two-rule trace no longer matches")
    # Converted-coordinate instances are still synthetic math, not two imports.
    for source_scale in (.01905,.0381):
        for root_scale in (1.,2.):
            factor = source_scale*root_scale
            offset = (.37,-.22,.41)
            def mapped(goal):
                return Goal(tuple(offset[i]+factor*c_map(goal.base)[i] for i in range(3)), tuple(c_map(v)for v in goal.basis))
            sequence("converted_scalar_math_%s_%s"%(source_scale,root_scale),{"r":Params().translated_size(factor)},
                     {"r":mapped(goal_at(0))},
                     ((tick,{"r":mapped(goal_at(tick))},{"r":tuple(factor*v for v in c_map((15*math.sin(tick/27),3*math.cos(tick/31),-2.)))}) for tick in range(1,121)),
                     {1,2,12,24,60,120}, gravity=(0.,-1.,0.))
    zero_goals = []
    for index in range(1,1001):
        goal = Goal(basis=columns(index*.0031))
        actor = Actor({"r":Params(tip_mass=0.,angle_limit=0.)})
        actor.reset({"r":goal})
        output = actor.step(1,{"r":goal})["r"]
        zero_goals.append({"goal":goal_dict(goal),"expected_tip":output.state.tip,"seeded_tip":goal.tip(Params(tip_mass=0.,angle_limit=0.))})
    def f32(value): return struct.unpack("<f",struct.pack("<f",value))[0]
    midpoint = 1+2**-24
    vectors = [(0.,0.,0.),(.01905,1.8288,20.),(-50.5,12.25,-.0031),
               (math.nextafter(midpoint,-math.inf),midpoint,math.nextafter(midpoint,math.inf)),
               (2**-126,2**-149,-2**-149)]
    adapter_vectors = [{"input":v,"expected_float32":tuple(f32(x)for x in v),"packed_float32_hex":struct.pack("<3f",*v).hex()}for v in vectors]
    adapter_bases = []
    for angle in (0.,.0031,.7,3.1):
        basis = columns(angle)
        rounded = tuple(tuple(f32(x)for x in v)for v in basis)
        # Determinant is evaluated independently in scalar64 for rounded columns.
        a,b,c = rounded
        terms = (a[0]*b[1]*c[2],a[1]*b[2]*c[0],a[2]*b[0]*c[1],a[2]*b[1]*c[0],a[1]*b[0]*c[2],a[0]*b[2]*c[1])
        determinant = sum(terms[:3])-sum(terms[3:])
        unit_roundoff = 2**-24
        gamma14 = 14*unit_roundoff/(1-14*unit_roundoff)
        # 14-operation floating determinant bound, fixed before engine execution.
        determinant_bound = gamma14*sum(abs(x)for x in terms)+8*sys.float_info.epsilon
        try:
            Goal(basis=rounded)
            strict_accepts = True
        except ValueError:
            strict_accepts = False
        adapter_bases.append({"input_columns":basis,"packed_columns_float32_hex":[struct.pack("<3f",*v).hex()for v in basis],
                              "rounded_determinant_scalar64":determinant,"native_float32_determinant_error_bound":determinant_bound,
                              "strict_math_validator_accepts_quantized_columns":strict_accepts})
    rational_path = REFERENCE / "CLOSED_FORM-zero-cone-fix.json"
    damping_path = REFERENCE / "DAMPING_GRAVITY-zero-cone-fix.json"
    rational = json.loads(rational_path.read_bytes())
    damping = json.loads(damping_path.read_bytes())
    oracle = {"format":"has_public_source0x31_scalar64_oracle_1","status":"PREPARED_ENGINE_UNPARSED_UNRUN",
              "created_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"source_arrays":"PUBLIC_SYNTHETIC_ONLY_NO_NATIVE_GEOMETRY",
              "reference_sha256":REFERENCE_SHA,"known_trace_sha256":sha(trace_path),
              "independent_rational_source_sha256":sha(rational_path),"independent_damping_source_sha256":sha(damping_path),
              "flags_hex":"0x31","fixed_hz":120,"independent_rational":rational["expected"],
              "independent_moved_goal_acceleration":[10.,-20.,-20.],
              "independent_damping":{"damped":damping["expected_damped"],"undamped":damping["expected_undamped"]},
              "sequences":sequences,"zero_cone_goals":zero_goals,
              "float32_vectors":adapter_vectors,"float32_bases":adapter_bases,
              "preregistered_gates":{"declared_before_engine_parse":True,"scalar64_trajectory_absolute":1e-9,
                  "independent_rational_absolute":1e-12,"zero_cone_rest_displacement":1e-10,
                  "float32_adapter":"Exact packed IEEE754 binary32 words; basis determinant bound derived per case",
                  "basis_validation":"Keep strict mathematical1e-9 domain; quantized engine basis is a separate boundary",
                  "qualification":"Engineering gates, not a formal accumulated-error proof; preserve any failure without posthoc relaxation"},
              "actual_engine_execution":False,"actual_Model_FK_parent_body_fan_Record_Off_portability":"UNRUN_NOT_INTEGRATED"}
    data = (json.dumps(oracle,separators=(",",":"),allow_nan=False)+"\n").encode()
    with target.open("xb")as handle:handle.write(data)
    if sha(reference_path) != REFERENCE_SHA or sha(trace_path) != oracle["known_trace_sha256"]:
        raise AssertionError("Immutable Python evidence changed while preparing")
    print(json.dumps({"oracle":str(target),"bytes":len(data),"sha256":sha(target),"sequences":len(sequences),
                      "simulation_input_frames":sum(len(row["frames"])for row in sequences),"zero_cone_cases":len(zero_goals),
                      "float32_vector_cases":len(adapter_vectors),"float32_basis_cases":len(adapter_bases),"engine":"UNPARSED_UNRUN"}))


if __name__ == "__main__": main()
