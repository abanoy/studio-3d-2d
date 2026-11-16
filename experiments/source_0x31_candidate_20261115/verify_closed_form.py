"""Independent first-tick scalar oracle; no projection implementation copied."""
from pathlib import Path
import hashlib
import json
import math
import sys
import argparse
import re

sys.dont_write_bytecode = True
from candidate import Actor, Goal, Parameters

CODE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="")
    run_id = parser.parse_args().run_id
    if run_id and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id) is None:
        raise ValueError("Safe bounded run ID required")
    output_path = CODE / ("CLOSED_FORM" + ("-" + run_id if run_id else "") + ".json")
    if output_path.exists():
        raise ValueError("Fresh evidence path required")
    actor = Actor({"r": Parameters()})
    actor.reset({"r": Goal()})
    output = actor.step(1, {"r": Goal()}, {"r": (3., 4., 0.)})["r"]
    # dt=1/120; initial error and velocity vanish. Therefore acceleration is
    # (3,4,-20), v=(1/40,1/30,-1/6), p=(1/4800,1/3600,20-1/720).
    expected_force = (3., 4., -20.)
    expected_v = (1/40, 1/30, -1/6)
    expected_p = (1/4800, 1/3600, 20-1/720)
    q = math.sqrt(sum(x*x for x in expected_p))
    expected_final_p = tuple(20*x/q for x in expected_p)
    # Orthogonal tangent projection: v minus p*(v dot p)/(p dot p).
    component = sum(expected_v[i]*expected_p[i] for i in range(3)) / sum(x*x for x in expected_p)
    expected_final_v = tuple(expected_v[i]-component*expected_p[i] for i in range(3))
    measured = {"acceleration": output.acceleration, "unconstrained_velocity": output.unconstrained_velocity,
                "unconstrained_tip": output.unconstrained_tip, "constrained_tip": output.state.tip,
                "constrained_velocity": output.state.velocity}
    expected = dict(zip(measured, (expected_force, expected_v, expected_p, expected_final_p, expected_final_v)))
    errors = {key: math.dist(value, expected[key]) for key, value in measured.items()}
    if max(errors.values()) > 1e-12 or output.angle_projected:
        raise AssertionError("Independent rational first-tick oracle failed")
    # Separate moved-goal case: lateral errors1/10,-1/5; stiffness100,
    # giving(10,-20,-20). A +2 along error contributes no along-axis spring.
    moved = Actor({"r": Parameters(yaw_stiffness=100., pitch_stiffness=100., along_stiffness=987654.)})
    moved.reset({"r": Goal()})
    moved_output = moved.step(1, {"r": Goal((1/10, -1/5, 2.))})["r"]
    if math.dist(moved_output.acceleration, (10., -20., -20.)) > 1e-12:
        raise AssertionError("Independent moved-goal force oracle failed")
    result = {"format": "has_source_0x31_closed_form_1", "status": "PASSED_INDEPENDENT_RATIONAL_FIRST_TICK_ORACLES",
              "expected": expected, "measured": measured, "errors": errors,
              "moved_goal_expected_acceleration": [10., -20., -20.], "moved_goal_measured_acceleration": moved_output.acceleration,
              "candidate_sha256": hashlib.sha256((CODE/"candidate.py").read_bytes()).hexdigest(),
              "scope": "Synthetic rational scalar derivation only; SDK and native app not executed, artist parity unqualified"}
    with output_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({"status": result["status"], "max_error": max(errors.values())}))


if __name__ == "__main__":
    main()
