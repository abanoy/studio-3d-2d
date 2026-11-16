"""UNRUN candidate: read a copied approved editable.blend, capture intermediates.

Root must review this script and create a fresh post-full-PASS lease before use.
Invoke only on a private desktop with --disable-autoexec and --background.
Never saves a blend, imports SourceIO or invokes the exporter. It does not
explicitly evaluate a depsgraph; the root must still disable file auto-execution.
Its detailed result is private native-derived data and must stay out of Git.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess
import sys

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(value):
    path = Path(value)
    require(path.is_absolute(), "Absolute locked paths required")
    for ancestor in (path, *path.parents):
        if ancestor.exists():
            require(not ancestor.is_symlink() and not (getattr(ancestor.lstat(), "st_file_attributes", 0) & 0x400), "Reparse path refused")
    return path.resolve()


def matrix_rows(matrix):
    return [[float(value) for value in row] for row in matrix]


def normalized(values):
    result = values.copy()
    lengths = np.linalg.norm(result, axis=1, keepdims=True)
    np.divide(result, lengths, out=result, where=lengths != 0)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lease", type=Path, required=True)
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    lease_path = safe_path(parser.parse_args(arguments).lease)
    lease = json.loads(lease_path.read_bytes())
    require(lease.get("format") == "has_blender_normal_probe_lease_1" and
            lease.get("phase") == "ROOT_APPROVED_AFTER_FULL_PASS" and
            lease.get("full_terminal_status") == "PASS" and
            lease.get("root_authoritative_closure") is True and
            lease.get("publish_private_arrays") is False, "Fresh root post-PASS authority required")
    expires = datetime.datetime.fromisoformat(lease["expires_utc"].replace("Z", "+00:00"))
    require(datetime.datetime.now(datetime.timezone.utc) < expires, "Root lease expired")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(head == lease["HEAD"], "Lease source revision changed")
    files = {}
    required = {"blend", "mdl", "vvd", "glb", "parameters", "blender_exe", "probe", "exporter_extract", "exporter_constants", "sourceio_import", "full_receipt", "closure_receipt"}
    require(set(lease["files"]) == required, "Exact input/runtime/full/closure lock required")
    for name, row in lease["files"].items():
        path = safe_path(row["path"])
        require(path.is_file() and digest(path) == row["sha256"], "Locked file changed: " + name)
        files[name] = path
    require(files["probe"] == Path(__file__).resolve(), "Probe path mismatch")
    require(safe_path(bpy.app.binary_path) == files["blender_exe"], "Wrong running Blender")
    require(safe_path(bpy.data.filepath) == files["blend"], "Wrong editable snapshot open")
    require(bpy.context.preferences.filepaths.use_scripts_auto_execute is False, "Auto-execution must be disabled")
    target = safe_path(lease["private_output_directory"])
    require(target.is_relative_to(ROOT / "output") and target.parent.is_dir() and not target.exists(), "Fresh private output path required")
    require("__pycache__" not in target.parts, "Unexpected private destination")
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render and not obj.hide_get()]
    require(0 < len(objects) <= 32, "Bounded active mesh selection required")
    rows = []
    total_vertices = total_corners = 0
    for obj in objects:
        mesh = obj.data
        require(not mesh.shape_keys or not mesh.shape_keys.key_blocks, "Morph-normal export path outside this candidate")
        total_vertices += len(mesh.vertices)
        total_corners += len(mesh.loops)
        require(total_vertices <= 200000 and total_corners <= 1000000, "Capture budget exceeded")
        coordinates = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", coordinates)
        coordinates = coordinates.reshape((-1, 3))
        corners = np.empty(len(mesh.loops), dtype=np.int32)
        mesh.loops.foreach_get("vertex_index", corners)
        edge_indices = np.empty(len(mesh.loops), dtype=np.int32)
        mesh.loops.foreach_get("edge_index", edge_indices)
        corner_normals = np.empty(len(mesh.loops) * 3, dtype=np.float32)
        mesh.corner_normals.foreach_get("vector", corner_normals)
        corner_normals = corner_normals.reshape((-1, 3))
        rounded = np.round(corner_normals, 4)
        after_normalize = normalized(rounded)
        predicted = after_normalize.copy()
        armature = obj.find_armature()
        normal_transform = None
        if armature:
            local = armature.matrix_world.inverted_safe() @ obj.matrix_world
            normal_transform = armature.matrix_world.to_3x3() @ local.to_3x3().inverted_safe().transposed()
            predicted[:] = np.matmul(predicted, np.array(normal_transform.transposed()))
            predicted = normalized(predicted)
        zero = ~predicted.any(axis=1)
        predicted[zero, 2] = 1
        predicted[:, [1, 2]] = predicted[:, [2, 1]]
        predicted[:, 2] *= -1
        uv = None
        if mesh.uv_layers.active:
            values = np.empty(len(mesh.loops) * 2, dtype=np.float32)
            mesh.uv_layers.active.data.foreach_get("uv", values)
            uv = values.reshape((-1, 2)).tolist()
        custom = {"present": False}
        attribute = mesh.attributes.get("custom_normal")
        if attribute:
            custom = {"present": True, "data_type": attribute.data_type, "domain": attribute.domain, "count": len(attribute.data)}
            # This is optional introspection. An unexposed RNA payload must not
            # be mistaken for a reproduced short2 encode/decode trace.
            try:
                values = []
                for item in attribute.data:
                    value = getattr(item, "value", getattr(item, "vector", None))
                    require(value is not None, "Custom-normal payload not exposed")
                    values.append(list(value) if hasattr(value, "__iter__") else value)
                custom["values"] = values
                custom["payload_capture"] = "captured"
            except (TypeError, ValueError, AttributeError) as error:
                custom["payload_capture"] = "not_exposed_" + type(error).__name__
        require(all(np.isfinite(values).all() for values in (coordinates, corner_normals, rounded, after_normalize, predicted)), "Nonfinite capture")
        rows.append({"name": obj.name, "mesh_name": mesh.name, "object_matrix_world": matrix_rows(obj.matrix_world),
                     "armature_matrix_world": matrix_rows(armature.matrix_world) if armature else None,
                     "normal_transform": matrix_rows(normal_transform) if normal_transform else None,
                     "vertices": coordinates.tolist(), "corner_vertex_indices": corners.tolist(),
                     "corner_edge_indices": edge_indices.tolist(), "edges": [list(edge.vertices) for edge in mesh.edges],
                     "faces": [{"start": polygon.loop_start, "count": polygon.loop_total, "material": polygon.material_index, "smooth": polygon.use_smooth} for polygon in mesh.polygons],
                     "vertex_groups": [group.name for group in obj.vertex_groups],
                     "vertex_weights": [[[group.group, float(group.weight)] for group in vertex.groups] for vertex in mesh.vertices],
                     "corner_uv_active": uv, "custom_normal_attribute": custom,
                     "corner_normals_stored_snapshot": corner_normals.tolist(),
                     "exporter_round4": rounded.tolist(), "exporter_normalized_float32": after_normalize.tolist(),
                     "predicted_exporter_Y_up": predicted.tolist(), "zero_replacement_count": int(zero.sum())})
    hashes_unchanged = all(digest(path) == lease["files"][name]["sha256"] for name, path in files.items())
    require(hashes_unchanged, "Locked inputs changed during capture")
    private = {"format": "has_private_blender_normal_intermediates_1", "HEAD": head,
               "blender_version": bpy.app.version_string, "blender_build_hash": bpy.app.build_hash.decode("ascii"),
               "numpy_version": np.__version__, "objects": rows,
               "sourceio_setter_payload": "NOT_OBSERVED_IN_ORIGINAL_CONVERSION; reconstruct through native VVD and qualified position/weight/UV multiset matching, retaining ambiguities",
               "captured_scene_state": "Saved pre-export editable.blend; no depsgraph evaluation or fresh native conversion performed"}
    private_bytes = (json.dumps(private, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    require(len(private_bytes) <= 64 * 1024 * 1024, "Private capture over 64 MiB")
    target.mkdir()
    (target / "PRIVATE_NORMALS.json").write_bytes(private_bytes)
    public = {"format": "has_blender_normal_capture_1", "status": "CAPTURE_COMPLETE_COMPARISON_UNRUN",
              "HEAD": head, "objects": len(rows), "vertices": total_vertices, "corners": total_corners,
              "private_bytes": len(private_bytes), "private_sha256": hashlib.sha256(private_bytes).hexdigest(),
              "input_hashes": {name: row["sha256"] for name, row in lease["files"].items()},
              "inputs_unchanged": hashes_unchanged, "installed_sources_modified": False,
              "original_blend_saved": False, "exporter_invoked": False, "SourceIO_imported": False,
              "normal_fidelity": "UNQUALIFIED; native/Blender/emitted GLB comparison still required"}
    with (target / "PUBLIC_CAPTURE.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(public, handle, indent=2)
        handle.write("\n")
    print("HAS_NORMAL_CAPTURE " + json.dumps(public))


if __name__ == "__main__":
    main()
