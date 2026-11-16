"""Stdlib-only diagnosis; publishes aggregates, never source geometry or normals.

Run from the checkout root. Reuses the frozen independent native/glTF matcher,
stopping before its SDK/output section. This is not another runtime or reader.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
MATCHER = ROOT / "experiments/source_appearance/native_coordinates_20261114/prove_coordinates_stdlib.py"
MATCHER_SHA = "f9afff684c82d601029f3a6a32d187a7df476d94b96bc39eff3abe2814c2723f"
EPSILON = 2e-5


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=CODE / "NORMAL_DIAGNOSIS.json")
    output = parser.parse_args().output.resolve()
    if Path.cwd().resolve() != ROOT or not output.is_relative_to(CODE) or output.exists():
        raise ValueError("Run at checkout root with a new experiment-owned result path")
    original = MATCHER.read_bytes()
    if sha(original) != MATCHER_SHA:
        raise ValueError("Frozen independent matcher identity changed")
    text = original.decode("utf-8-sig").split("# Source SDK forward", 1)[0]
    initializer = "consumed=set();geometry_errors="
    anchor = "   actual=[0.,0.,0.];native_result=[0.,0.,0.]"
    if text.count(initializer) != 1 or text.count(anchor) != 1:
        raise ValueError("Frozen instrumentation anchors changed")
    text = text.replace(initializer, "diagnostic_rows=[]\n" + initializer, 1)
    instrumentation = '''   selected_normal=source_vertices[vi][1]
   require(abs(dist(normal,selected_normal)-ne)<1e-12,'selected normal/matched error mismatch')
   selected_unit=[v/norm(selected_normal)for v in selected_normal]
   rounded=[round(v,4)for v in selected_normal]
   rounded=[v/norm(rounded)for v in rounded]
   diagnostic_rows.append({'raw_error':ne,'unit_native_error':dist(normal,selected_unit),'native_length_error':abs(norm(selected_normal)-1),'export_length_error':abs(norm(normal)-1),'angular_error_degrees':angular(normal,selected_normal),'round4_normalize_prediction_error':dist(normal,rounded)})
'''
    text = text.replace(anchor, instrumentation + anchor, 1)
    ast.parse(text)
    namespace = {}
    exec(compile(text, str(MATCHER), "exec"), namespace)
    rows = namespace["diagnostic_rows"]
    if len(rows) != 9661 or len(namespace["consumed"]) != 9661:
        raise ValueError("Incomplete qualified matching")
    if max(row["raw_error"] for row in rows) <= EPSILON:
        raise ValueError("Historical normal failure no longer reproduced")
    input_bytes = {"native_mdl": namespace["raw"], "native_vvd": namespace["vvd"],
                   "standard_glb": namespace["glb"], "parameters": namespace["params_raw"]}
    input_paths = {"native_mdl": namespace["native_path"],
                   "native_vvd": namespace["native_path"].with_suffix(".vvd"),
                   "standard_glb": namespace["B"] / "scene.glb",
                   "parameters": namespace["B"] / "parameters.json"}
    inputs_unchanged = all(path.read_bytes() == input_bytes[key] for key, path in input_paths.items())
    if not inputs_unchanged or MATCHER.read_bytes() != original:
        raise ValueError("Read-only inputs changed during analysis")
    metrics = {}
    for key in rows[0]:
        values = sorted(row[key] for row in rows)
        metrics[key] = {"min": values[0], "max": values[-1], "mean": sum(values) / len(values),
                        "p50": values[len(values) // 2], "p99": values[int(len(values) * .99)],
                        "above_2e_5": sum(value > EPSILON for value in values)}
    result = {
        "format": "has_native_normal_boundary_diagnosis_1",
        "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_HEAD": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "status": "DIAGNOSIS_COMPLETE_NATIVE_NORMAL_GATE_STILL_FAILED",
        "normal_fidelity": "UNQUALIFIED; original 2e-5 gate is not relaxed or relabelled",
        "input_hashes": {key: sha(value) for key, value in input_bytes.items()},
        "matcher_sha256": MATCHER_SHA,
        "executed_read_only_prefix_sha256": sha(text.encode("utf-8")),
        "vertices_matched": len(rows),
        "attribute_equivalent_ambiguities": namespace["equivalent_ambiguities"],
        "native_vertex_identity": "Position/weight/UV-compatible multiset; nearest-normal tie break, not unique native vertex IDs",
        "metrics": metrics,
        "raw_failures_fixed_by_unit_normalization": sum(row["raw_error"] > EPSILON and row["unit_native_error"] <= EPSILON for row in rows),
        "round4_normalize_prediction_within_2e_7": sum(row["round4_normalize_prediction_error"] < 2e-7 for row in rows),
        "round4_normalize_prediction_within_2e_5": sum(row["round4_normalize_prediction_error"] < EPSILON for row in rows),
        "round4_only_unit_vector_distance_upper_bound": 2 * math.sqrt(3) * .00005,
        "findings": {
            "native_float_normals_already_unit": "Confirmed within 2.1083e-7; raw normalization is not the cause",
            "VVD_compressed_normal_hypothesis": "Refuted for this input's float32 normal records; no packed-normal decoder participates",
            "exporter_rounding": "Installed exporter rounds corner normals to 4 decimals, normalizes, transforms and normalizes before Y-up conversion",
            "rounding_sufficiency": "Round4+normalize closely predicts most rows but cannot explain the maximum discrepancy",
            "remaining_boundary": "Blender custom-normal fan encoding/decoding or mesh evaluation is a candidate; exact causal reproduction remains UNRUN"
        },
        "scope": {"stdlib_only": True, "production_modules_imported": False,
                  "apps_or_native_runtime_launched": False, "private_arrays_published": False,
                  "inputs_unchanged": inputs_unchanged, "production_files_changed": False,
                  "HAS_posed_or_runtime_normal_transport": "UNRUN", "native_artist_fidelity": "NOT_CLAIMED"},
        "scratch_attempt_preserved": "Initial interactive instrumentation read the final candidate's normal rather than the chosen vi; its output is invalid and was not accepted. Current code selects source_vertices[vi] and asserts agreement with stored ne."
    }
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"result": str(output), "status": result["status"], "normal_max": metrics["raw_error"]["max"],
                      "raw_failures": metrics["raw_error"]["above_2e_5"],
                      "round4_prediction_max_residual": metrics["round4_normalize_prediction_error"]["max"]}))


if __name__ == "__main__":
    main()
