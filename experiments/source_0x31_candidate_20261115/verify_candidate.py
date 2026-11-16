"""CPU mathematical checks, not executable-SDK or artist-native parity tests."""
from pathlib import Path
from dataclasses import asdict, replace
from copy import deepcopy
import hashlib
import json
import math
import subprocess
import sys
import time
import argparse
import re

sys.dont_write_bytecode = True
from candidate import Actor, DT, FIXED_HZ, Goal, IDENTITY, Parameters

CODE = Path(__file__).resolve().parent
ROOT = CODE.parents[1]
checks = []


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)


def close(a, b, tolerance=1e-10):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b))) <= tolerance


def reject(call, label):
    try:
        call()
    except (ValueError, TypeError):
        checks.append(label)
    else:
        raise AssertionError("Missing refusal: " + label)


def rotated_columns(angle):
    # Independent explicit Y-axis rotation, columns of a rigid matrix.
    c, s = math.cos(angle), math.sin(angle)
    return ((c, 0., -s), (0., 1., 0.), (s, 0., c))


def c_map(value): return (value[0], value[2], -value[1])


def goal_at(tick):
    t = tick / FIXED_HZ
    return Goal((.25*math.sin(.7*t), .1*math.sin(.9*t), .13*math.cos(.4*t)), rotated_columns(.25*math.sin(.8*t)))


def manual_first_step(parameters, new_base, wind):
    # Seed is the independent identity-goal tip (0,0,L), with zero velocity.
    # A moved identity goal supplies error=(base.x,base.y,base.z).
    ax = parameters.yaw_stiffness*new_base[0] + wind[0]
    ay = parameters.pitch_stiffness*new_base[1] + wind[1]
    az = -parameters.tip_mass + wind[2]  # along spring omitted, not inverse mass
    velocity = (ax*DT, ay*DT, az*DT)
    position = (ax*DT*DT, ay*DT*DT, parameters.length+az*DT*DT)
    segment = tuple(position[i]-new_base[i] for i in range(3))
    size = math.sqrt(sum(v*v for v in segment))
    direction = tuple(v/size for v in segment)
    angle = math.acos(max(-1., min(1., direction[2])))
    if direction[2] < 0:
        angle = 2*math.pi-angle
    projected = angle > parameters.angle_limit
    if projected:
        target = (new_base[0], new_base[1], new_base[2]+parameters.length)
        difference = tuple(target[i]-position[i] for i in range(3))
        magnitude = math.sqrt(sum(v*v for v in difference))
        radius = parameters.length*math.sin(parameters.angle_limit)
        corrected = tuple(target[i]-radius*difference[i]/magnitude for i in range(3))
        relative = tuple(corrected[i]-new_base[i] for i in range(3))
        magnitude = math.sqrt(sum(v*v for v in relative))
        direction = tuple(v/magnitude for v in relative)
    post_position = tuple(new_base[i]+parameters.length*direction[i] for i in range(3))
    radial_speed = sum(velocity[i]*direction[i] for i in range(3))
    post_velocity = tuple(velocity[i]-radial_speed*direction[i] for i in range(3))
    return (ax, ay, az), velocity, position, post_position, post_velocity, projected


