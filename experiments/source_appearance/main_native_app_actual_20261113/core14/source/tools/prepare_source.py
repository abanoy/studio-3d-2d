"""Prepare Source MDL/BSP or a resource-only GMA/legacy bin into the shared GLB contract."""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
import lzma

from asset_audit import digest, inspect
import source_appearance
from source_archive import stage_archive, resource_path
from source_paths import DEFAULT_GMOD, DEFAULT_WORKSHOP
from source_installation import conversion_context
from source_case import sidecars as loose_sidecars
from source_content import vpk_index, vpk_read, mount_paths

PIN = "fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
ROOT = Path(__file__).resolve().parent.parent
status_path = None
metadata_mode = False


def write_status(payload):
    # Metadata inspection must never overwrite an owner input or an earlier
    # result, including error paths. Default conversion status semantics stay.
    with status_path.open("x" if metadata_mode else "w", encoding="utf-8") as stream:
        json.dump(payload, stream)


def conversion_failure(log_path, returncode):
    """Keep a bounded worker exception actionable in the ordinary import UI."""
    reason = ""
    try:
        with Path(log_path).open("rb") as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - 16384))
            tail = stream.read(16384).decode("utf-8", "replace").replace("\r\n", "\n")
        matches = re.findall(r"^(?:ValueError|RuntimeError|ImportError|ModuleNotFoundError): ([^\r\n]{1,500})$", tail, re.MULTILINE)
        if matches: reason = matches[-1].rstrip("\r")
    except OSError:
        pass
    detail = (": " + reason) if reason else ""
    return f"Conversion failed (exit {returncode}){detail}; see {log_path}"


