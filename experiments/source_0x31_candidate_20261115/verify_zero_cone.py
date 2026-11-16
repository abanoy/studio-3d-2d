"""Reproduce original root boundary failure and check exact zero-cone correction."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

sys.dont_write_bytecode = True
import candidate

CODE = Path(__file__).resolve().parent
ORIGINAL_SHA = "636a81bd7932e790c7a3d512d88ea71e09362e473c4f8bc3f84e4022fbbbce9f"


def main():
    output_path = CODE / "ZERO_CONE_CORRECTION.json"
    if output_path.exists():
        raise ValueError("Fresh result required")
    original_path = CODE / "attempt1-original/candidate.py"
    if hashlib.sha256(original_path.read_bytes()).hexdigest() != ORIGINAL_SHA:
        raise ValueError("Immutable original candidate changed")
    spec = importlib.util.spec_from_file_location("has_source0x31_original_boundary", original_path)
    old = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = old
    spec.loader.exec_module(old)
    rows = {}
    for name, module in (("original", old), ("corrected", candidate)):
        failures = []
        maximum_displacement = 0.
        for index in range(1, 1001):
            angle = index*.0031
            c, s = math.cos(angle), math.sin(angle)
            goal = module.Goal(basis=((c,0.,-s), (0.,1.,0.), (s,0.,c)))
            parameters = module.Parameters(tip_mass=0., angle_limit=0.)
            actor = module.Actor({"r": parameters})
            actor.reset({"r": goal})
            expected = goal.tip(parameters)
            try:
                output = actor.step(1, {"r": goal})["r"]
                displacement = math.dist(output.state.tip, expected)
                maximum_displacement = max(maximum_displacement, displacement)
                if displacement > 1e-10 or output.state.velocity != (0.,0.,0.):
                    failures.append({"case": index, "failure": "rest_changed"})
            except ValueError as error:
                failures.append({"case": index, "failure": type(error).__name__, "message": str(error)})
        rows[name] = {"cases": 1000, "failures": len(failures), "first_failures": failures[:12], "maximum_rest_displacement": maximum_displacement, "displacement_gate": 1e-10}
    if rows["original"]["failures"] != 104 or rows["corrected"]["failures"] != 0:
        raise AssertionError("Original root reproduction or corrected zero-cone sweep failed")
    # Move/rotate the permitted ray under strong acceleration. Analytic expected
    # tip is simply base+L*unit(goal.forward), independent of unprojected motion.
    parameters = candidate.Parameters(angle_limit=0.)
    actor = candidate.Actor({"r": parameters})
    actor.reset({"r": candidate.Goal()})
    maximum_forced_error = 0.
    for tick in range(1, 501):
        angle = tick*.0031
        c, s = math.cos(angle), math.sin(angle)
        base = (.2*math.sin(angle), .1*math.cos(angle), -.3)
        goal = candidate.Goal(base, ((c,0.,-s), (0.,1.,0.), (s,0.,c)))
        output = actor.step(tick, {"r": goal}, {"r": (500.,100.,-200.)})["r"]
        forward_size = math.sqrt(s*s+c*c)
        expected = (base[0]+20*s/forward_size, base[1], base[2]+20*c/forward_size)
        error = math.dist(output.state.tip, expected)
        maximum_forced_error = max(maximum_forced_error, error)
        if error > 1e-10 or not all(math.isfinite(v) for row in (output.state.tip,output.state.velocity) for v in row):
            raise AssertionError("Analytic forced zero-cone solution failed")
    # The provisional tip is exactly the base, an undefined direction in the
    # original branch. Zero cone still has a well-defined permitted direction.
    collapsed = candidate.Actor({"r": candidate.Parameters(tip_mass=0., angle_limit=0.)})
    collapsed.reset({"r": candidate.Goal()})
    output = collapsed.step(1, {"r": candidate.Goal()}, {"r": (0.,0.,-20/(candidate.DT*candidate.DT))})["r"]
    if output.unconstrained_tip != (0.,0.,0.) or output.state.tip != (0.,0.,20.) or output.state.velocity != (0.,0.,0.):
        raise AssertionError("Zero-cone provisional collapse not handled analytically")
    result = {"format": "has_source_0x31_zero_cone_correction_1", "status": "ORIGINAL_FAILURE_REPRODUCED_EXACT_ZERO_CONE_CORRECTION_PASSES",
              "original_source_sha256": ORIGINAL_SHA,
              "corrected_source_sha256": hashlib.sha256((CODE/"candidate.py").read_bytes()).hexdigest(),
              "root_reproduction": rows, "forced_moved_rotated_zero_cone_cases": 500,
              "maximum_forced_tip_error": maximum_forced_error,
              "zero_cone_provisional_collapse_checked": True,
              "correction": "Exact angle_limit==0 analytic direction before acos/normalizing target difference; no tolerance waiver",
              "scope": "Mathematical candidate only; SDK/native apps not executed and native parity unqualified"}
    with output_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({"status": result["status"], "original_failures": rows["original"]["failures"], "corrected_failures": rows["corrected"]["failures"], "corrected_rest_max": rows["corrected"]["maximum_rest_displacement"], "forced_tip_max": maximum_forced_error}))


if __name__ == "__main__":
    main()
