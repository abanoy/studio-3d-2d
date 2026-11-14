"""UNRUN preparation only. Build a fresh diagnostic overlay/lock after lease release.

Never launches Python workers, Blender, Godot, installs, or changes main source.
The generated native runner remains separately explicit and root-reviewed.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
AMENDMENT = HERE.parent.parent/"source-jiggle-crosswalk-scene-amendment/20261114T0225"
CANDIDATE_SHA = "718e5a6390e4406e7da77c966667a915de06d9d9e56a1072f92db93fcd03a770"
JUNKO = "8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716"
PYTHON = Path(r"C:\Program Files\Python313\python.exe")
PYTHONW = Path(r"C:\Program Files\Python313\pythonw.exe")
BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
PIN = "fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
REVIEWED_REVISION = "80a1e557512902b29b5fb95b3152bb4284fdf55e"


def require(ok, message):
    if not ok: raise ValueError(message)


def no_reparse(path):
    for value in [path, *path.parents]:
        try: info = value.lstat()
        except FileNotFoundError: continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400, "Reparse path refused")


def identity(path):
    no_reparse(path); before = path.stat()
    require(path.is_file(), "Regular input file required")
    with path.open("rb") as stream: digest = hashlib.file_digest(stream, "sha256").hexdigest()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "Input changed during hashing")
    return dict(sha256=digest, bytes=before.st_size, mtime_ns=before.st_mtime_ns)


def tree(folder):
    no_reparse(folder); result = {}
    for base, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs+files: no_reparse(Path(base)/name)
        dirs[:] = sorted(name for name in dirs if name not in {".git", "__pycache__"})
        for name in sorted(files):
            if not name.endswith((".pyc", ".pyo")):
                path = Path(base)/name; result[str(path)] = identity(path)
        require(len(result) <= 10000, "Input tree exceeds bounded membership")
    return result


def main_sources(root):
    # Same functional roots/entries as the canonical runner: no extension
    # filter, so shaders, JSON, examples and launch.pyw are all included.
    result = {}
    for folder in ("src", "tests", "tools", "data", "examples"):
        for path in sorted((root/folder).rglob("*")):
            no_reparse(path)
            if path.is_file() and path.suffix != ".pyc" and "__pycache__" not in path.parts:
                result[str(path)] = identity(path)
    for name in ("project.godot", "main.tscn", "run.py", "launch.pyw"):
        result[str(root/name)] = identity(root/name)
    return result


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, allow_nan=False, indent=2); stream.write("\n")


def replace_once(text, old, new):
    require(text.count(old) == 1, "Bridge/protocol source anchor changed")
    return text.replace(old, new, 1)


def assignments(text, replacements):
    source = ast.parse(text); lines = text.splitlines(keepends=True); found = {}
    for node in source.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in replacements:
                    require(target.id not in found, "Duplicate protocol assignment")
                    found[target.id] = node
    require(set(found) == set(replacements), "Protocol assignment seam changed")
    for name, node in sorted(found.items(), key=lambda row: row[1].lineno, reverse=True):
        lines[node.lineno-1:node.end_lineno] = [name+" = "+replacements[name]+"\n"]
    result = "".join(lines); ast.parse(result); return result


def bridge_overlay(text):
    text = replace_once(text, "import source_mdl_snapshot\n", "import source_mdl_snapshot\nimport qualification_support\n")
    text = replace_once(text, "props_loaded = 0\n", "crosswalk_qualification = None\nprops_loaded = 0\n")
    text = replace_once(text, '    mdl = getattr(container, "mdl", None)\n',
                        '    mdl = getattr(container, "mdl", None)\n    crosswalk_qualification = qualification_support.Qualification(request, selected_mdl_capture, mdl, container, bpy)\n')
    old = '''bpy.ops.export_scene.gltf(filepath=str(out / "scene.glb"), export_format="GLB", use_selection=True,
                          export_animations=False, export_cameras=False, export_lights=True,
                          export_extras=False, export_yup=True, export_image_format="AUTO")'''
    new = '''if crosswalk_qualification is None:
    raise ValueError("Diagnostic conversion did not prove a Junko MDL container")
with crosswalk_qualification.export_context():
    bpy.ops.export_scene.gltf(filepath=str(out / "scene.glb"), export_format="GLB", use_selection=True,
        export_animations=False, export_cameras=False, export_lights=True,
        export_extras=False, export_yup=True, export_image_format="AUTO", export_skins=True,
        export_armature_object_remove=False, export_rest_position_armature=True,
        export_hierarchy_flatten_bones=False, export_hierarchy_flatten_objs=False,
        export_leaf_bone=False, export_gpu_instances=False, export_use_gltfpack=False,
        export_draco_mesh_compression_enable=False, export_def_bones=False)'''
    text = replace_once(text, old, new)
    text = replace_once(text, 'tag_lightmap_glb(out / "scene.glb", lightmap_report["materials"])\n',
                        'tag_lightmap_glb(out / "scene.glb", lightmap_report["materials"])\ncrosswalk_qualification.complete(selected_mdl_capture)\n')
    ast.parse(text); return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("main", "output", "input-stage", "mdl", "baseline-bundle"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--expected-root-revision", required=True)
    parser.add_argument("--prepare-only", action="store_true", required=True)
    args = parser.parse_args()
    root = args.main.resolve(strict=True); task = args.output.absolute()
    require(task.parent == root/"output" and re.fullmatch(r"crosswalk-qualification-[A-Za-z0-9_]+", task.name) and not task.exists(), "Use a new direct owned output task")
    no_reparse(task)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    require(revision == args.expected_root_revision == REVIEWED_REVISION, "Exact reviewed80 root checkpoint required")
    scope = ["src", "tests", "tools", "data", "examples", "project.godot", "main.tscn", "run.py", "launch.pyw"]
    changed = subprocess.check_output(["git", "diff", "HEAD", "--name-only", "--", *scope], cwd=root, text=True).splitlines()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "--", *scope], cwd=root, text=True).splitlines()
    require(not [n for n in changed+untracked if "__pycache__" not in Path(n).parts and not n.endswith(".pyc")], "Uncommitted functional source remains")
    stage = args.input_stage.resolve(strict=True); mdl = args.mdl.resolve(strict=True); baseline = args.baseline_bundle.resolve(strict=True)
    require(stage.is_relative_to(root/"output") and mdl.is_relative_to(stage) and mdl != stage and baseline.is_relative_to(root/"output"), "Use protected owned staged inputs/baseline")
    require(stage != root/"output" and baseline != root/"output" and not task.is_relative_to(stage) and not task.is_relative_to(baseline), "Protected input trees must exclude the new task")
    require(identity(mdl)["sha256"] == JUNKO and identity(AMENDMENT/"source_jiggle_crosswalk.py")["sha256"] == CANDIDATE_SHA, "Native/candidate identity differs")
    require((baseline/"scene.glb").is_file() and (baseline/"parameters.json").is_file(), "Existing baseline bundle required")
    require((baseline/"parameters.json").stat().st_size <= 256*1024, "Baseline report exceeds existing cap")
    base_parameters = json.loads((baseline/"parameters.json").read_bytes())
    base_native = base_parameters["native_parameters"]; base_jiggle = base_native.get("source_jiggle", {})
    require(base_parameters["source_sha256"] == JUNKO and base_parameters["scale"] == .01905 and
            "appearance_request" not in base_native and len(base_native["bones"]) == 69 and
            base_jiggle.get("status") == "retained_inert" and len(base_jiggle.get("rules", [])) == 49,
            "Require the current default Junko baseline with retained native values")
    protected = main_sources(root)
    require(len(protected) == 996, "Reviewed80 canonical functional catalogue count differs")
    main_members = sorted(protected)
    for path in (PYTHON, PYTHONW, BLENDER): protected[str(path)] = identity(path)
    native_before = tree(stage); baseline_before = tree(baseline)
    runtime = root/"output/dependencies"/("sourceio-"+PIN); runtime_before = tree(runtime)
    exporter = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\5.1\scripts\addons_core\io_scene_gltf2")
    exporter_before = tree(exporter)
    task.mkdir(); (task/"driver").mkdir(); (task/"overlay/tools").mkdir(parents=True)
    for source in sorted((root/"tools").glob("*.py")):
        shutil.copyfile(source, task/"overlay/tools"/source.name)
    (task/"overlay/tools/blender_source_bridge.py").write_text(bridge_overlay((root/"tools/blender_source_bridge.py").read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    shutil.copyfile(AMENDMENT/"source_jiggle_crosswalk.py", task/"overlay/tools/source_jiggle_crosswalk.py")
    shutil.copyfile(HERE/"qualification_support.py", task/"overlay/tools/qualification_support.py")
    old = root/"experiments/source_appearance/main_native_workers_20261113/shared/driver/wider-source"
    reference_sources = {str(path): identity(path) for path in sorted(old.glob("*.py"))}
    for name in ("background_python_bootstrap.py", "background_blender_observer.py", "win_desktop_attestation.py", "stage_resources.py"):
        shutil.copyfile(old/name, task/"driver"/name)
    stage_text = (task/"driver/stage_resources.py").read_text(encoding="utf-8")
    stage_text = replace_once(stage_text, 'sys.path.insert(0, str(CHECKOUT / "tools"))', 'sys.path.insert(0, str(TASK / "overlay/tools"))')
    (task/"driver/stage_resources.py").write_text(stage_text, encoding="utf-8", newline="\n")
    bg_text = (old/"background_route.py").read_text(encoding="utf-8")
    native_node = next(n for n in ast.parse(bg_text).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NATIVE_MODULES" for t in n.targets))
    roles = ast.literal_eval(native_node.value)
    roles["blender"] |= {"source_jiggle_metadata", "source_jiggle_values", "source_mdl_snapshot", "source_jiggle_crosswalk", "qualification_support"}
    worker_names = {"prepare_source", "blender_source_bridge", "source_appearance", "source_mdl_choices", "source_choice_io", "source_archive", *set.union(*roles.values())}
    workers = {str(task/"overlay/tools"/(name+".py")): identity(task/"overlay/tools"/(name+".py"))["sha256"] for name in sorted(worker_names)}
    required_node = next(n for n in ast.parse(bg_text).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "REQUIRED_SOURCES" for t in n.targets))
    bg_text = assignments(bg_text, {"PROTOTYPE": 'TASK / "overlay"', "INPUT_STAGE": "Path("+repr(str(stage))+")",
                                   "WORKER_SHA": repr(workers), "NATIVE_MODULES": repr(roles),
                                   "REQUIRED_SOURCES": "("+ast.unparse(required_node.value)+" | {str(PRIVATE)})"})
    (task/"driver/background_route.py").write_text(bg_text, encoding="utf-8", newline="\n")
    # Preserve the historical independent decoded geometry/skin/morph/image
    # verifier as data-only code, without importing its eleven-case driver.
    original_driver = (old/"background_conversion_driver.py").read_text(encoding="utf-8")
    function = next(n for n in ast.parse(original_driver).body if isinstance(n, ast.FunctionDef) and n.name == "glb_structure")
    (task/"overlay/tools/qualification_fingerprints.py").write_text('import hashlib,json\nimport secondary_helpers as H\nimport stage_resources as S\n\n'+ast.get_source_segment(original_driver, function)+'\n', encoding="utf-8", newline="\n")
    shutil.copyfile(HERE/"run_prepared.py", task/"driver/run_prepared.py")
    save(task/"empty-mount-plan.json", [])
    source_paths = set(workers) | {str(task/"overlay/tools"/(name+".py")) for name in set.union(*roles.values())}
    source_paths |= {str(task/"driver"/name) for name in ("background_route.py", "background_python_bootstrap.py", "background_blender_observer.py", "win_desktop_attestation.py", "stage_resources.py")}
    source_paths.add(str(root/"tools/private_desktop.py"))
    driver_before = tree(task/"driver"); overlay_before = tree(task/"overlay")
    frozen = {**protected, **native_before, **baseline_before, **runtime_before, **exporter_before,
              **reference_sources, **driver_before, **overlay_before, str(task/"empty-mount-plan.json"): identity(task/"empty-mount-plan.json")}
    lock = dict(format="has_Junko_crosswalk_qualification_lock_draft_1", root=str(root), task=str(task), root_revision=revision,
                mdl=str(mdl), input_stage=str(stage), baseline=str(baseline), files=frozen,
                native_members=sorted(native_before), runtime_members=sorted(runtime_before), baseline_members=sorted(baseline_before),
                main_members=main_members, canonical_functional_source_count=996,
                driver_members=sorted(driver_before), overlay_members=sorted(overlay_before),
                exporter_root=str(exporter), exporter_members=sorted(exporter_before),
                background_sources={path: identity(Path(path))["sha256"] for path in sorted(source_paths)},
                protocol_reference_sources=reference_sources, code_context="diagnostic_bridge_overlay_not_main_port",
                root_review="REQUIRED_before_execution", native_qualification="UNRUN")
    save(task/"fresh-input-lock.json", lock)
    require(all(identity(Path(path)) == value for path, value in frozen.items()), "Inputs changed while preparing")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == revision, "Root checkpoint changed while preparing")
    print(json.dumps({"task": str(task), "lock": identity(task/"fresh-input-lock.json"), "launched": False, "native_qualification": "UNRUN"}))


if __name__ == "__main__": main()