def main():
    global status_path, metadata_mode
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--catalog", action="store_true", help="List importable archive members as JSON without extraction")
    p.add_argument("--appearance", type=Path, help="Source-bound static MDL appearance request")
    p.add_argument("--appearance-catalogue", action="store_true", help="Read bounded MDL49 appearance metadata only; no extraction or conversion")
    p.add_argument("--status-file", type=Path)
    p.add_argument("--cancel-file", type=Path)
    p.add_argument("--member", help="Explicit models/...mdl or maps/...bsp within an archive")
    p.add_argument("--sourceio", type=Path, default=Path(os.environ.get("HYBRID_SOURCEIO", ROOT / "output/dependencies" / ("sourceio-" + PIN))))
    p.add_argument("--blender", default=os.environ.get("HYBRID_SOURCE_BLENDER", os.environ.get("HYBRID_BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")))
    p.add_argument("--gmod", type=Path, default=Path(os.environ.get("HYBRID_GMOD", DEFAULT_GMOD)))
    p.add_argument("--workshop", type=Path, default=Path(os.environ.get("HYBRID_GMOD_WORKSHOP", DEFAULT_WORKSHOP)))
    p.add_argument("--content", action="append", type=Path, default=[], help="Additional read-only content directory or _dir.vpk (repeatable)")
    p.add_argument("--mount-plan", type=Path, help="Explicit browser-selected dependency locations")
    p.add_argument("--mount-settings", type=Path, help="Saved extra roots and dependency checkbox overrides")
    p.add_argument("--scale", type=float, default=0.01905)
    args = p.parse_args()
    status_path = args.status_file
    metadata_mode = args.appearance_catalogue
    source = args.source.resolve(strict=True)
    if args.appearance_catalogue:
        if args.catalog or args.appearance:
            raise ValueError("Choose one metadata mode without an appearance request")
        from source_choice_io import inspect_choices
        result = inspect_choices(source, args.member or "")
        if status_path:
            if status_path.exists():
                raise ValueError("Metadata result already exists")
            write_status({"ok": True, "catalogue": result})
        else:
            print(json.dumps(result))
        return 0
    if args.catalog:
        if source.suffix.lower() == ".vpk":
            entries = vpk_index(source)
            result = {"models": [r["path"] for r in entries if r["path"].lower().endswith(".mdl")],
                      "maps": [r["path"] for r in entries if r["path"].lower().endswith(".bsp")]}
        elif source.suffix.lower() in {".mdl", ".bsp"}:
            result = {"models": [source.name] if source.suffix.lower() == ".mdl" else [],
                      "maps": [source.name] if source.suffix.lower() == ".bsp" else []}
        else:
            audit = inspect(source)
            result = {"models": [m["model"] for m in audit.get("models", [])], "maps": audit.get("maps", [])}
        print(json.dumps(result))
        return 0
    if not args.output:
        raise ValueError("--output is required for conversion")
    # Supplied standalone assets do not require a game installation. Installed
    # content retains its host checks; missing dependencies remain explicit.
    settings = {}
    if args.mount_settings:
        if args.mount_settings.stat().st_size > 1024 * 1024: raise ValueError("Mount settings exceed 1 MiB")
        settings = json.loads(args.mount_settings.read_text(encoding="utf-8"))
        if not isinstance(settings, dict): raise ValueError("Invalid mount settings")
        extra = settings.get("extra", [])
        overrides = settings.get("overrides", {})
        if not isinstance(extra, list) or len(extra) > 128 or not all(isinstance(p, str) for p in extra): raise ValueError("Invalid additional roots")
        if not isinstance(overrides, dict) or len(overrides) > 4096 or not all(isinstance(p, str) and isinstance(v, bool) for p, v in overrides.items()): raise ValueError("Invalid mount overrides")
    context = conversion_context(args.gmod, args.workshop, settings.get("extra", []), source)
    discovered = context["discovery"]
    addon = args.sourceio.resolve(strict=True)
    if not (addon / "library/utils/pylib").is_dir():
        raise ValueError("Select the documented pinned SourceIO source directory")
    if not 0.0001 <= args.scale <= 1:
        raise ValueError("Scale must be between 0.0001 and 1")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sha = digest(source)
    appearance = source_appearance.load(args.appearance, sha) if args.appearance else None
    staging = None
    case_resolved_sidecars = {}
    if source.suffix.lower() == ".vpk":
        entries = {r["path"].lower(): r for r in vpk_index(source)}
        member = resource_path(args.member or "")
        if not member.lower().endswith((".mdl", ".bsp")) or member.lower() not in entries:
            raise ValueError("Select an indexed MDL/BSP member of this VPK")
        native = output / "native"
        asset = native / member
        selected = [member]
        if member.lower().endswith(".mdl"):
            base = member[:-4]
            selected.extend(base + suffix for suffix in (".vvd", ".dx90.vtx", ".dx80.vtx", ".sw.vtx", ".vtx", ".phy", ".ani") if (base + suffix).lower() in entries)
        for name in selected:
            target = native / resource_path(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(vpk_read(source, entries[name.lower()]))
        mounts = [native, source]
    elif source.suffix.lower() in {".gma", ".bin"}:
        staging = stage_archive(source, output / "archive")
        (output / "staging.json").write_text(json.dumps(staging, indent=2), encoding="utf-8")
        choices = staging["models"] + staging["maps"]
        member = resource_path(args.member) if args.member else (choices[0] if len(choices) == 1 else None)
        if member not in choices:
            raise ValueError("Choose --member explicitly from: " + ", ".join(choices))
        native = Path(staging["root"])
        asset = native / member
        mounts = [native]
    elif source.suffix.lower() in {".mdl", ".bsp"}:
        native = output / "native"
        native.mkdir()
        # Keep the selected source and sidecars. Original materials remain read-only mounts.
        asset = native / source.name
        shutil.copyfile(source, asset)
        if source.suffix.lower() == ".mdl":
            for suffix, sidecar in loose_sidecars(source).items():
                managed_name = source.with_suffix(suffix).name
                shutil.copyfile(sidecar, native / managed_name)
                if sidecar.name != managed_name:
                    case_resolved_sidecars[managed_name] = sidecar.name
        content_root = next((parent.parent for parent in source.parents if parent.name.lower() in {"models", "maps"}), source.parent)
        mounts = [native, content_root]
    else:
        raise ValueError("Choose MDL, BSP, GMA or a legacy LZMA .bin; VMF is not supported")
    if appearance is not None:
        appearance = source_appearance.bind(appearance, sha, asset)
    for provider in discovered["providers"]:
        if provider["path"] in settings.get("overrides", {}): provider["enabled"] = settings["overrides"][provider["path"]] and provider["present"]
    if args.mount_plan:
        if args.mount_plan.stat().st_size > 1024 * 1024: raise ValueError("Mount plan exceeds 1 MiB")
        plan = json.loads(args.mount_plan.read_text(encoding="utf-8"))
        if not isinstance(plan, list) or len(plan) > 4096 or not all(isinstance(p, str) for p in plan): raise ValueError("Invalid mount plan")
        mounts.extend(Path(p).resolve(strict=True) for p in plan)
    else:
        mounts.extend(Path(p) for p in mount_paths(discovered, source))
    mounts.extend(path.resolve(strict=True) for path in args.content)
    for mount in mounts:
        if not mount.is_dir() and mount.suffix.lower() not in {".vpk", ".gma"}:
            raise ValueError("Dependencies must be directories, VPK indexes or GMA archives: " + str(mount))
    request = {"source": str(asset), "original_source": str(source), "sha256": sha,
               "source_profile": context["source_profile"],
               "sourceio": str(addon), "sourceio_revision": PIN, "output": str(output), "case_resolved_sidecars": case_resolved_sidecars,
               "gmod_installation": context["gmod_installation"], "sfm_installations": context["sfm_installations"],
               "workshop_root": str(args.workshop.resolve()),
               "source_member": args.member, "mount_discovery": discovered,
               "scale": args.scale, "mounts": list(dict.fromkeys(map(str, mounts)))}
    if appearance is not None:
        request["appearance"] = appearance
    req = output / "conversion-request.json"
    req.write_text(json.dumps(request, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", NO_BPY="1", BLENDER_USER_CONFIG=str(output / "blender-config"))
    command = [args.blender, "--background", "--factory-startup", "--disable-autoexec", "--offline-mode",
               "--python-exit-code", "1", "--python", str(Path(__file__).with_name("blender_source_bridge.py")), "--", str(req)]
    with (output / "conversion.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        (output / "worker.json").write_text(json.dumps({"blender_pid": process.pid}), encoding="utf-8")
        started = time.monotonic()
        try:
            while process.poll() is None:
                if args.cancel_file and args.cancel_file.exists():
                    raise RuntimeError("Source preparation cancelled; partial bundle retained")
                if time.monotonic() - started > 600:
                    raise RuntimeError("Source preparation timed out after 600 seconds")
                time.sleep(0.2)
        finally:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
    if digest(source) != sha:
        raise RuntimeError("Original input changed during conversion")
    if process.returncode or not (output / "scene.glb").is_file():
        raise RuntimeError(conversion_failure(output / 'conversion.log', process.returncode))
    if (output / "scene.glb").stat().st_size > 128 * 1024 * 1024:
        raise RuntimeError("Prepared GLB exceeds the studio's 128 MiB limit; retain bundle for simplification")
    print("Prepared:", output / "scene.glb", flush=True)
    print("Retain this entire bundle. Load scene.glb with Add model (MDL) or Scene (BSP).")
    if status_path:
        write_status({"ok": True, "glb": str(output / "scene.glb")})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, lzma.LZMAError, subprocess.SubprocessError) as error:
        if status_path:
            try:
                write_status({"ok": False, "error": str(error)})
            except OSError as status_error:
                print("Cannot write preparation result: " + str(status_error), file=sys.stderr)
        print(error, file=sys.stderr)
        raise SystemExit(1)
