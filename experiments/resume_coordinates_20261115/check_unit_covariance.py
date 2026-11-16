"""Synthetic unit/axis algebra only. No engine or native solver qualification."""
from pathlib import Path
import hashlib
import json
import math

CODE = Path(__file__).resolve().parent
ROOT = CODE.parents[1]


def add(a, b): return tuple(x + y for x, y in zip(a, b))
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def mul(a, n): return tuple(x * n for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def norm(a): return math.sqrt(dot(a, a))
def unit(a): return mul(a, 1 / norm(a))
def convert(a): return (a[0], a[2], -a[1])
def inverse_convert(a): return (a[0], -a[2], a[1])
def error(a, b): return norm(sub(a, b))


def rotate(a, axis, angle):
    k = unit(axis)
    cross = (k[1]*a[2]-k[2]*a[1], k[2]*a[0]-k[0]*a[2], k[0]*a[1]-k[1]*a[0])
    return add(add(mul(a, math.cos(angle)), mul(cross, math.sin(angle))), mul(k, dot(k, a)*(1-math.cos(angle))))


def spring_acceleration(basis, e, velocity, ky, kp, dy, dp):
    return add(mul(basis[0], ky*dot(basis[0], e)-dy*dot(basis[0], velocity)),
               mul(basis[1], kp*dot(basis[1], e)-dp*dot(basis[1], velocity)))


def main():
    output = CODE / "UNIT_COVARIANCE.json"
    if output.exists():
        raise ValueError("Fresh result required")
    sdk = ROOT / "output/source-sdk-jiggle-reference-20261114/jigglebones.cpp"
    sdk_sha = hashlib.sha256(sdk.read_bytes()).hexdigest()
    if sdk_sha != "a3f319258a21498bfa6467bef641446d66ecd5497b9dc8a949b1f08b87d7027e":
        raise ValueError("Pinned SDK reference changed")
    identity = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
    cases = 0
    maxima = {"tip": 0., "acceleration": 0., "velocity": 0., "position": 0., "length_projection": 0.}
    negatives = {"local_Y_instead_of_Z_min": math.inf, "unscaled_mass_min": math.inf,
                 "rotating_world_gravity_with_model_max": 0., "double_length_conversion_min": math.inf}
    for source_scale in (.01905, .0381):
        for root_scale in (1., 2.):
            length_scale = source_scale * root_scale
            base = (.31, -.17, .93)
            translation = (.47, -.23, .37)
            map_point = lambda p: add(translation, mul(convert(p), length_scale))
            for angle in (0., .23, -.47):
                basis = tuple(rotate(v, (.3, .7, -.2), angle) for v in identity)
                world_basis = tuple(convert(v) for v in basis)
                length = 20.
                tip = add(base, mul(basis[2], length))
                world_base = map_point(base)
                world_tip = add(world_base, mul(world_basis[2], length*length_scale))
                maxima["tip"] = max(maxima["tip"], error(world_tip, map_point(tip)))
                negatives["local_Y_instead_of_Z_min"] = min(negatives["local_Y_instead_of_Z_min"], error(world_tip, add(world_base, mul(world_basis[1], length*length_scale))))
                negatives["double_length_conversion_min"] = min(negatives["double_length_conversion_min"], length*length_scale*(1-source_scale))
                # Gravity is Source-global -Z -> HAS-global -Y, independent of model orientation.
                native_gravity = (0., 0., -20.)
                world_gravity = (0., -20.*length_scale, 0.)
                negatives["unscaled_mass_min"] = min(negatives["unscaled_mass_min"], error(world_gravity, (0., -20., 0.)))
                rotated_gravity = rotate(world_gravity, (.3, .7, -.2), angle)
                negatives["rotating_world_gravity_with_model_max"] = max(negatives["rotating_world_gravity_with_model_max"], error(rotated_gravity, world_gravity))
                for stiffness in (50., 100.):
                    for world_wind in ((0., 0., 0.), (.03, 0., 0.), (-.12, 0., 0.), (0., .5, 0.), (0., 0., -.5)):
                        native_wind = mul(inverse_convert(world_wind), 1/length_scale)
                        native_position = add(tip, (.03, -.02, .01))
                        native_velocity = (.7, -.2, .3)
                        native_spring = spring_acceleration(basis, sub(tip, native_position), native_velocity, stiffness, stiffness, 5., 5.)
                        native_acceleration = add(add(native_spring, native_gravity), native_wind)
                        world_position = map_point(native_position)
                        world_velocity = mul(convert(native_velocity), length_scale)
                        world_spring = spring_acceleration(world_basis, sub(world_tip, world_position), world_velocity, stiffness, stiffness, 5., 5.)
                        world_acceleration = add(add(world_spring, world_gravity), world_wind)
                        maxima["acceleration"] = max(maxima["acceleration"], error(world_acceleration, mul(convert(native_acceleration), length_scale)))
                        dt = 1/120
                        vn = add(native_velocity, mul(native_acceleration, dt))
                        vw = add(world_velocity, mul(world_acceleration, dt))
                        pn = add(native_position, mul(vn, dt))
                        pw = add(world_position, mul(vw, dt))
                        maxima["velocity"] = max(maxima["velocity"], error(vw, mul(convert(vn), length_scale)))
                        maxima["position"] = max(maxima["position"], error(pw, map_point(pn)))
                        projected_native = add(base, mul(unit(sub(pn, base)), length))
                        projected_world = add(world_base, mul(unit(sub(pw, world_base)), length*length_scale))
                        maxima["length_projection"] = max(maxima["length_projection"], error(projected_world, map_point(projected_native)))
                        cases += 1
    if max(maxima.values()) > 1e-12 or min(negatives.values()) < 1e-5:
        raise ValueError("Algebraic covariance or negative control failed")
    result = {"format": "has_source_jiggle_unit_covariance_1", "status": "PASSED_SYNTHETIC_ALGEBRA_ONLY",
              "cases": cases, "maximum_errors": maxima, "negative_controls": negatives,
              "source_sdk_sha256": sdk_sha,
              "scope": {"apps_or_native_runtime_launched": False, "native_model_data_used": False,
                        "full_0x31_solver_implemented": False, "SDK_compiled_or_executed": False,
                        "HAS_dynamics_or_clock_fidelity": "UNRUN", "actual_two_conversion_scales": "UNRUN"},
              "interpretation": "Covariance of yaw/pitch acceleration, one Euler step and length projection; angle projection/history/basis construction and integration stability are not exercised. Synthetic scales are not actual import qualifications.",
              "policy_boundary": "A similarity-preserving native gravity uses source_scale*root_scale*tipMass; fixed physical gravity is a different artistic policy. HAS airflow has no established native Source wind equivalence."}
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"result": str(output), "status": result["status"], "cases": cases, "max_error": max(maxima.values())}))


if __name__ == "__main__":
    main()
