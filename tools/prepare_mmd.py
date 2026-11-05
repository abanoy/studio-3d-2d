"""Prepare an MMD asset in a NEW directory using separately installed Blender/MMD Tools."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib
import time
from asset_audit import inspect, digest, safe_member


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--blender", default=os.environ.get("HYBRID_BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"))
    parser.add_argument("--mmd-tools", type=Path, default=Path(os.environ.get("HYBRID_MMD_TOOLS", str(Path.home() / "AppData/Roaming/Blender Foundation/Blender/5.1/extensions/user_default/mmd_tools"))))
    parser.add_argument("--scale", type=float, default=0.08)
    parser.add_argument("--shared-toons", type=Path, default=Path(r"C:\a\tools\mmd64\Data"))
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("--cancel-file", type=Path)
    args = parser.parse_args()
    try: result = prepare(args)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        result = {"ok": False, "error": str(error)}
    if args.status_file: args.status_file.write_text(json.dumps(result), encoding="utf-8")
    print(json.dumps(result))
    return 0 if result["ok"] else 1


def prepare(args):
    source = args.source.resolve(strict=True)
    if source.stat().st_size > 128 * 1024 * 1024: raise ValueError("MMD source exceeds128MiB")
    audit = inspect(source)
    if audit["kind"] not in ("pmx", "pmd"):
        raise ValueError("Only PMD/PMX are converted by this adapter; Source assets need their own adapter.")
    if not 0.0001 <= args.scale <= 100:
        raise ValueError("Scale must be between 0.0001 and 100")
    addon = args.mmd_tools.resolve(strict=True)
    manifest = tomllib.loads((addon / "blender_manifest.toml").read_text(encoding="utf-8"))
    if manifest.get("id") != "mmd_tools":
        raise ValueError("Select an installed MMD Tools package directory")
    dependencies = []
    for item in audit["texture_dependencies"]:
        if item.get("unsafe") or not item["present"]:
            raise ValueError("Missing or unsafe texture dependency: " + item["name"])
        relative = safe_member(item["name"])
        path = (source.parent / relative).resolve(strict=True)
        path.relative_to(source.parent)
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("Texture exceeds 64 MiB adapter limit")
        dependencies.append((relative, path, digest(path)))
    if len(dependencies) > 2048 or sum(path.stat().st_size for _, path, _ in dependencies) > 512 * 1024 * 1024:
        raise ValueError("MMD texture budget exceeded")
    if args.cancel_file and args.cancel_file.exists(): raise RuntimeError("Import cancelled before staging")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    native = output / "native"
    native.mkdir()
    shutil.copyfile(source, native / source.name)
    for relative, path, _ in dependencies:
        target = native / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target == native / source.name:
            raise ValueError("Texture collides with model source")
        if not target.exists(): shutil.copyfile(path, target)
    # MMD's shared toon ramp names are not part of the model's explicit texture table.
    # Stage only these ten known files, never an arbitrary folder or a global preference.
    for index in range(1, 11):
        name = f"toon{index:02}.bmp"
        toon = (args.shared_toons / name).resolve(strict=True)
        if toon.stat().st_size > 1024 * 1024: raise ValueError("Shared toon exceeds 1 MiB")
        dependencies.append(("shared-toons/" + name, toon, digest(toon)))
        shutil.copyfile(toon, output / name)
    request = {"source": str(native / source.name), "original_name": source.name,
               "sha256": audit["sha256"], "mmd_tools": str(addon), "scale": args.scale,
               "output": str(output), "audit": audit,
               "dependency_hashes": {name: sha for name, _, sha in dependencies},
               "addon_version": manifest["version"]}
    request_path = output / "conversion-request.json"
    request_path.write_text(json.dumps(request, ensure_ascii=True, indent=2), encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["BLENDER_USER_CONFIG"] = str(output / "blender-config")
    command = [args.blender, "--background", "--factory-startup", "--disable-autoexec", "--offline-mode",
               "--python-exit-code", "1", "--python", str(Path(__file__).with_name("blender_mmd_bridge.py")),
               "--", str(request_path)]
    with (output / "conversion.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=output, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        worker = {"blender_pid": process.pid}
        (output / "worker.json").write_text(json.dumps(worker), encoding="utf-8")
        start = time.monotonic()
        try:
            while process.poll() is None:
                if args.cancel_file and args.cancel_file.exists():
                    worker["cancelled_while_running"] = True
                    raise RuntimeError("MMD import cancelled; previous scene preserved")
                if time.monotonic() - start > 180: raise RuntimeError("MMD import timed out after180seconds")
                time.sleep(.1)
        finally:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
            worker.update(finished=True, exit_code=process.returncode)
            (output / "worker.json").write_text(json.dumps(worker), encoding="utf-8")

    if digest(source) != audit["sha256"] or any(digest(path) != sha for _, path, sha in dependencies):
        raise RuntimeError("Source/dependency changed during conversion; do not use this result.")
    if process.returncode or not (output / "scene.glb").is_file():
        raise RuntimeError(f"Blender conversion failed (exit {process.returncode}); see {output / 'conversion.log'}")
    if (output / "scene.glb").stat().st_size > 128 * 1024 * 1024:
        raise ValueError("Prepared GLB exceeds128MiB")
    return {"ok": True, "glb": str(output / "scene.glb")}


if __name__ == "__main__": raise SystemExit(main())
