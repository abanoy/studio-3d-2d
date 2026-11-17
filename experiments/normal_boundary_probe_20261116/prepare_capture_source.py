"""Derive bounded capture successor from immutable UNRUN predecessor."""
from pathlib import Path
import ast
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/resume_coordinates_20261115/capture_blender_normals_UNRUN.py'


def main():
    text=OLD.read_text(encoding='utf-8')
    text=text.replace('import sys\n','import sys\nsys.dont_write_bytecode=True\n',1)
    text=text.replace('import numpy as np','import numpy as np\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom probe_support import check_lease, check_context_lock',1)
    begin=text.index('    lease = json.loads(lease_path.read_bytes())')
    end=text.index('    require(files["probe"]',begin)
    text=text[:begin]+'    lease, files = check_lease(lease_path, __file__)\n    head = lease["HEAD"]\n'+text[end:]
    text=text.replace('    require(bpy.context.preferences.filepaths.use_scripts_auto_execute is False, "Auto-execution must be disabled")','    require(bpy.context.preferences.filepaths.use_scripts_auto_execute is False, "Auto-execution must be disabled")\n    require(getattr(bpy.app,"online_access",None) is False,"Offline mode must be active")',1)
    text=text.replace('require(0 < len(objects) <= 32, "Bounded active mesh selection required")','require(len(objects) == 2, "Exact two-mesh saved profile required")',1)
    text=text.replace('        if mesh.uv_layers.active:\n            values', '        require(len(mesh.uv_layers) == 1, "Exact single UV0 source profile required")\n        if mesh.uv_layers.active:\n            values',1)
    text=text.replace('mesh.uv_layers.active.data.foreach_get("uv", values)','mesh.uv_layers[0].uv.foreach_get("vector", values)',1)
    text=text.replace('        zero = ~predicted.any(axis=1)', '''        # Keep raw transported read-back separately: normalization must not
        # erase vector-length information in the boundary comparator.
        transported_raw = corner_normals.copy()
        if normal_transform:
            transported_raw = np.matmul(transported_raw, np.array(normal_transform.transposed()))
        transported_raw[:, [1, 2]] = transported_raw[:, [2, 1]]
        transported_raw[:, 2] *= -1
        zero = ~predicted.any(axis=1)''',1)
    text=text.replace('(coordinates, corner_normals, rounded, after_normalize, predicted)', '(coordinates, corner_normals, transported_raw, rounded, after_normalize, predicted)',1)
    text=text.replace('"corner_normals_stored_snapshot": corner_normals.tolist(),','"corner_normals_stored_snapshot": corner_normals.tolist(),\n                     "stored_normal_transport_Y_up_raw": transported_raw.tolist(),',1)
    text=text.replace('    hashes_unchanged = all(', '    check_lease(lease_path,__file__)\n    hashes_unchanged = all(',1)
    text=text.replace('"format": "has_private_blender_normal_intermediates_1"','"format": "has_private_blender_normal_intermediates_2"',1)
    text=text.replace('"format": "has_blender_normal_capture_1"','"format": "has_blender_normal_capture_2"',1)
    text=text.replace('Saved pre-export editable.blend; no depsgraph evaluation or fresh native conversion performed','Saved pre-export editable.blend; corner_normals property read may compute Blender normals, but no explicit depsgraph evaluation or fresh native conversion performed',1)
    text=text.replace('"input_hashes": {name: row["sha256"] for name, row in lease["files"].items()},','"input_hashes": {name: row["sha256"] for name, row in lease["files"].items()},\n              "analysis_hashes": {name: row["sha256"] for name,row in lease["analysis_files"].items()},\n              "lease_sha256": digest(lease_path),\n              "full_source_commit": lease["full_context"]["expected_commit"],',1)
    ast.parse(text)
    target=HERE/'capture_blender_normals.py';target.write_text(text,encoding='utf-8',newline='\n')
    (HERE/'CAPTURE_SOURCE_PROVENANCE.json').write_text(json.dumps({'format':'normal_capture_source_successor_1','predecessor_sha256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'successor_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'Blender_parsed_or_executed':False,'changes':['Actual full/source/host/graphics-release interpretation before capture.','Current pinned layer.uv.foreach_get vector API; exact2meshes/UV0 profile.','Retain raw transported normals separately from normalized prediction.','Private/public schema2 and exact support/comparator pins.'],'old_failure_gate_2e_5_unchanged':True},indent=2)+'\n',encoding='utf-8')
    print(hashlib.sha256(target.read_bytes()).hexdigest())


if __name__=='__main__':main()
