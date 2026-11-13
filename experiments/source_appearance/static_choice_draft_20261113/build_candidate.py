"""Create output-only draft from the exact frozen working source, never run tools."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
BASE = "1236796865e677b150a2d7e2add20f2aac5325fe"
FILES = ("tools/prepare_source.py", "tools/blender_source_bridge.py", "src/source_import.gd",
         "tools/asset_audit.py", "tools/source_archive.py", "tools/source_content.py")

def stamp(path):
    stat = path.stat()
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns}

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError("Source seam is no longer unique: " + old[:80])
    return text.replace(old, new, 1)

def main():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != BASE:
        raise RuntimeError("Frozen HEAD differs")
    before = {}
    for name in FILES:
        raw = (ROOT / name).read_bytes()
        blob = subprocess.check_output(["git", "show", BASE + ":" + name], cwd=ROOT)
        if raw.replace(b"\r\n", b"\n") != blob.replace(b"\r\n", b"\n"):
            raise RuntimeError("Working source differs from commit: " + name)
        before[name] = stamp(ROOT / name)
    overlay = TASK / "overlay"
    overlay.mkdir(exist_ok=False)
    for name in FILES:
        target = overlay / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    (overlay / "tests").mkdir()
    prototype = ROOT / "experiments/source_appearance/overlay/tools/source_appearance.py"
    shutil.copy2(prototype, overlay / "tools/source_appearance.py")
    prepare = (overlay / "tools/prepare_source.py").read_text(encoding="utf-8")
    prepare = replace_once(prepare, "from asset_audit import digest, inspect", "from asset_audit import digest, inspect\nimport source_appearance")
    prepare = replace_once(prepare, "    p.add_argument(\"--status-file\", type=Path)",
        "    p.add_argument(\"--appearance\", type=Path, help=\"Source-bound static MDL appearance request\")\n"
        "    p.add_argument(\"--appearance-catalogue\", action=\"store_true\", help=\"Read bounded MDL49 appearance metadata only; no extraction or conversion\")\n"
        "    p.add_argument(\"--status-file\", type=Path)")
    prepare = replace_once(prepare, "    if args.catalog:\n", "    if args.appearance_catalogue:\n"
        "        if args.catalog or args.appearance:\n            raise ValueError(\"Choose one metadata mode without an appearance request\")\n"
        "        from source_choice_io import inspect_choices\n"
        "        result = inspect_choices(source, args.member or \"\")\n"
        "        if status_path:\n"
        "            if status_path.exists():\n                raise ValueError(\"Metadata result already exists\")\n"
        "            status_path.write_text(json.dumps({\"ok\": True, \"catalogue\": result}), encoding=\"utf-8\")\n"
        "        else:\n            print(json.dumps(result))\n"
        "        return 0\n"
        "    if args.catalog:\n")
    prepare = replace_once(prepare, "    sha = digest(source)\n", "    sha = digest(source)\n"
        "    appearance = source_appearance.load(args.appearance, sha) if args.appearance else None\n")
    prepare = replace_once(prepare, "    for provider in discovered[\"providers\"]:",
        "    if appearance is not None:\n"
        "        appearance = source_appearance.bind(appearance, sha, asset)\n"
        "    for provider in discovered[\"providers\"]:")
    prepare = replace_once(prepare, '    req = output / "conversion-request.json"',
        '    if appearance is not None:\n        request["appearance"] = appearance\n'
        '    req = output / "conversion-request.json"')
    (overlay / "tools/prepare_source.py").write_text(prepare, encoding="utf-8")
    bridge = (overlay / "tools/blender_source_bridge.py").read_text(encoding="utf-8")
    prototype_bridge = (ROOT / "experiments/source_appearance/overlay/tools/blender_source_bridge.py").read_text(encoding="utf-8")
    # Transfer only the reviewed feature seams; never replace the complete old worker.
    bridge = replace_once(bridge, "import hashlib\n", "import hashlib\nimport source_appearance\n")
    start = bridge.index("def load_model(")
    end = bridge.index("\n\nsource = Path(request[\"source\"])", start)
    proto_start = prototype_bridge.index("def load_model(")
    proto_end = prototype_bridge.index("\n\nsource = Path(request[\"source\"])", proto_start)
    bridge = bridge[:start] + prototype_bridge[proto_start:proto_end] + bridge[end:]
    bridge = replace_once(bridge, '    container = load_model(source, FileBuffer(TinyPath(str(source))), request["scale"])',
        '    appearance = request.get("appearance")\n'
        '    if appearance is not None:\n        appearance = source_appearance.bind(appearance, request["sha256"], source)\n'
        '    container = load_model(source, FileBuffer(TinyPath(str(source))), request["scale"], appearance=appearance)')
    bridge = replace_once(bridge, '    if native_physics:\n        native_parameters["source_physics"]=',
        '    if appearance is not None:\n        native_parameters.update(container.has_selected_appearance)\n'
        '        native_parameters["appearance_request"] = appearance\n'
        '    if native_physics:\n        native_parameters["source_physics"]=')
    bridge = replace_once(bridge, 'else:\n    from SourceIO.blender_bindings.source1.bsp.import_bsp import import_bsp',
        'else:\n    if request.get("appearance") is not None:\n'
        '        raise ValueError("Appearance choices apply only to one MDL model, not a BSP map")\n'
        '    from SourceIO.blender_bindings.source1.bsp.import_bsp import import_bsp')
    bridge = replace_once(bridge, '"Default skin/bodygroup only in GLB; all imported variants retained in editable.blend",',
        '"One selected static skin/bodygroup appearance in GLB; all imported variants retained in editable.blend; no runtime variant switching" if request.get("appearance") is not None else "Default skin/bodygroup only in GLB; all imported variants retained in editable.blend",')
    (overlay / "tools/blender_source_bridge.py").write_text(bridge, encoding="utf-8")
    receipt = {"format": "studio_output_draft_source_context_1", "base_revision": BASE,
        "source_files": before, "prototype_validator": stamp(prototype),
        "scope": "Unshipped source-only static choices draft; no runtime/conversion/native reads"}
    (TASK / "BASE_SOURCE_CONTEXT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    if {name: stamp(ROOT / name) for name in FILES} != before:
        raise RuntimeError("Main sources changed during copy")
    print(json.dumps({"base_revision": BASE, "copied": len(FILES), "main_preserved": True}))

if __name__ == "__main__":
    main()
