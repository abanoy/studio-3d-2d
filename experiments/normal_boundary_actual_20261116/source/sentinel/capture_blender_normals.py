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
import ctypes as C
from ctypes import wintypes as W
from contextlib import contextmanager
sys.dont_write_bytecode=True

import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from probe_support import check_lease, check_context_lock

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
    lease, files = check_lease(lease_path, __file__)
    head = lease["HEAD"]
    require(files["probe"] == Path(__file__).resolve(), "Probe path mismatch")
    require(safe_path(bpy.app.binary_path) == files["blender_exe"], "Wrong running Blender")
    require(safe_path(bpy.data.filepath) == files["blend"], "Wrong editable snapshot open")
    require(bpy.context.preferences.filepaths.use_scripts_auto_execute is False, "Auto-execution must be disabled")
    require(getattr(bpy.app,"online_access",None) is False,"Offline mode must be active")
    target = safe_path(lease["private_output_directory"])
    require(target.is_relative_to(ROOT / "output") and target.parent.is_dir() and not target.exists(), "Fresh private output path required")
    require("__pycache__" not in target.parts, "Unexpected private destination")
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render and not obj.hide_get()]
    require(len(objects) == 2, "Exact two-mesh saved profile required")
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
        # Keep raw transported read-back separately: normalization must not
        # erase vector-length information in the boundary comparator.
        transported_raw = corner_normals.copy()
        if normal_transform:
            transported_raw = np.matmul(transported_raw, np.array(normal_transform.transposed()))
        transported_raw[:, [1, 2]] = transported_raw[:, [2, 1]]
        transported_raw[:, 2] *= -1
        zero = ~predicted.any(axis=1)
        predicted[zero, 2] = 1
        predicted[:, [1, 2]] = predicted[:, [2, 1]]
        predicted[:, 2] *= -1
        uv = None
        require(len(mesh.uv_layers) == 1, "Exact single UV0 source profile required")
        if mesh.uv_layers.active:
            values = np.empty(len(mesh.loops) * 2, dtype=np.float32)
            mesh.uv_layers[0].uv.foreach_get("vector", values)
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
        require(all(np.isfinite(values).all() for values in (coordinates, corner_normals, transported_raw, rounded, after_normalize, predicted)), "Nonfinite capture")
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
                     "stored_normal_transport_Y_up_raw": transported_raw.tolist(),
                     "exporter_round4": rounded.tolist(), "exporter_normalized_float32": after_normalize.tolist(),
                     "predicted_exporter_Y_up": predicted.tolist(), "zero_replacement_count": int(zero.sum())})
    check_lease(lease_path,__file__)
    hashes_unchanged = all(digest(path) == lease["files"][name]["sha256"] for name, path in files.items())
    require(hashes_unchanged, "Locked inputs changed during capture")
    private = {"format": "has_private_blender_normal_intermediates_2", "HEAD": head,
               "blender_version": bpy.app.version_string, "blender_build_hash": bpy.app.build_hash.decode("ascii"),
               "numpy_version": np.__version__, "objects": rows,
               "sourceio_setter_payload": "NOT_OBSERVED_IN_ORIGINAL_CONVERSION; reconstruct through native VVD and qualified position/weight/UV multiset matching, retaining ambiguities",
               "captured_scene_state": "Saved pre-export editable.blend; corner_normals property read may compute Blender normals, but no explicit depsgraph evaluation or fresh native conversion performed"}
    private_bytes = (json.dumps(private, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    require(len(private_bytes) <= 64 * 1024 * 1024, "Private capture over 64 MiB")
    target.mkdir()
    (target / "PRIVATE_NORMALS.json").write_bytes(private_bytes)
    public = {"format": "has_blender_normal_capture_2", "status": "CAPTURE_COMPLETE_COMPARISON_UNRUN",
              "HEAD": head, "objects": len(rows), "vertices": total_vertices, "corners": total_corners,
              "private_bytes": len(private_bytes), "private_sha256": hashlib.sha256(private_bytes).hexdigest(),
              "input_hashes": {name: row["sha256"] for name, row in lease["files"].items()},
              "analysis_hashes": {name: row["sha256"] for name,row in lease["analysis_files"].items()},
              "lease_sha256": digest(lease_path),
              "full_source_commit": lease["full_context"]["expected_commit"],
              "inputs_unchanged": hashes_unchanged, "installed_sources_modified": False,
              "original_blend_saved": False, "exporter_invoked": False, "SourceIO_imported": False,
              "normal_fidelity": "UNQUALIFIED; native/Blender/emitted GLB comparison still required"}
    with (target / "PUBLIC_CAPTURE.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(public, handle, indent=2)
        handle.write("\n")
    print("HAS_NORMAL_CAPTURE " + json.dumps(public))


@contextmanager
def _hidden_placement_sentinel():
    """Own a hidden zero-size HWND; unchanged outer monitor proves its desktop.

    This is placement evidence for a background process, not Blender GUI or
    rendering evidence. Never shows/activates a window or changes a desktop.
    """
    if sys.platform != 'win32':
        raise RuntimeError('Hidden placement sentinel requires Windows')
    user=C.WinDLL('user32',use_last_error=True)
    kernel=C.WinDLL('kernel32',use_last_error=True)
    def api(lib,name,result,*arguments):
        value=getattr(lib,name);value.restype=result;value.argtypes=arguments;return value
    create=api(user,'CreateWindowExW',W.HWND,W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,W.HWND,W.HMENU,W.HINSTANCE,C.c_void_p)
    destroy=api(user,'DestroyWindow',W.BOOL,W.HWND)
    is_window=api(user,'IsWindow',W.BOOL,W.HWND)
    visible=api(user,'IsWindowVisible',W.BOOL,W.HWND)
    enabled=api(user,'IsWindowEnabled',W.BOOL,W.HWND)
    owner=api(user,'GetWindowThreadProcessId',W.DWORD,W.HWND,C.POINTER(W.DWORD))
    get_style=api(user,'GetWindowLongW',W.LONG,W.HWND,C.c_int)
    get_rect=api(user,'GetWindowRect',W.BOOL,W.HWND,C.POINTER(W.RECT))
    current_pid=api(kernel,'GetCurrentProcessId',W.DWORD)
    current_tid=api(kernel,'GetCurrentThreadId',W.DWORD)
    pid=int(current_pid());tid=int(current_tid())
    WS_POPUP=0x80000000;WS_DISABLED=0x08000000;WS_VISIBLE=0x10000000;WS_CHILD=0x40000000
    WS_EX_NOACTIVATE=0x08000000;WS_EX_TOOLWINDOW=0x00000080
    hwnd=None
    policy={'format':'has_hidden_background_desktop_placement_sentinel_1',
        'purpose':'Owned background-process desktop placement only; no Blender GUI or render assertion.',
        'class':'STATIC','requested_size_pixels':[0,0],'disabled':False,'noactivate_style':False,
        'toolwindow_style':False,'visible_at_creation':None,'visible_before_destruction':None,
        'owned_pid_and_thread_verified':False,'destroyed_in_finally':False,
        'show_or_activation_calls':False,'thread_desktop_switch_calls':False}
    def checked_owned():
        if not hwnd or not is_window(hwnd):raise RuntimeError('Owned placement HWND is unavailable')
        found=W.DWORD();thread=int(owner(hwnd,C.byref(found)))
        if int(found.value)!=pid or thread!=tid or int(current_tid())!=tid:
            raise RuntimeError('Placement HWND process/thread ownership differs')
    try:
        # A top-level system class; no parent, menu, WS_VISIBLE, message-only
        # parent or desktop-switch API. Startup lpDesktop remains authoritative.
        hwnd=create(WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW,'STATIC','HAS background capture placement',WS_POPUP|WS_DISABLED,0,0,0,0,None,None,None,None)
        if not hwnd:raise OSError(C.get_last_error(),'Create hidden placement HWND')
        checked_owned()
        style=int(get_style(hwnd,-16))&0xffffffff
        extended=int(get_style(hwnd,-20))&0xffffffff
        area=W.RECT()
        if not get_rect(hwnd,C.byref(area)):raise OSError(C.get_last_error(),'Read hidden placement rectangle')
        if style&(WS_POPUP|WS_DISABLED)!=(WS_POPUP|WS_DISABLED) or style&(WS_VISIBLE|WS_CHILD):
            raise RuntimeError('Placement HWND is not hidden disabled top-level popup')
        if extended&(WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW)!=(WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW):
            raise RuntimeError('Placement HWND activation/tool policy differs')
        if area.right!=area.left or area.bottom!=area.top or visible(hwnd) or enabled(hwnd):
            raise RuntimeError('Placement HWND must remain zero-size, hidden and disabled')
        policy.update(disabled=True,noactivate_style=True,toolwindow_style=True,
                      visible_at_creation=False,owned_pid_and_thread_verified=True)
        yield policy
    finally:
        if hwnd:
            checked_owned()
            policy['visible_before_destruction']=bool(visible(hwnd))
            if not destroy(hwnd):raise OSError(C.get_last_error(),'Destroy owned placement HWND')
            policy['destroyed_in_finally']=True
            if policy['visible_before_destruction']:
                raise RuntimeError('Placement HWND unexpectedly became visible')


def _main_with_placement_sentinel():
    # The original main remains byte-exact. Its numeric/private capture and
    # original public fields are unchanged; append placement policy only after
    # successful cleanup. A cleanup failure exits nonzero and remains a failure.
    require(getattr(bpy.app,'background',None) is True,'Actual Blender background mode required')
    with _hidden_placement_sentinel() as policy:
        main()
    policy['blender_background_verified']=True
    arguments=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser();parser.add_argument('--lease',type=Path,required=True)
    lease_path=safe_path(parser.parse_args(arguments).lease)
    lease,files=check_lease(lease_path,__file__)
    target=safe_path(lease['private_output_directory'])
    public_path=target/'PUBLIC_CAPTURE.json'
    public=json.loads(public_path.read_bytes())
    require('background_isolation_sentinel' not in public and policy['destroyed_in_finally'] is True,'Fresh cleaned sentinel metadata required')
    public['background_isolation_sentinel']=policy
    with public_path.open('w',encoding='utf-8',newline='\n') as handle:
        json.dump(public,handle,indent=2);handle.write('\n')
    print('HAS_NORMAL_ISOLATION_SENTINEL '+json.dumps(policy))

if __name__ == "__main__":
    _main_with_placement_sentinel()
