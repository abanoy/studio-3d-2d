"""Scalar second-tick damping and world-gravity controls, independent of helpers."""
from pathlib import Path
from dataclasses import replace
import json
import math
import sys
import argparse
import hashlib
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
    output_path = CODE / ("DAMPING_GRAVITY" + ("-" + run_id if run_id else "") + ".json")
    if output_path.exists():
        raise ValueError("Fresh result required")
    base = Parameters()
    damped = Actor({"r": base})
    undamped = Actor({"r": replace(base, yaw_damping=0., pitch_damping=0.)})
    for instance in (damped, undamped):
        instance.reset({"r": Goal()})
        instance.step(1, {"r": Goal()}, {"r": (3., 4., 0.)})
    # First tick has zero initial velocity; its closed form is independent
    # of damping. Derive p1,v1 directly from the rational Euler coordinates.
    q = (1/4800, 1/3600, 20-1/720)
    q_length = math.sqrt(sum(v*v for v in q))
    p1 = tuple(20*v/q_length for v in q)
    u = (1/40, 1/30, -1/6)
    factor = sum(u[i]*q[i] for i in range(3)) / sum(v*v for v in q)
    v1 = tuple(u[i]-factor*q[i] for i in range(3))
    expected_damped = (-50*p1[0]-5*v1[0], -50*p1[1]-5*v1[1], -20.)
    expected_undamped = (-50*p1[0], -50*p1[1], -20.)
    d = damped.step(2, {"r": Goal()})["r"].acceleration
    n = undamped.step(2, {"r": Goal()})["r"].acceleration
    if math.dist(d, expected_damped) > 1e-12 or math.dist(n, expected_undamped) > 1e-12:
        raise AssertionError("Independent second-tick damping force failed")
    actual_difference = tuple(d[i]-n[i] for i in range(3))
    if math.dist(actual_difference, (-5*v1[0], -5*v1[1], 0.)) > 1e-12 or math.dist(d,n) < .1:
        raise AssertionError("Zero-damping control did not expose velocity damping")
    gravity_controls = []
    for angle in (-.7, 0., .7):
        c, s = math.cos(angle), math.sin(angle)
        goal = Goal(basis=((c,0.,-s), (0.,1.,0.), (s,0.,c)))
        actor = Actor({"r": base})
        actor.reset({"r": goal})
        acceleration = actor.step(1, {"r": goal})["r"].acceleration
        if acceleration != (0.,0.,-20.):
            raise AssertionError("Rotating the goal rotated world gravity")
        gravity_controls.append({"goal_rotation_y": angle, "acceleration": acceleration})
    result = {"format": "has_source_0x31_scalar_damping_gravity_1", "status": "PASSED_INDEPENDENT_SECOND_TICK_AND_WORLD_GRAVITY_CONTROLS",
              "candidate_sha256": hashlib.sha256((CODE/"candidate.py").read_bytes()).hexdigest(),
              "expected_damped": expected_damped, "actual_damped": d,
              "expected_undamped": expected_undamped, "actual_undamped": n,
              "damping_difference": actual_difference, "rotated_goal_gravity": gravity_controls,
              "scope": "Synthetic scalar mathematics; no SDK/native client/app executed"}
    with output_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({"status": result["status"], "max_error": max(math.dist(d, expected_damped), math.dist(n, expected_undamped))}))


if __name__ == "__main__":
    main()