def inspect_invariants(output, goal, parameters):
    p, v = output.state.tip, output.state.velocity
    segment = tuple(p[i]-goal.base[i] for i in range(3))
    size = math.sqrt(sum(x*x for x in segment))
    forward = tuple(x/size for x in segment)
    angle = math.acos(max(-1., min(1., sum(forward[i]*goal.basis[2][i] for i in range(3)))))
    radial_speed = abs(sum(v[i]*forward[i] for i in range(3)))
    finite = all(math.isfinite(x) for row in (p, v, *output.basis) for x in row)
    orthogonality = max(abs(sum(output.basis[i][k]*output.basis[j][k] for k in range(3))-(1. if i==j else 0.)) for i in range(3) for j in range(3))
    if not finite or abs(size-parameters.length) > 1e-9 or angle > parameters.angle_limit+1e-9 or radial_speed > 1e-7 or orthogonality > 1e-9:
        raise AssertionError("Finite length/cone/tangent/rigid-basis invariant failed")
    return angle, math.sqrt(sum(x*x for x in v))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="")
    run_id = parser.parse_args().run_id
    if run_id and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id) is None:
        raise ValueError("Safe bounded run ID required")
    suffix = "-" + run_id if run_id else ""
    result_path = CODE / ("RESULT" + suffix + ".json")
    trace_path = CODE / ("SYNTHETIC_TRACE" + suffix + ".json")
    if result_path.exists() or trace_path.exists():
        raise ValueError("Fresh owned evidence paths required")
    source_files = {
        "jigglebones.cpp": "a3f319258a21498bfa6467bef641446d66ecd5497b9dc8a949b1f08b87d7027e",
        "jigglebones.h": "4e859d919b71f62bfee8fd9554e41b25c5b0ef8447d400c932f411340b296c1f",
        "studio.h": "cf5ac8bb6bfe4c7dab15024e8424afaab02ff781965d48077c55341b3914fff2"}
    for name, expected in source_files.items():
        path = ROOT / "output/source-sdk-jiggle-reference-20261114" / name
        check(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "Immutable inspected SDK source " + name)
    traces = {"source": "Synthetic independent goals only; no native model coordinates", "first_step_examples": [], "reset_samples": []}
    # Scalar first-force/kinematic expectations are constructed without solver helpers.
    for stiffness, base, wind in ((50., (0., 0., 0.), (3., 4., 0.)),
                                  (100., (.1, -.2, 2.), (0., 0., 0.)),
                                  (50., (50., 0., 0.), (0., 0., 0.))):
        parameters = Parameters(yaw_stiffness=stiffness, pitch_stiffness=stiffness)
        actor = Actor({"test": parameters})
        actor.reset({"test": Goal()})
        output = actor.step(1, {"test": Goal(base)})["test"] if wind == (0.,0.,0.) else actor.step(1, {"test": Goal(base)}, {"test": wind})["test"]
        expected = manual_first_step(parameters, base, wind)
        check(close(output.acceleration, expected[0]), "Independent scalar first acceleration " + str(base))
        check(close(output.unconstrained_velocity, expected[1]) and close(output.unconstrained_tip, expected[2]), "Independent Euler velocity-before-position " + str(base))
        check(close(output.state.tip, expected[3]) and close(output.state.velocity, expected[4]), "Independent projection and radial-speed removal " + str(base))
        check(output.angle_projected == expected[5], "Independent angular branch " + str(base))
        traces["first_step_examples"].append({"stiffness": stiffness, "new_base": base, "wind": wind, "expected_acceleration": expected[0], "expected_unconstrained_velocity": expected[1], "expected_unconstrained_tip": expected[2], "actual": asdict(output)})
    for mass in (0., 20., 40.):
        actor = Actor({"rule": Parameters(tip_mass=mass)})
        actor.reset({"rule": Goal()})
        output = actor.step(1, {"rule": Goal()})["rule"]
        check(output.acceleration == (0., 0., -mass), "tipMass is downward acceleration, mass=" + str(mass))
    base_parameters = Parameters()
    ignored_along = replace(base_parameters, along_stiffness=987654., along_damping=123456.)
    first, second = Actor({"rule": base_parameters}), Actor({"rule": ignored_along})
    first.reset({"rule": Goal()}); second.reset({"rule": Goal()})
    for tick in range(1, 241):
        goals = {"rule": Goal((.1*math.sin(tick/12), -.1, 2.))}
        check(first.step(tick, goals) == second.step(tick, goals), "Length flag excludes along terms tick" + str(tick))
    for flags in (0x01, 0x11, 0x21, 0x33, 0x71, 0xB1, 0x131):
        reject(lambda flags=flags: Parameters(raw_rule_flags=flags), "Unsupported flags refused " + hex(flags))
    for kwargs in ({"length": 0.}, {"tip_mass": -1.}, {"angle_limit": math.pi/2}, {"yaw_stiffness": float("nan")}, {"pitch_damping": float("inf")}):
        reject(lambda kwargs=kwargs: Parameters(**kwargs), "Invalid bounded parameter refused " + repr(kwargs))
    for basis in (((-1.,0.,0.), (0.,1.,0.), (0.,0.,1.)), ((2.,0.,0.), (0.,1.,0.), (0.,0.,1.)), ((1.,.1,0.), (0.,1.,0.), (0.,0.,1.))):
        reject(lambda basis=basis: Goal(basis=basis), "Mirrored/scaled/sheared input refused " + repr(basis[0]))
    raw = {"native_rule_flags": 0x31, "retained_unused": {"along_stiffness": 100., "opaque": [1, 2, 3]}}
    original_raw = deepcopy(raw)
    actor = Actor({"a": Parameters(), "b": Parameters(yaw_stiffness=100., pitch_stiffness=100.)}, raw)
    seed = {"a": Goal(), "b": Goal((.3, .2, .1))}
    actor.reset(seed)
    before = actor.snapshot()
    for call, label in ((lambda: actor.step(0, seed), "Repeated initial tick"),
                        (lambda: actor.step(2, seed), "Skipped tick"),
                        (lambda: actor.step(1, {"a": Goal()}), "Missing rule goal"),
                        (lambda: actor.step(1, seed, {"unknown": (1.,0.,0.)}), "Unknown force rule"),
                        (lambda: actor.step(1, seed, {"b": (float("nan"),0.,0.)}), "Invalid second-rule force")):
        reject(call, label + " refused")
        check(actor.snapshot() == before, label + " leaves all rule states/tick unchanged")
    raw["retained_unused"]["opaque"].append(4)
    returned = actor.raw_metadata
    returned["retained_unused"]["opaque"].append(5)
    check(actor.raw_metadata == original_raw, "Retained metadata copies isolate mutable caller and getter")
    # Replay is byte-for-byte deterministic within this Python/clock/math context.
    def run_replay(target):
        target.reset(seed)
        frames = []
        for tick in range(1, 361):
            goals = {"a": goal_at(tick), "b": Goal((.3,.2,.1), rotated_columns(.12*math.sin(tick/90)))}
            wind = {"a": (7.*math.sin(tick/31), 3., 0.)}
            outputs = target.step(tick, goals, wind)
            if tick in (1, 120, 240, 360):
                frames.append({"tick": tick, "a": asdict(outputs["a"]), "b": asdict(outputs["b"])})
        return json.dumps(frames, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    first_replay = run_replay(actor)
    twin = Actor(dict(actor.parameters), original_raw)
    check(run_replay(actor) == first_replay == run_replay(twin), "Reset/cold independent actor exact synthetic replay")
    traces["reset_samples"] = json.loads(first_replay)
    untouched = twin.snapshot()
    actor.step(361, {"a": goal_at(361), "b": Goal()}, {"a": (100.,20.,0.)})
    check(twin.snapshot() == untouched, "Advancing one actor cannot change another actor")
    actor.stop()
    check(actor.snapshot() == (False, 0, ()), "Stop clears numerical state only")
    reject(lambda: actor.step(1, seed), "Stopped actor cannot resurrect without reset")
    actor.reset(seed)
    check(actor.snapshot() == before, "Explicit reset reseeds current goals at tick0")
    # Metamorphic covariance covers the nonlinear projection but is not native parity.
    covariance_max = 0.
    bad_mass_difference = 0.
    for source_scale in (.01905, .0381):
        for root_scale in (1., 2.):
            factor = source_scale*root_scale
            offset = (.37, -.22, .41)
            def mapped_goal(goal):
                return Goal(tuple(offset[i]+factor*c_map(goal.base)[i] for i in range(3)), tuple(c_map(column) for column in goal.basis))
            native = Actor({"rule": Parameters()})
            translated = Actor({"rule": Parameters().translated_size(factor)}, gravity_down=(0.,-1.,0.))
            wrong_mass = Actor({"rule": replace(Parameters().translated_size(factor), tip_mass=20.)}, gravity_down=(0.,-1.,0.))
            native.reset({"rule": goal_at(0)})
            translated.reset({"rule": mapped_goal(goal_at(0))})
            wrong_mass.reset({"rule": mapped_goal(goal_at(0))})
            for tick in range(1, 361):
                wind = (15.*math.sin(tick/27), 3.*math.cos(tick/31), -2.)
                mapped_wind = tuple(factor*v for v in c_map(wind))
                n = native.step(tick, {"rule": goal_at(tick)}, {"rule": wind})["rule"]
                t = translated.step(tick, {"rule": mapped_goal(goal_at(tick))}, {"rule": mapped_wind})["rule"]
                w = wrong_mass.step(tick, {"rule": mapped_goal(goal_at(tick))}, {"rule": mapped_wind})["rule"]
                expected_position = tuple(offset[i]+factor*c_map(n.state.tip)[i] for i in range(3))
                expected_velocity = tuple(factor*v for v in c_map(n.state.velocity))
                errors = [math.dist(t.state.tip, expected_position), math.dist(t.state.velocity, expected_velocity)]
                errors.extend(math.dist(t.basis[i], c_map(n.basis[i])) for i in range(3))
                covariance_max = max(covariance_max, *errors)
                bad_mass_difference = max(bad_mass_difference, math.dist(t.state.tip, w.state.tip))
            check(covariance_max < 1e-9, "Full candidate unit covariance scale=" + str(factor))
    check(bad_mass_difference > .01, "Unscaled tipMass negative control diverges")
    property_steps = 0
    constrained_steps = 0
    maximum_angle = maximum_speed = 0.
    for stiffness in (50., 100.):
        for strength in (3., 12., 50.):
            for direction in ((1.,0.,0.), (-1.,0.,0.), (0.,1.,0.), (0.,0.,1.)):
                parameters = Parameters(yaw_stiffness=stiffness, pitch_stiffness=stiffness)
                instance = Actor({"rule": parameters})
                instance.reset({"rule": goal_at(0)})
                for tick in range(1, 721):
                    # Synthetic acceleration amplitudes are not HAS fan-speed units.
                    force = tuple(strength/.01905*component*(1+.2*math.sin(tick/19)) for component in direction)
                    goal = goal_at(tick)
                    output = instance.step(tick, {"rule": goal}, {"rule": force})["rule"]
                    angle, speed = inspect_invariants(output, goal, parameters)
                    maximum_angle, maximum_speed = max(maximum_angle, angle), max(maximum_speed, speed)
                    constrained_steps += output.angle_projected
                    property_steps += 1
                check(True, "Finite length/cone/tangent invariants stiffness=" + str(stiffness) + " synthetic_strength=" + str(strength) + " direction=" + str(direction))
    check(constrained_steps > 0, "Strong-input cases actually exercise angular projection")
    for name, expected in source_files.items():
        check(hashlib.sha256((ROOT/"output/source-sdk-jiggle-reference-20261114"/name).read_bytes()).hexdigest() == expected, "Inspected SDK source unchanged " + name)
    result = {"format": "has_source_0x31_math_candidate_result_1", "status": "PASSED_BOUNDED_SYNTHETIC_MATH_CHECKS_NOT_NATIVE_PARITY",
              "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "source_HEAD": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "candidate_sha256": hashlib.sha256((CODE/"candidate.py").read_bytes()).hexdigest(),
              "assertions_passed": len(checks), "assertion_labels": checks, "property_integration_steps": property_steps,
              "actual_angle_projection_steps": constrained_steps, "maximum_angle_radians": maximum_angle,
              "maximum_velocity_native_units_per_second": maximum_speed, "unit_covariance_max_error": covariance_max,
              "unscaled_mass_negative_control_max_tip_difference": bad_mass_difference,
              "clock": {"fixed_hz": FIXED_HZ, "initialization": "seed goal at tick0; first integration at tick1", "SDK_first_call_min_dt_or_fallback_parity": False},
              "scope": {"production_integration": False, "SDK_compiled_or_executed": False,
                        "native_geometry_or_rest_arrays_loaded": False, "Godot_Blender_or_other_app_launched": False,
                        "actual_HAS_FK_or_parent_rule_ordering": "UNRUN", "native_SFM_artist_motion": "UNQUALIFIED",
                        "actual_fan_units_or_renderer_Record_Off_restore": "UNRUN", "float32_or_cross_platform_bit_parity": False},
              "source_sdk_commit": "019e91ccd650a34745934c65cdbbe89ffcc44ede", "inspected_source_hashes": source_files}
    with trace_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(traces, handle, indent=2, allow_nan=False); handle.write("\n")
    result["synthetic_trace_sha256"] = hashlib.sha256(trace_path.read_bytes()).hexdigest()
    with result_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({"status": result["status"], "assertions": len(checks), "property_steps": property_steps, "angle_projection_steps": constrained_steps, "unit_covariance_max": covariance_max}))


if __name__ == "__main__":
    main()
