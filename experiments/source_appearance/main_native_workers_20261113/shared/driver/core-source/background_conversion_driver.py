"""Explicit background conversion candidate with dual self-attestation. Default is preflight.

Real conversion requires root-reviewed input lock, --run-conversions and
--lease-confirmed. No app/GPU rendering, adoption, network or installation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
import stage_resources as S
import secondary_helpers as H
import background_route as BG

TASK, ROOT = S.TASK, S.CHECKOUT
PROTOTYPE = ROOT  # Actual current main worker, not a prototype copy.
INPUT_STAGE = ROOT / "output/sfm-next-cases-20261112/stage"
SOURCEIO = ROOT / "output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
PYTHON = Path(r"C:\Program Files\Python313\python.exe")
PYTHONW = Path(r"C:\Program Files\Python313\pythonw.exe")
BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
PRIVATE = ROOT / "tools/private_desktop.py"
PIN = "fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
WORKERS = {'tools/prepare_source.py': '2d23571e8bbcfe8c5cbde98bce006282c991f7c2e08670215bc552dc69b3c23e', 'tools/blender_source_bridge.py': 'e885074a2cb8c21976b25429e9c09c43c976eca760b835bc4b295fcac6185f4d', 'tools/source_appearance.py': '97b54184b92b391feb55f91c9308a89821574dd16f1f292318c13ed07a521f7b', 'tools/source_mdl_choices.py': 'a0f5e551ba9e2e38e3a92ca1d824a09311bf4ec4979a0d9947c128d15666e555', 'tools/source_choice_io.py': '7d193d4e29389f27483ce3670ce240433af526bd8e186b6851a581fb22e70640', 'tools/source_archive.py': '44fc9c9ca6d3b81aa34d72634f3a23d57624d0e96c57599f3c03b9e7af4cc131'}

ORDER = [("multi_skin_glove", "default-no-appearance"), ("keiki_tools_chisels", "default-no-appearance"),
         ("multi_skin_glove", "skin-0"), ("keiki_tools_chisels", "groups-000"),
         ("multi_skin_glove", "skin-1"), ("multi_skin_glove", "skin-2"),
         *[("keiki_tools_chisels", "groups-" + bits) for bits in ["001", "010", "011", "100", "101", "110"]],
         ("multi_skin_glove", "all-blank-refusal"), ("keiki_tools_chisels", "groups-111")]
REFUSAL = "Selected bodygroups contain no renderable geometry; keep at least one visible part"


def read_json(path, limit=4 * 1024 * 1024, expected_sha=None):
    S.no_reparse(path)
    S.require(path.stat().st_size <= limit, "Metadata exceeds byte budget: " + str(path))
    raw = path.read_bytes()
    if expected_sha is not None:
        S.require(hashlib.sha256(raw).hexdigest() == expected_sha, "Metadata byte hash differs: " + str(path))
    return json.loads(raw, object_pairs_hook=S.unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def normalized(path):
    return str(Path(path).absolute()).replace("\\", "/").rstrip("/").casefold()


def owned(path, base):
    path, base = Path(path).absolute(), Path(base).absolute()
    S.no_reparse(path)
    S.require(path != base and path.is_relative_to(base) and ".." not in path.parts, "Path escaped owned output: " + str(path))
    return path


def functional(root):
    data = read_json(TASK / "RESOURCE_PLAN.json")
    return {str(Path(path).relative_to(ROOT)).replace("\\", "/"): S.identity(Path(path))
            for path in data["protected_inputs_before_after"]
            if Path(path).is_relative_to(ROOT / "tools") or Path(path).is_relative_to(ROOT / "tests")}


def runtime_tree(root):
    result = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for value in dirs + files:
            S.no_reparse(Path(base) / value)
        dirs[:] = sorted(value for value in dirs if value not in {"__pycache__", ".git"})
        for value in sorted(files):
            path = Path(base) / value
            if path.suffix not in {".pyc", ".pyo"}:
                result[path.relative_to(root).as_posix()] = S.identity(path)
    S.require(1 <= len(result) <= 4096 and sum(row["bytes"] for row in result.values()) <= 512 * 1024 * 1024, "Pinned runtime exceeds source budget")
    return result


def staged_members(root):
    S.no_reparse(root)
    S.require(root.is_dir(), "Staged resource root is absent")
    result = []
    for base, dirs, files in os.walk(root, followlinks=False):
        for value in dirs + files:
            S.no_reparse(Path(base) / value)
        result.extend((Path(base) / value).relative_to(root).as_posix() for value in files)
        S.require(len(result) <= 4096, "Staged resource membership budget exceeded")
    return sorted(result)


def verify_stage_members(root, expected):
    S.require(staged_members(root) == expected, "Staged directory membership changed; unlisted resources are forbidden")


def head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def selection(case, variant):
    if variant == "default-no-appearance":
        return None
    if case == "multi_skin_glove":
        if variant in {"skin-0", "skin-1", "skin-2"}:
            return {"skin": int(variant[-1]), "bodygroups": {"0": 0}}
        S.require(variant == "all-blank-refusal", "Unknown glove variant")
        return {"skin": 0, "bodygroups": {"0": 1}}
    S.require(case == "keiki_tools_chisels" and re.fullmatch("groups-[01]{3}", variant), "Unknown chisels variant")
    return {"skin": 0, "bodygroups": {str(i): int(v) for i, v in enumerate(variant[-3:])}}


def catalogue(case):
    return {"skin_groups": case["skin_table"], "bodygroups": [
        {"index": group["index"], "name": group["name"], "choices": [
            {key: choice[key] for key in ["index", "name", "vertices", "blank"]} for choice in group["choices"]]}
        for group in case["actual_metadata"]["bodygroups"]], "default_skin_has_native_slot_identity": True}


def schedule(plan, arrays):
    S.require(arrays.get("format") == "has_sfm_future_owned_stage_commands_1", "Wrong command-array format")
    rows = arrays["commands"]
    indexed = {(row["case"], row["variant"]): row for row in rows}
    S.require(len(indexed) == len(rows) == 14 and set(indexed) == set(ORDER), "Exact fourteen command cases required")
    cases = {case["case"]: case for case in plan["cases"]}
    result = []
    for key in ORDER:
        row, case = indexed[key], cases[key[0]]
        args = row["command"]
        S.require(isinstance(args, list) and all(isinstance(value, str) for value in args) and len(args) >= 3, "Invalid command vector")
        S.require(normalized(args[0]) == normalized(PYTHON) and normalized(args[1]) == normalized(PROTOTYPE / "tools/prepare_source.py"), "Worker/Python command changed")
        source = INPUT_STAGE / row["case"] / case["native_member"]
        S.require(normalized(args[2]) == normalized(source), "Native command input changed")
        tail = args[3:]
        S.require(len(tail) % 2 == 0 and all(tail[i].startswith("--") for i in range(0, len(tail), 2)), "Invalid command options")
        options = dict(zip(tail[::2], tail[1::2]))
        expected = {"--output", "--sourceio", "--blender", "--mount-plan"}
        choose = selection(*key)
        if choose is not None:
            expected.add("--appearance")
        S.require(len(options) * 2 == len(tail) and set(options) == expected, "Duplicate or unexpected conversion option")
        S.require(normalized(options["--sourceio"]) == normalized(SOURCEIO) and normalized(options["--blender"]) == normalized(BLENDER), "Approved native runtime command changed")
        S.require(normalized(options["--mount-plan"]) == normalized(TASK / "empty-mount-plan.json"), "Mount plan changed")
        S.require(normalized(options["--output"]) == normalized(TASK / "native-conversions" / row["case"] / row["variant"]), "Historical candidate output changed")
        expected_success = choose is None or any(value == 0 for value in choose["bodygroups"].values())
        S.require(row["expected_prepare_success"] is expected_success, "Expected outcome changed")
        request_path = None
        if choose is not None:
            request_path = TASK / "requests" / (row["case"] + "-" + row["variant"] + ".json")
            S.require(normalized(options["--appearance"]) == normalized(request_path), "Request command changed")
            actual = read_json(request_path, 64 * 1024)
            expected_request = {"format": "studio_source_appearance_request_1", "source_sha256": case["native_mdl_sha256"],
                                "native_mdl_sha256": case["native_mdl_sha256"], **choose}
            S.require(actual == expected_request, "Request does not exactly match its reviewed native variant")
        result.append({"case": key[0], "variant": key[1], "source": str(source), "request": str(request_path) if request_path else None,
                       "selection": choose, "expected_success": expected_success})
    return result


def commands(row, index, run):
    case = owned(run / f"{index + 1:02d}-{row['case']}-{row['variant']}", run)
    bundle = case / "bundle"
    args = [str(PYTHON), "-B", "-u", str(PROTOTYPE / "tools/prepare_source.py"), row["source"],
            "--output", str(bundle), "--sourceio", str(SOURCEIO), "--blender", str(BLENDER),
            "--mount-plan", str(TASK / "empty-mount-plan.json"), "--gmod", str(case / "absent-gmod"),
            "--workshop", str(case / "absent-workshop")]
    if row["request"]:
        args += ["--appearance", row["request"]]
    # A fresh nonce/control hash is materialized by BG.prepare only on execution.
    return case, bundle, args, None


def verify_conversion_request(bundle, row, case):
    request = read_json(bundle / "conversion-request.json")
    source = Path(row["source"])
    expected_mounts = [bundle / "native", INPUT_STAGE / row["case"] / case["native_member"].split("/")[0]]
    S.require(normalized(request["original_source"]) == normalized(source)
              and normalized(request["source"]) == normalized(bundle / "native" / source.name)
              and request["sha256"] == case["native_mdl_sha256"] and request["source_member"] is None
              and normalized(request["output"]) == normalized(bundle) and normalized(request["sourceio"]) == normalized(SOURCEIO)
              and request["sourceio_revision"] == PIN and request["source_profile"] == "standalone"
              and not request["gmod_installation"], "Native worker request identity/profile differs")
    S.require([normalized(path) for path in request["mounts"]] == [normalized(path) for path in expected_mounts], "Native worker mounted unowned/installed content")
    if row["selection"] is None:
        S.require("appearance" not in request, "Default request branch changed")
    else:
        S.require(request["appearance"] == read_json(Path(row["request"]), 64 * 1024), "Appearance transport differs")
    return request, expected_mounts


def verify_parameters(parameters, row, case, native):
    S.require(parameters["source_sha256"] == case["native_mdl_sha256"] and parameters["source_member"] is None
              and parameters["sourceio_revision"] == PIN and parameters["source_profile"] == "standalone", "Preparation report provenance differs")
    saved = parameters["native_parameters"]
    S.require(saved["skin_groups"] == case["skin_table"], "Native skin catalogue differs")
    S.require(saved["bones"] == [{"name": bone["name"], "parent": bone["parent"]} for bone in native["bones"]], "Native bone catalogue differs")
    S.require(saved["flex_names"] == native["flex_names"], "Native flex descriptors differ")
    controllers = saved["flex_controllers"]
    S.require(len(controllers) == len(native["controllers"]) and all(
        {key: value[key] for key in ["name", "group", "min", "max"]} == {key: expected[key] for key in ["name", "group", "min", "max"]}
        and type(value.get("local_to_global")) is int for value, expected in zip(controllers, native["controllers"])), "Native controller catalogue differs")
    groups = case["actual_metadata"]["bodygroups"]
    S.require(set(saved["bodygroups"]) == {group["name"] for group in groups}, "Converted bodygroup names differ")
    for group in groups:
        converted = saved["bodygroups"][group["name"]]
        S.require(len(converted) == len(group["choices"]) and all(
            value is None if choice["blank"] else isinstance(value, str) and bool(value)
            for value, choice in zip(converted, group["choices"])), "Converted native blank/variant correspondence differs")
    selected = row["selection"] or {"skin": 0, "bodygroups": {str(group["index"]): 0 for group in groups}}
    numeric = {str(group["index"]): selected["bodygroups"].get(str(group["index"]), 0) for group in groups}
    named = {group["name"]: numeric[str(group["index"])] for group in groups}
    S.require(saved["selected_skin"] == selected["skin"] and saved["selected_bodygroup_indices"] == named, "Selected native appearance indices differ")
    if row["selection"] is not None:
        S.require(saved["selected_native_bodygroup_indices"] == numeric and saved["native_appearance_choices"] == catalogue(case)
                  and saved["appearance_request"] == read_json(Path(row["request"]), 64 * 1024), "Explicit native catalogue/request differs")
    else:
        S.require(not any(key in saved for key in ["selected_native_bodygroup_indices", "native_appearance_choices", "appearance_request"]), "Default native report branch changed")
    active = [saved["bodygroups"][name][index] for name, index in named.items() if saved["bodygroups"][name][index] is not None]
    S.require(len(active) == len(set(active)) and active, "Selected mesh ownership is ambiguous/empty")
    return active


def glb_structure(path, active_names, native):
    S.no_reparse(path)
    glb = H.GLB(path)
    doc = glb.doc
    S.require(not doc.get("animations") and not doc.get("cameras"), "Static conversion unexpectedly exports animation/cameras")
    nodes = doc.get("nodes", [])
    mesh_nodes = [node for node in nodes if "mesh" in node]
    S.require(sorted(node.get("name", "") for node in mesh_nodes) == sorted(active_names), "GLB selected mesh-node membership differs")
    parents = {}
    for parent, node in enumerate(nodes):
        for child in node.get("children", []):
            H.integer(child, len(nodes)); S.require(child not in parents, "GLB multiple node parents")
            parents[child] = parent
    native_names = {bone["name"] for bone in native["bones"]}
    joints_by_name = {}
    used_skins = {H.integer(node.get("skin"), len(doc.get("skins", []))) for node in mesh_nodes}
    for skin_index in sorted(used_skins):
        skin = doc["skins"][skin_index]
        joints = skin.get("joints", [])
        S.require(joints and len(set(joints)) == len(joints), "Invalid GLB joint list")
        binds = glb.accessor(skin["inverseBindMatrices"], "MAT4", maximum=4096)
        S.require(len(binds) == len(joints), "GLB inverse-bind count differs")
        for joint in joints:
            H.integer(joint, len(nodes))
            name = nodes[joint].get("name", "")
            S.require(name not in joints_by_name or joints_by_name[name] == joint, "Ambiguous GLB native joint names")
            joints_by_name[name] = joint
    S.require(native_names <= set(joints_by_name), "GLB lost native joint bindings")
    for bone in native["bones"]:
        node = joints_by_name[bone["name"]]
        visited = set()
        parent = parents.get(node)
        while parent is not None and nodes[parent].get("name") not in native_names:
            S.require(parent not in visited, "GLB parent cycle")
            visited.add(parent); parent = parents.get(parent)
        expected = native["bones"][bone["parent"]]["name"] if bone["parent"] >= 0 else None
        S.require((nodes[parent].get("name") if parent is not None else None) == expected, "GLB native parent hierarchy differs")
    for image in doc.get("images", []):
        S.require("uri" not in image and type(image.get("bufferView")) is int, "Expected embedded GLB image buffer")
        H.integer(image["bufferView"], len(doc.get("bufferViews", [])))
    def local_transform(node):
        if "matrix" in node:
            S.require(not any(key in node for key in ["translation", "rotation", "scale"])
                      and isinstance(node["matrix"], list) and len(node["matrix"]) == 16, "Invalid GLB matrix/TRS transform")
            return {"matrix": [H.finite(value) for value in node["matrix"]]}
        result = {}
        for key, default in [("translation", [0., 0., 0.]), ("rotation", [0., 0., 0., 1.]), ("scale", [1., 1., 1.])]:
            value = node.get(key, default)
            S.require(isinstance(value, list) and len(value) == len(default), "Invalid GLB rest transform")
            result[key] = [H.finite(component) for component in value]
        return result
    def chain(index):
        result, visited = [], set()
        while index is not None:
            S.require(index not in visited, "GLB rest-transform parent cycle")
            visited.add(index)
            node = nodes[index]
            result.append({"name": node.get("name", ""), "local_transform": local_transform(node)})
            index = parents.get(index)
        return result
    meshes, used_materials = [], set()
    for node in mesh_nodes:
        mesh = glb.ref("meshes", node["mesh"])
        S.require(type(node.get("skin")) is int, "Selected native mesh lost its skin")
        skin = glb.ref("skins", node["skin"])
        target_count = len(mesh.get("primitives", [{}])[0].get("targets", []))
        defaults = node.get("weights", mesh.get("weights", [0.] * target_count))
        S.require(isinstance(defaults, list) and len(defaults) == target_count, "GLB default morph-weight count differs")
        deformation = {"mesh_rest_chain": chain(nodes.index(node)),
                       "ordered_joints": [{"name": nodes[joint].get("name", ""), "rest_chain": chain(joint)} for joint in skin["joints"]],
                       "inverse_bind_matrices": glb.accessor(skin["inverseBindMatrices"], "MAT4", maximum=4096),
                       "effective_default_morph_weights": [H.finite(value) for value in defaults]}
        primitives = []
        for primitive in mesh.get("primitives", []):
            S.require(primitive.get("mode", 4) == 4, "Expected triangle primitive")
            attrs = primitive["attributes"]
            S.require({"POSITION", "JOINTS_0", "WEIGHTS_0"} <= set(attrs) and not ({"JOINTS_1", "WEIGHTS_1"} & set(attrs)), "Unsupported/missing native skin attributes")
            positions = glb.accessor(attrs["POSITION"], "VEC3")
            joints = glb.accessor(attrs["JOINTS_0"], "VEC4")
            weights = glb.accessor(attrs["WEIGHTS_0"], "VEC4")
            S.require(len(joints) == len(weights) == len(positions), "GLB skin attribute count differs")
            S.require(all(all(type(value) is int and 0 <= value < len(skin["joints"]) for value in row) for row in joints), "GLB vertex joint out of range")
            S.require(all(all(0 <= value <= 1 for value in row) and abs(sum(row) - 1) <= 1e-4 for row in weights), "GLB weights not normalized")
            indices = glb.accessor(primitive["indices"], "SCALAR", maximum=600000)
            S.require(len(indices) % 3 == 0 and all(type(row[0]) is int and 0 <= row[0] < len(positions) for row in indices), "GLB triangle indices out of range")
            decoded = {name: glb.accessor(index) for name, index in attrs.items()}
            S.require(all(len(values) == len(positions) for values in decoded.values()), "GLB vertex attribute count differs")
            morphs = []
            for target in primitive.get("targets", []):
                S.require(set(target) <= {"POSITION", "NORMAL", "TANGENT"}, "Unsupported morph semantic")
                morphs.append({name: glb.morph_delta(index, len(positions)) for name, index in target.items()})
            names = mesh.get("extras", {}).get("targetNames", [])
            S.require(len(names) == len(morphs) == target_count, "GLB target names/count differ")
            signature = hashlib.sha256(json.dumps({"attributes": decoded, "indices": indices, "morphs": morphs,
                                                    "target_names": names, "binding_rest_morph_defaults": deformation},
                                                   sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
            material = H.integer(primitive["material"], len(doc.get("materials", [])))
            used_materials.add(material)
            primitives.append({"vertices": len(positions), "indices": len(indices), "target_names": names,
                               "geometry_skin_morph_sha256": signature, "material": material,
                               "nonzero_position_morph_vertices": [sum(any(abs(value) > 1e-12 for value in delta) for delta in target.get("POSITION", [])) for target in morphs]})
        S.require(primitives, "Empty GLB mesh")
        meshes.append({"node": node["name"], "primitives": primitives, "binding_rest_morph_defaults": deformation})
    S.require(meshes and used_materials, "No GLB renderable mesh/material")
    active_materials = []
    for index in sorted(used_materials):
        material = doc["materials"][index]
        texture = material.get("pbrMetallicRoughness", {}).get("baseColorTexture", {})
        texture_row = glb.ref("textures", texture.get("index"))
        image = glb.ref("images", texture_row.get("source"))
        view = glb.ref("bufferViews", image["bufferView"])
        start, count = view.get("byteOffset", 0), view["byteLength"]
        active_materials.append({"index": index, "name": material.get("name", ""), "embedded_base_image_sha256": hashlib.sha256(glb.binary[start:start + count]).hexdigest()})
    return {"sha256": glb.sha, "bytes": len(glb.raw), "meshes": meshes, "native_joint_names_bound": sorted(native_names), "active_materials": active_materials,
            "scope": "Embedded GLB structure, decoded geometry/skin/morph fingerprints and native names/parents; no independent native vertex/material/deformation/render equivalence."}


def dependencies(bundle, parameters, glb, expected_mounts, native_missing, approved_sources):
    report = read_json(bundle / "dependencies.json")
    resolved = {}
    for row in report["resolved"]:
        name = S.safe_name(row["path"])
        key = name.casefold()
        S.require(key not in resolved and normalized(row["provider"]) in {normalized(root) for root in expected_mounts}, "Dependency used an ambiguous/unowned provider")
        source = Path(row["provider"]) / name
        approved = approved_sources.get(normalized(source))
        S.require(approved is not None and row["bytes"] == approved["bytes"] and row["sha256"] == approved["sha256"],
                  "Dependency input is not an approved staged resource or verified model copy")
        copy = owned(bundle / "resolved-native" / name, bundle / "resolved-native")
        for path in [source, copy]:
            value = S.identity(path)
            S.require(value["bytes"] == row["bytes"] and value["sha256"] == row["sha256"], "Resolved dependency bytes differ from owned source/copy")
        resolved[key] = row
    materials = parameters["materials"]
    active_names = {row["name"] for row in glb["active_materials"]}
    indexed = {}
    for row in materials:
        S.require(row["material"] not in indexed, "Ambiguous material report names")
        indexed[row["material"]] = row
    S.require(active_names <= set(indexed), "Active GLB material lacks preparation report")
    active_paths, inactive_paths = set(), set()
    for name, material in indexed.items():
        paths = {str(material["vmt"]).replace("\\", "/").casefold()}
        if material.get("base_texture"):
            paths.add(str(material["base_texture"]).replace("\\", "/").casefold())
        if name in active_names:
            S.require(material["status"] == "PBR approximation" and material.get("base_texture") and paths <= set(resolved), "Active material/texture is missing or fallback gray")
            active_paths.update(paths)
        else:
            inactive_paths.update(paths)
    missing = []
    for value in report["missing_requests"]:
        key = S.safe_name(value).casefold()
        classification = "active material input" if key in active_paths else "inactive material input" if key in inactive_paths else "optional lookup probe or unclassified request"
        missing.append({"path": value, "classification": classification})
    S.require(not any(row["classification"] == "active material input" for row in missing), "Missing active resource")
    return {"resolved_count": len(resolved), "all_resolved_providers_owned": True, "actual_missing_requests": missing,
            "active_materials": [indexed[name] for name in sorted(active_names)],
            "inactive_materials": [row for name, row in indexed.items() if name not in active_names],
            "native_preflight_missing_references": native_missing,
            "scope": "Actual converter requests and active/inactive PBR inputs; native unsupported map gaps remain separately reported."}


def refused(code, receipt, bundle, log, isolation):
    S.require(isolation.get("passed") and isolation.get("expected_worker_exit") == 1 and receipt.get("exit") == 1,
              "Expected refusal lacks verified dual background attestation")
    worker_log = bundle / "conversion.log"
    S.require(code == 1 and worker_log.is_file() and worker_log.stat().st_size <= 32 * 1024 * 1024, "Expected refusal process/log absent")
    text = worker_log.read_text(encoding="utf-8", errors="replace")
    S.require(REFUSAL in text and REFUSAL in log and "STUDIO_SOURCE_READY" not in text and not (bundle / "scene.glb").exists()
              and not (bundle / "parameters.json").exists(), "Failure was not the explicit all-blank geometry refusal")


def make_lock(path, revision, staging_path, closure_path):
    path = owned(path, TASK)
    S.require(path.parent == TASK and re.fullmatch(r"conversion-inputs-[A-Za-z0-9_]+\.json", path.name) and not path.exists(), "Choose a fresh direct conversion-inputs lock")
    S.require(re.fullmatch("[0-9a-f]{40}", revision or "") and head() == revision, "Bind the exact current checkpoint after source/test authoring")
    data = read_json(TASK / "CORE_FAMILIES.json", 8 * 1024 * 1024)["families"]
    manifest = read_json(TASK / "native-core-cases.json")
    resources = read_json(TASK / "RESOURCE_PLAN.json", 8 * 1024 * 1024)
    closure = read_json(TASK / "CORE_VMT_CLOSURE.json", 8 * 1024 * 1024)["cases"]
    S.require(manifest["format"] == "has_source_appearance_native_cases_1" and len(manifest["cases"]) == 14, "Exact core14 manifest required")
    entries = {(row["family"], row["variant"]): row for row in manifest["cases"]}
    S.require(set(entries) == set(ORDER), "Core schedule differs")
    rows = []
    for key in ORDER:
        entry = entries[key]; case = data[key[0]]["case_context"]; choose = selection(*key)
        source = INPUT_STAGE / key[0] / case["native_member"]
        S.require(normalized(entry["source"]) == normalized(source) and entry["use_override"] is (choose is not None), "Manifest worker/source branch differs")
        S.require(entry["skin"] == (choose or {"skin": 0})["skin"] and entry["bodygroups"] == (choose or {"bodygroups": {str(g["index"]): 0 for g in case["actual_metadata"]["bodygroups"]}})["bodygroups"], "Manifest selection differs")
        request = TASK / "requests" / (key[0] + "-" + key[1] + ".json") if choose is not None else None
        if request:
            expected = {"format": "studio_source_appearance_request_1", "source_sha256": case["native_mdl_sha256"], "native_mdl_sha256": case["native_mdl_sha256"], **choose}
            S.require(read_json(request) == expected, "Fresh request differs")
        rows.append({"case": key[0], "variant": key[1], "source": str(source), "request": str(request) if request else None,
                     "selection": choose, "expected_success": not entry["expect_all_blank"]})
    files = {}
    for row in resources["retained_resources"]:
        source = Path(row["path"]); actual = S.identity(source)
        S.require(actual == {key: row[key] for key in ("sha256", "bytes", "mtime_ns")}, "Fresh retained resource changed")
        files[str(source)] = actual
    S.require(len(files) == 296, "Wrong retained resource set")
    for source, expected in resources["original_archives"].items():
        files[source] = S.identity(Path(source)); S.require(files[source] == expected, "Original archive changed")
    source_scope = functional(ROOT)
    S.require(len(source_scope) == 17, "Main Python scope is not7port+10shared files")
    for name, observed in source_scope.items():
        source = ROOT / name; files[str(source)] = observed
        S.require(observed == resources["protected_inputs_before_after"][str(source)], "Main Python source changed after preparation")
    for source in [TASK / "RESOURCE_PLAN.json", TASK / "CORE_FAMILIES.json", TASK / "CORE_VMT_CLOSURE.json", TASK / "native-core-cases.json", TASK / "CORE_COMMANDS.json", TASK / "empty-mount-plan.json", PYTHON, PYTHONW, BLENDER, PRIVATE, Path(H.__file__).absolute(), Path(__file__).absolute(), *[Path(p) for p in BG.REQUIRED_SOURCES]]:
        files[str(source)] = S.identity(source)
    for row in rows:
        if row["request"]: files[row["request"]] = S.identity(Path(row["request"]))
    for name, expected in WORKERS.items(): S.require(files[str(ROOT / name)]["sha256"] == expected, "Current main worker differs")
    background_sources = BG.source_observation({source: files[source]["sha256"] for source in BG.REQUIRED_SOURCES})
    members = sorted(Path(source).relative_to(INPUT_STAGE).as_posix() for source in files if Path(source).is_relative_to(INPUT_STAGE))
    verify_stage_members(INPUT_STAGE, members)
    runtime = runtime_tree(SOURCEIO); S.require(runtime == resources["sourceio_tree"], "Pinned SourceIO tree changed")
    lock = {"format": "has_sfm_main_core_conversion_input_lock_1", "root_revision": revision,
        "source_context": "Actual main Python static-appearance working-source scope; sevenport+tenshared files, unrelatedmutableGD/tests excluded",
        "files": files, "staged_members": members, "background_sources": background_sources, "main_python_sources": source_scope,
        "sourceio_tree": runtime, "schedule": rows, "cases": [data[key]["case_context"] for key in ("multi_skin_glove", "keiki_tools_chisels")],
        "native": {key: data[key]["native_metadata"] for key in data}, "native_closure": closure,
        "limits": ["Fourteen main-worker conversions only; no app/render/nativefidelity acceptance.", "Nitori native hairbump missing and PBR additiveglow mismatch retained.", "Historical metadata joined only by exact selectedMDLhash; no old execution lock reused."]}
    S.save(path, lock)
    print(json.dumps({"lock": str(path), **S.identity(path), "native_conversion_run": False, "private_desktop_launched": False}), flush=True)

def check_lock(lock):
    S.require(lock["format"] == "has_sfm_main_core_conversion_input_lock_1" and head() == lock["root_revision"], "Fresh main checkpoint lock differs")
    verify_stage_members(INPUT_STAGE, lock["staged_members"])
    BG.source_observation(lock["background_sources"])
    changed = [source for source, expected in lock["files"].items() if S.identity(Path(source)) != expected]
    S.require(not changed, "Protected main/input/runtime changed: " + str(changed[:3]))
    S.require(functional(ROOT) == lock["main_python_sources"] and runtime_tree(SOURCEIO) == lock["sourceio_tree"], "ScopedmainPython/pinnedruntime changed")



def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-lock", "--prepare-inputs", dest="freeze_lock", type=Path, help="Prepare a fresh immutable input lock only; never launches a converter")
    parser.add_argument("--expected-root-revision")
    parser.add_argument("--staging-receipt", type=Path, default=TASK / "runs/execute-1794542752822327800/verification.json")
    parser.add_argument("--vmt-receipt", type=Path, default=TASK / "runs/vmt-closure-1794542959743314500/verification.json")
    parser.add_argument("--input-lock", type=Path)
    parser.add_argument("--lock-sha256")
    parser.add_argument("--output", type=Path, help="Fresh direct conversion-run-<nonce> child of this task")
    parser.add_argument("--run-conversions", action="store_true")
    parser.add_argument("--lease-confirmed", action="store_true")
    options = parser.parse_args(argv)
    if options.freeze_lock:
        S.require(not (options.run_conversions or options.lease_confirmed or options.input_lock or options.output), "Freeze mode cannot run or reuse an execution")
        make_lock(options.freeze_lock.absolute(), options.expected_root_revision, options.staging_receipt.absolute(), options.vmt_receipt.absolute())
        return
    S.require(options.input_lock and re.fullmatch("[0-9a-f]{64}", options.lock_sha256 or ""), "Supply a reviewed lock and its exact raw SHA256")
    S.require(not options.run_conversions or options.lease_confirmed, "Real conversions require the root's explicit lease")
    lock_path = owned(options.input_lock, TASK)
    lock = read_json(lock_path, 8 * 1024 * 1024, options.lock_sha256)
    check_lock(lock)
    run = options.output.absolute() if options.output else TASK / ("conversion-run-" + str(time.time_ns()))
    S.require(run.parent == TASK and re.fullmatch(r"conversion-run-[A-Za-z0-9_]+", run.name) and not run.exists(), "Execution/preflight output must be a fresh direct conversion-run child")
    S.no_reparse(run)
    run.mkdir(exist_ok=False)
    rows = lock["schedule"]
    S.require([(row["case"], row["variant"]) for row in rows] == ORDER, "Frozen schedule differs")
    candidate = [{"case": row["case"], "variant": row["variant"], "expected_success": row["expected_success"],
                  "native_command": commands(row, index, run)[2], "private_command": None,
                  "background_protocol": "Fresh per-case nonce/control materializes only on explicit execution; dual independent self-attestation required."} for index, row in enumerate(rows)]
    S.save(run / "candidate-commands.json", candidate)
    report = {"format": "has_sfm_main_core_native_conversion_background_1", "input_lock": str(lock_path), "lock_sha256": options.lock_sha256,
              "root_revision": lock["root_revision"], "mode": "execute" if options.run_conversions else "preflight-only",
              "results": [], "all_fourteen_passed": False, "run": str(run), "passed": False,
              "app_gpu_render_or_native_fidelity_acceptance": False, "automatic_cleanup": False}
    current_case = None
    try:
        if options.run_conversions:
            cases = {case["case"]: case for case in lock["cases"]}
            baseline = {}
            for index, row in enumerate(rows):
                check_lock(lock)
                case_folder, bundle, native_args, private_args = commands(row, index, run)
                case_folder.mkdir(exist_ok=False)
                current_case = {"case": row["case"], "variant": row["variant"], "folder": str(case_folder), "passed": False}
                S.require(not bundle.exists(), "Bundle must be fresh")
                environment = os.environ.copy()
                for name in ["PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "BLENDER_SYSTEM_SCRIPTS", "BLENDER_SYSTEM_DATAFILES", "BLENDER_SYSTEM_EXTENSIONS", "BLENDER_USER_RESOURCES"]:
                    environment.pop(name, None)
                environment.update(PYTHONDONTWRITEBYTECODE="1", NO_BPY="1")
                for name, relative in {"TEMP": "temp", "TMP": "temp", "APPDATA": "appdata", "LOCALAPPDATA": "localappdata",
                                       "BLENDER_USER_CONFIG": "blender-config", "BLENDER_USER_SCRIPTS": "blender-scripts",
                                       "BLENDER_USER_DATAFILES": "blender-datafiles", "BLENDER_USER_EXTENSIONS": "blender-extensions"}.items():
                    path = case_folder / relative
                    path.mkdir(exist_ok=True)
                    environment[name] = str(path)
                launch = BG.prepare(case_folder, native_args, lock["files"], lock["root_revision"], options.lock_sha256, BG.Win.capture_self())
                private_args = launch["private_command"]
                S.save(case_folder / "command.json", {"native": native_args, "private_wrapper": private_args,
                                                       "background_request_sha256": launch["request_sha256"],
                                                       "owned_environment": {key: value for key, value in environment.items() if value.startswith(str(case_folder))},
                                                       "creationflags": "CREATE_NO_WINDOW outer launcher; private wrapper creates suspended CREATE_NO_WINDOW child and kill-on-close job"})
                code, seconds = BG.run_outer(launch, case_folder, bundle, environment, lease_confirmed=options.lease_confirmed)
                S.save(case_folder / "exit.json", {"exit": code, "seconds": seconds})
                log = (case_folder / "process.log").read_text(encoding="utf-8", errors="replace")
                receipt = read_json(case_folder / "private-receipt.json")
                isolation = BG.verify_case(case_folder, launch, 0 if row["expected_success"] else 1, BG.Win.system_filetime())
                S.save(case_folder / "background-isolation-verification.json", isolation)
                case = cases[row["case"]]
                _, mounts = verify_conversion_request(bundle, row, case)
                result = {"case": row["case"], "variant": row["variant"], "expected_success": row["expected_success"], "exit": code,
                          "seconds": seconds, "folder": str(case_folder), "passed": False,
                          "background_isolation_receipt": S.identity(case_folder / "background-isolation-verification.json")}
                if not row["expected_success"]:
                    refused(code, receipt, bundle, log, isolation)
                    result["explicit_all_blank_refusal"] = True
                else:
                    S.require(code == 0 and "Prepared:" in log, "Native conversion failed or completion marker absent")
                    S.require(isolation["passed"] and isolation["expected_worker_exit"] == 0, "Background isolation did not verify")
                    parameters = read_json(bundle / "parameters.json")
                    native = lock["native"][row["case"]]
                    active = verify_parameters(parameters, row, case, native)
                    structure = glb_structure(bundle / "scene.glb", active, native)
                    native_missing = lock["native_closure"][row["case"]]["missing_native_references"]
                    approved_sources = {normalized(source): value for source, value in lock["files"].items()
                                        if Path(source).is_relative_to(INPUT_STAGE)}
                    for model in case["model_allowlist"]:
                        original = INPUT_STAGE / row["case"] / model["member"]
                        approved_sources[normalized(bundle / "native" / Path(model["member"]).name)] = lock["files"][str(original)]
                    dependency = dependencies(bundle, parameters, structure, mounts, native_missing, approved_sources)
                    result.update(parameters=S.identity(bundle / "parameters.json"), dependencies=S.identity(bundle / "dependencies.json"),
                                  glb_structure=structure, dependency_classification=dependency)
                    signatures = {mesh["node"]: sorted(primitive["geometry_skin_morph_sha256"] for primitive in mesh["primitives"]) for mesh in structure["meshes"]}
                    if row["variant"] == "default-no-appearance":
                        baseline[row["case"]] = signatures
                    else:
                        S.require(all(baseline[row["case"]].get(name) == digest for name, digest in signatures.items()), "Selected retained geometry/skin/morph fingerprints differ from default baseline")
                    S.save(case_folder / "glb-structure.json", structure)
                    S.save(case_folder / "dependency-classification.json", dependency)
                result["passed"] = True
                S.save(case_folder / "verification.json", result)
                report["results"].append(result)
                current_case = None
                print(("PASS ") + row["case"] + " / " + row["variant"], flush=True)
            report["all_fourteen_passed"] = len(report["results"]) == 14
        report["passed"] = not options.run_conversions or report["all_fourteen_passed"]
    except BaseException as error:
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        if current_case is not None:
            folder = Path(current_case["folder"])
            current_case["error"] = report.get("error", "Case did not finish")
            report["failed_case"] = current_case
            if not (folder / "verification.json").exists():
                S.save(folder / "verification.json", current_case)
            if not (folder / "exit.json").exists():
                private_path = folder / "private-receipt.json"
                child_exit = read_json(private_path).get("exit") if private_path.exists() else None
                S.save(folder / "exit.json", {"observed_private_child_exit": child_exit,
                                               "driver_error": current_case["error"], "note": "No exit status is invented if the wrapper receipt is absent."})
        try:
            check_lock(lock)
            report["protected_main_python_runtime_original_stage_request_inputs_unchanged"] = True
        except BaseException as error:
            report["preservation_error"] = str(error)
            report["protected_main_python_runtime_original_stage_request_inputs_unchanged"] = False
            report["passed"] = False
        report["lock_file_unchanged"] = S.identity(lock_path)["sha256"] == options.lock_sha256
        report["passed"] = report["passed"] and report["lock_file_unchanged"]
        S.save(run / "verification.json", report)
        print(json.dumps({key: report[key] for key in ["mode", "run", "passed", "all_fourteen_passed", "protected_main_python_runtime_original_stage_request_inputs_unchanged"]}), flush=True)
    S.require(report["passed"], "Driver did not pass; retain all partial evidence")


if __name__ == "__main__":
    main()
