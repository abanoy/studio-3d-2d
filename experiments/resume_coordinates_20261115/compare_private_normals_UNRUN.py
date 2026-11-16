"""UNRUN stdlib candidate joining a future private Blender capture to VVD/GLB.

No engine. Publishes aggregate errors and hashes only. Native vertex identity
remains a position/weight/UV-compatible multiset, with ambiguities disclosed.
"""
from pathlib import Path
from collections import defaultdict
from itertools import product
import argparse
import ast
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
MATCHER = ROOT / "experiments/source_appearance/native_coordinates_20261114/prove_coordinates_stdlib.py"
MATCHER_SHA = "f9afff684c82d601029f3a6a32d187a7df476d94b96bc39eff3abe2814c2723f"


def sha(data): return hashlib.sha256(data).hexdigest()
def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=CODE / "BLENDER_BOUNDARY_COMPARISON.json")
    args = parser.parse_args()
    private_path = args.private.resolve()
    output = args.output.resolve()
    require(Path.cwd().resolve() == ROOT and private_path.is_relative_to(ROOT / "output") and output.is_relative_to(CODE) and not output.exists(), "Root cwd, retained private input and fresh experiment result required")
    public_path = private_path.with_name("PUBLIC_CAPTURE.json")
    private_bytes = private_path.read_bytes()
    public_bytes = public_path.read_bytes()
    capture = json.loads(private_bytes)
    public = json.loads(public_bytes)
    require(capture["format"] == "has_private_blender_normal_intermediates_1" and public["format"] == "has_blender_normal_capture_1" and public["private_sha256"] == sha(private_bytes), "Capture identity mismatch")
    original = MATCHER.read_bytes()
    require(sha(original) == MATCHER_SHA, "Frozen matcher changed")
    text = original.decode("utf-8-sig").split("# Source SDK forward", 1)[0]
    initializer = "consumed=set();geometry_errors="
    anchor = "   actual=[0.,0.,0.];native_result=[0.,0.,0.]"
    require(text.count(initializer) == text.count(anchor) == 1, "Matcher anchors changed")
    text = text.replace(initializer, "diagnostic_export_rows=[]\n" + initializer, 1)
    text = text.replace(anchor, "   diagnostic_export_rows.append((tuple(pos),tuple(normal),tuple(uv),dict(wm),vi,ne))\n" + anchor, 1)
    ast.parse(text)
    namespace = {}
    exec(compile(text, str(MATCHER), "exec"), namespace)
    require(public["input_hashes"]["mdl"] == sha(namespace["raw"]) and public["input_hashes"]["vvd"] == sha(namespace["vvd"]) and public["input_hashes"]["glb"] == sha(namespace["glb"]) and public["input_hashes"]["parameters"] == sha(namespace["params_raw"]), "Capture did not measure the qualified exact inputs")
    mv, norm, dist = (namespace[name] for name in ("mv", "norm", "dist"))
    native_names = {row["name"]: index for index, row in enumerate(namespace["native"])}
    require(len(native_names) == 69, "Nonunique native names cannot identify groups in this diagnostic")
    buckets = defaultdict(list)
    corner_count = 0
    step = 1e-5
    for object_index, obj in enumerate(capture["objects"]):
        transform = [v for row in obj["object_matrix_world"] for v in row]
        normal_transform = obj["normal_transform"] or [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
        groups = obj["vertex_groups"]
        require(obj["corner_uv_active"] is not None, "Source profile requires UV0")
        for corner, vertex in enumerate(obj["corner_vertex_indices"]):
            point = mv(namespace["C"], mv(transform, obj["vertices"][vertex]))
            weights = defaultdict(float)
            for group, weight in obj["vertex_weights"][vertex]:
                if weight:
                    require(groups[group] in native_names, "Unknown weighted group in selected mesh")
                    weights[native_names[groups[group]]] += weight
            uv = obj["corner_uv_active"][corner]
            uv = (uv[0], 1.-uv[1])
            source_normal = obj["corner_normals_stored_snapshot"][corner]
            transformed = tuple(sum(normal_transform[r][k]*source_normal[k] for k in range(3)) for r in range(3))
            transformed = mv(namespace["C"], transformed, 0.)
            transformed = tuple(v/norm(transformed) for v in transformed) if norm(transformed) else (0., 1., 0.)
            predicted = obj["predicted_exporter_Y_up"][corner]
            require(all(math.isfinite(v) for row in (point, transformed, predicted, uv) for v in row), "Nonfinite private corner")
            buckets[tuple(round(v/step) for v in point)].append((point, dict(weights), uv, transformed, predicted, object_index, corner))
            corner_count += 1
    prediction_errors = []
    native_to_blender_errors = []
    blender_to_emitted_errors = []
    ambiguities = 0
    unmatched = 0
    for point, normal, uv, weights, native_vertex, raw_error in namespace["diagnostic_export_rows"]:
        center = tuple(round(v/step) for v in point)
        candidates = []
        for delta in product((-1, 0, 1), repeat=3):
            for entry in buckets.get(tuple(v+d for v, d in zip(center, delta)), ()):
                p, w, u, bnormal, predicted, object_index, corner = entry
                if dist(point, p) >= 2e-6 or dist(uv, u) >= 2e-6:
                    continue
                if max(abs(weights.get(k, 0.)-w.get(k, 0.)) for k in set(weights) | set(w)) >= 2e-6:
                    continue
                candidates.append((dist(normal, predicted), object_index, corner, bnormal))
        if not candidates:
            unmatched += 1
            continue
        ambiguities += len(candidates) > 1
        candidates.sort()
        predicted_error, _, _, blender_normal = candidates[0]
        native_normal = namespace["source_vertices"][native_vertex][1]
        prediction_errors.append(predicted_error)
        native_to_blender_errors.append(dist(native_normal, blender_normal))
        blender_to_emitted_errors.append(dist(blender_normal, normal))
    require(private_path.read_bytes() == private_bytes and public_path.read_bytes() == public_bytes and MATCHER.read_bytes() == original, "Capture/matcher changed while read")
    require(namespace["native_path"].read_bytes() == namespace["raw"] and namespace["native_path"].with_suffix(".vvd").read_bytes() == namespace["vvd"] and (namespace["B"] / "scene.glb").read_bytes() == namespace["glb"] and (namespace["B"] / "parameters.json").read_bytes() == namespace["params_raw"], "Native/standard inputs changed while analysed")
    count = len(namespace["diagnostic_export_rows"])
    def stats(values):
        return {"count": len(values), "max": max(values) if values else None,
                "mean": sum(values)/len(values) if values else None,
                "above_2e_5": sum(v > 2e-5 for v in values)}
    matched_pipeline = unmatched == 0 and len(prediction_errors) == count and max(prediction_errors) < 2e-6
    result = {"format": "has_blender_normal_boundary_comparison_1", "status": "COHERENT_BOUNDARY_MEASUREMENT" if matched_pipeline else "BOUNDARY_PREDICTION_OR_MATCH_FAILED",
              "normal_fidelity": "UNQUALIFIED; native 2e-5 gate unchanged, independently reported in NORMAL_DIAGNOSIS.json",
              "private_capture_sha256": sha(private_bytes), "public_capture_sha256": sha(public_bytes), "matcher_sha256": MATCHER_SHA,
              "captured_corners": corner_count, "exported_vertices": count, "matched_exported_vertices": len(prediction_errors),
              "unmatched_exported_vertices": unmatched, "multiple_corner_candidates": ambiguities,
              "exporter_stage_prediction_error": stats(prediction_errors), "native_to_stored_blender_normal_error": stats(native_to_blender_errors),
              "stored_blender_to_emitted_normal_error": stats(blender_to_emitted_errors),
              "identity_limit": "Geometry/weight/UV-compatible corners; nearest predicted-normal witness does not establish unique native vertex/corner identity",
              "causal_limit": "A saved Blender intermediate localizes the difference; it does not independently prove the exact custom fan encoder operation or capture the original SourceIO setter payload.",
              "native_runtime_launched_by_this_analysis": False, "private_arrays_published": False}
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"result": str(output), "status": result["status"], "matched": len(prediction_errors), "unmatched": unmatched}))


if __name__ == "__main__":
    main()
