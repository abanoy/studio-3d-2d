"""Actual static Source choices, native conversion and source-offline app persistence.

This opt-in Windows graphical test requires the root coordinator's exclusive lease.
It never downloads tools, executes model-supplied scripts, or edits supplied inputs.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import uuid
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from build_owner_review_snapshot import freeze_source
from source_installation import conversion_context

PIN = "fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
BAD = ("ERROR:", "FAIL ", "SCRIPT ERROR", "SHADER ERROR", "ObjectDB instances leaked",
       "unclaimed string names", "Pages in use exist at exit", "resources still in use")


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stamp(path):
    path = Path(path).resolve(strict=True)
    before = path.stat()
    digest = sha(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("File changed while recording: " + str(path))
    return dict(bytes=after.st_size, mtime_ns=after.st_mtime_ns, sha256=digest)


def tree(root):
    root = Path(root).resolve(strict=True)
    rows = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinks are not admitted in a native/runtime tree: " + str(path))
        if path.is_file():
            rows[path.relative_to(root).as_posix()] = stamp(path)
    return rows


def source_state():
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    names = sorted(n for n in set(names) if n and n.split("/")[0] not in {"output", ".godot", ".git", "__pycache__"}
                   and "__pycache__" not in Path(n).parts and not n.endswith(".pyc"))
    return dict(revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                files={n: stamp(ROOT / n) for n in names})


def runtime_state(environment):
    paths = {"python": Path(sys.executable), "pythonw": Path(sys.executable).with_name("pythonw.exe"),
             "godot": Path(environment["HYBRID_GODOT"]), "blender": Path(environment["HYBRID_SOURCE_BLENDER"]),
             "ffmpeg": Path(environment["HYBRID_FFMPEG"]),
             "ffprobe": Path(environment["HYBRID_FFMPEG"]).with_name("ffprobe.exe")}
    return {"executables": {name: {"path": str(path.resolve(strict=True)), **stamp(path)} for name, path in paths.items()},
            "sourceio_root": environment["HYBRID_SOURCEIO"], "sourceio_files": tree(environment["HYBRID_SOURCEIO"])}


def read_manifest(path):
    data = json.loads(path.read_bytes())
    if data.get("format") != "has_source_appearance_native_cases_1" or not isinstance(data.get("cases"), list) or not 1 <= len(data["cases"]) <= 64:
        raise ValueError("Expected one bounded has_source_appearance_native_cases_1 manifest")
    cases, roots = [], {}
    for index, value in enumerate(data["cases"]):
        if not isinstance(value, dict) or not isinstance(value.get("name"), str) or not value["name"]:
            raise ValueError("Each native case needs a nonempty name")
        source = Path(value["source"]).resolve(strict=True)
        resource_root = Path(value["resource_root"]).resolve(strict=True)
        if not source.is_file() or source.suffix.lower() != ".mdl" or not source.is_relative_to(resource_root) or not resource_root.is_dir() or resource_root == Path(resource_root.anchor):
            raise ValueError("A case requires a loose MDL inside an explicit complete resource_root")
        if value.get("member") != source.name:
            raise ValueError("Loose MDL member must match the exact source filename")
        if type(value.get("skin")) is not int or not 0 <= value["skin"] < 256 or type(value.get("use_override")) is not bool or type(value.get("expect_all_blank")) is not bool:
            raise ValueError("Invalid native choice indices/flags")
        groups = value.get("bodygroups")
        if not isinstance(groups, dict) or len(groups) > 256 or any(not isinstance(k, str) or not re.fullmatch(r"0|[1-9][0-9]*", k) or type(v) is not int or not 0 <= v < 256 for k, v in groups.items()):
            raise ValueError("Bodypart selections require canonical native numeric keys and integer indices")
        if not value["use_override"] and (value["skin"] != 0 or any(groups.values()) or value["expect_all_blank"]):
            raise ValueError("Opted-out baseline cannot request nondefault or all-blank choices")
        if value["expect_all_blank"] and not value["use_override"]:
            raise ValueError("All-blank refusal is an explicit UI selection")
        row = {key: value[key] for key in ["name", "member", "skin", "bodygroups", "use_override", "expect_all_blank"]}
        row.update(source=str(source), resource_root=str(resource_root), key=f"{index + 1:02d}-" + re.sub(r"[^A-Za-z0-9_-]+", "-", value["name"]).strip("-")[:48],
                   appearance_expected=value["use_override"] and (value["skin"] != 0 or any(groups.values())))
        for optional in ["pose_native_bone_index", "expected_meshes", "expected_morphs"]:
            if optional in value:
                row[optional] = value[optional]
        if "pose_native_bone_index" in row and (type(row["pose_native_bone_index"]) is not int or not 0 <= row["pose_native_bone_index"] < 4096):
            raise ValueError("Optional posing target requires an admitted native bone index")
        for optional in ["expected_meshes", "expected_morphs"]:
            if optional in row and (not isinstance(row[optional], list) or len(row[optional]) > 64 or any(not isinstance(x, dict) or not isinstance(x.get("name"), str) or not x["name"] or type(x.get("present")) is not bool for x in row[optional])):
                raise ValueError("Optional native-derived presence checks need exact names and boolean expectations")
        if row["expect_all_blank"] and any(key in row for key in ["pose_native_bone_index", "expected_meshes", "expected_morphs"]):
            raise ValueError("Refused cases cannot claim unrun adopted geometry/pose checks")
        cases.append(row)
        roots.setdefault(resource_root, None)
    if len({row["name"] for row in cases}) != len(cases):
        raise ValueError("Native case names must be distinct")
    return cases, roots


def private_receipt(path):
    receipt = json.loads(path.read_bytes())
    ok = receipt.get("format") == "studio_private_desktop_1" and receipt.get("exit") == 0 and all(receipt.get(k) is True for k in ["private_window_seen", "child_desktop_confirmed", "job_closed", "desktop_closed"]) and all(receipt.get(k) is False for k in ["foreground_child_observed", "desktop_switch_requested"])
    if not ok:
        raise RuntimeError("Private process did not close cleanly: " + str(path))
    return receipt


def case_checks(row):
    groups = len(row["bodygroups"]) if row["use_override"] else 0
    if row["expect_all_blank"]:
        return 8 + groups
    return 25 + groups + int(row["appearance_expected"]) + len(row.get("expected_meshes", [])) + len(row.get("expected_morphs", [])) + (8 if "pose_native_bone_index" in row else 0)


def result_binding(result, request, path, studio):
    if not isinstance(result, dict) or result.get("format") != "has_source_choices_native_app_result_1" or result.get("mode") != request["mode"] or result.get("failures") != 0:
        return False
    if Path(result.get("project_root", "")).resolve() != studio or Path(result.get("job_path", "")).resolve() != path or result.get("job_sha256") != sha(path):
        return False
    if result.get("source_manifest_sha256") != request["source_manifest_sha256"] or result.get("source_revision") != request["source_revision"]:
        return False
    if request["mode"] == "writer":
        actual = result.get("cases", [])
        if len(actual) != len(request["cases"]) or result.get("checks") != 1 + sum(case_checks(row) for row in request["cases"]):
            return False
        for observed, expected in zip(actual, request["cases"]):
            phases = ["metadata", "controls", "all_blank_refusal"] if expected["expect_all_blank"] else ["metadata", "controls", "conversion", "adoption", "undo", "redo", "reference_0", "reference_24", "packed_save", "packed_open_cached", "linked_save"]
            if observed.get("name") != expected["name"] or observed.get("checks") != case_checks(expected) or observed.get("failures") != 0 or observed.get("passed") is not True or observed.get("all_blank_refused") != expected["expect_all_blank"] or observed.get("conversion_started") != (not expected["expect_all_blank"]) or observed.get("completed_phases") != phases:
                return False
            if not expected["expect_all_blank"]:
                bundle = Path(observed.get("bundle", "")).resolve()
                if (bundle.parent != studio / "output/compatibility" or not bundle.name.startswith("source-")
                        or Path(observed.get("expected", "")).resolve() != Path(expected["folder"]) / "expected.json"
                        or Path(observed.get("parameters", "")).resolve() != bundle / "parameters.json"
                        or Path(observed.get("conversion_request", "")).resolve() != bundle / "conversion-request.json"):
                    return False
        return result.get("actual_source_dialog") is True and result.get("actual_native_conversion") is True
    modes = result.get("reader_modes", [])
    return (result.get("checks") == (34 if request.get("export_movie") else 30)
            and [row.get("mode") for row in modes] == ["packed", "linked"]
            and all(row.get("checks") == 14 and row.get("failures") == 0 and row.get("passed") is True and row.get("frames") == [0, 24] for row in modes)
            and result.get("actual_source_dialog") is False and result.get("actual_native_conversion") is False
            and bool(result.get("movie")) == bool(request.get("export_movie")))


def launch(module, studio, folder, request, environment):
    folder.mkdir(parents=True, exist_ok=False)
    request.update(format="has_source_choices_native_job_1", folder=str(folder))
    path = folder / "job.json"
    write(path, request)
    previous_engine = os.environ.get("HYBRID_GODOT")
    try:
        os.environ["HYBRID_GODOT"] = environment["HYBRID_GODOT"]
        args = module.command("tests/source_choices_native_smoke.gd", extra=["--audio-driver", "Dummy", "--log-file", str(folder / "engine.log"), "--", str(path)])
    finally:
        if previous_engine is None:
            os.environ.pop("HYBRID_GODOT", None)
        else:
            os.environ["HYBRID_GODOT"] = previous_engine
    if ("--receipt" not in args or Path(args[args.index("--path") + 1]).resolve() != studio
            or Path(args[0]).resolve() != Path(sys.executable).with_name("pythonw.exe").resolve()
            or Path(args[1]).resolve() != studio / "tools/private_desktop.py"
            or Path(args[args.index("--") + 1]).resolve() != Path(environment["HYBRID_GODOT"]).resolve()):
        raise RuntimeError("Graphical command did not select the owned snapshot/private desktop")
    receipt_path = Path(args[args.index("--receipt") + 1])
    write(folder / "command.json", args)
    process = subprocess.Popen(args, cwd=studio, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    execution_error = None
    try:
        stdout, stderr = process.communicate(timeout=request["watchdog_seconds"] + 45)
    except BaseException as exc:
        timed_out = isinstance(exc, subprocess.TimeoutExpired)
        execution_error = {"type": type(exc).__name__, "message": str(exc)}
        stdout, stderr = getattr(exc, "stdout", None) or b"", getattr(exc, "stderr", None) or b""
        try:
            if process.poll() is None:
                process.kill()
            stdout, stderr = process.communicate(timeout=20)
        except BaseException as cleanup:
            execution_error["cleanup"] = {"type": type(cleanup).__name__, "message": str(cleanup)}
    text = (stdout + stderr).decode("utf-8", "replace")
    (folder / "stdout.log").write_text(text, encoding="utf-8")
    engine = (folder / "engine.log").read_text(encoding="utf-8", errors="replace") if (folder / "engine.log").exists() else ""
    markers = [line for blob in [text, engine] for line in blob.splitlines() if any(token in line for token in BAD)]
    result_path = folder / "result.json"
    result = json.loads(result_path.read_bytes()) if result_path.is_file() else None
    record = dict(exit=process.returncode, timed_out=timed_out, retained_Popen_reaped=process.poll() is not None,
                  execution_error=execution_error, error_markers=markers, result=result, receipt_path=str(receipt_path), strict_result_binding=result_binding(result, request, path, studio))
    if receipt_path.is_file():
        record["receipt"] = json.loads(receipt_path.read_bytes())
    write(folder / "process-verification.json", record)
    if execution_error is not None or not record["retained_Popen_reaped"] or timed_out or process.returncode or markers or not record["strict_result_binding"]:
        raise RuntimeError("Actual native app case failed; retained at " + str(folder))
    private_receipt(receipt_path)
    return record


def movie_gate(movie, folder, environment):
    ffmpeg = environment["HYBRID_FFMPEG"]
    ffprobe = str(Path(ffmpeg).with_name("ffprobe.exe"))
    def capture(label, args):
        write(folder / (label + "-command.json"), args)
        try:
            process = subprocess.run(args, capture_output=True, timeout=45)
            stdout, stderr = process.stdout, process.stderr
        except subprocess.TimeoutExpired as exc:
            (folder / (label + ".stdout.log")).write_bytes(exc.stdout or b"")
            (folder / (label + ".stderr.log")).write_bytes(exc.stderr or b"")
            raise
        (folder / (label + ".stdout.log")).write_bytes(stdout); (folder / (label + ".stderr.log")).write_bytes(stderr)
        process.check_returncode(); return stdout
    media = json.loads(capture("ffprobe", [ffprobe, "-v", "error", "-count_frames", "-show_streams", "-of", "json", movie]))
    video = next(x for x in media["streams"] if x["codec_type"] == "video")
    if (video["codec_name"], video["width"], video["height"], video["r_frame_rate"], video["nb_read_frames"], float(video["duration"])) != ("h264", 1920, 1080, "24/1", "48", 2.0):
        raise RuntimeError("Wrong native cold movie dimensions/frame range")
    if not any(x["codec_type"] == "audio" and x["codec_name"] == "aac" for x in media["streams"]):
        raise RuntimeError("Cold movie is missing required AAC audio")
    decoded = folder / "decoded.wav"
    capture("audio-decode", [ffmpeg, "-v", "error", "-i", movie, "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(decoded)])
    with wave.open(str(decoded), "rb") as stream:
        samples = array.array("h", stream.readframes(stream.getnframes()))
    if sys.byteorder != "little":
        samples.byteswap()
    onset = next((i / 48000 for i, sample in enumerate(samples) if abs(sample) > 2000), None)
    rms = math.sqrt(sum(v * v for v in samples[52800:57600]) / 4800)
    if onset is None or abs(onset - 1.0) >= .002 or not 4000 < rms < 12000:
        raise RuntimeError("Cold native movie audio onset/level gate failed")
    return dict(movie=movie, movie_sha256=sha(movie), video=video, onset_seconds=onset, rms_at_1_1s=rms)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--lease-confirmed", action="store_true", help="Only after the root coordinator grants the exclusive graphical lease")
    opt = parser.parse_args()
    if os.name != "nt" or not opt.lease_confirmed:
        parser.error("This native Windows test requires an explicit exclusive private-desktop lease")
    manifest = opt.inputs_manifest.resolve(strict=True)
    cases, roots = read_manifest(manifest)
    folder = (opt.output or ROOT / "output/source-choices-native" / (str(time.time_ns()) + "-" + uuid.uuid4().hex[:8])).resolve()
    if not folder.is_relative_to((ROOT / "output").resolve()) or folder == (ROOT / "output").resolve() or folder.exists():
        raise ValueError("Use a fresh, strictly owned checkout/output directory")
    folder.mkdir(parents=True)
    studio = folder / "Studio"
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", HYBRID_PYTHON=str(Path(sys.executable).resolve()),
                       HYBRID_GODOT=os.environ.get("HYBRID_GODOT", r"C:\a\tools\Godot\Godot_v4.6-stable_win64.exe"),
                       HYBRID_SOURCEIO=os.environ.get("HYBRID_SOURCEIO", str(ROOT / "output/dependencies" / ("sourceio-" + PIN))),
                       HYBRID_SOURCE_BLENDER=os.environ.get("HYBRID_SOURCE_BLENDER", os.environ.get("HYBRID_BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")),
                       HYBRID_FFMPEG=os.environ.get("HYBRID_FFMPEG", r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"))
    engine = Path(environment["HYBRID_GODOT"])
    if engine.name.endswith("_console.exe"):
        environment["HYBRID_GODOT"] = str(engine.with_name(engine.name.replace("_console", "")))
    source_before = runtime_before = manifest_before = None
    originals = {}
    moved, writer, readers, media, errors = [], None, [], None, []
    snapshot_before = None; owned_before = None; package_before = {}; conversion_metadata = {}
    try:
        source_before = source_state(); runtime_before = runtime_state(environment); manifest_before = stamp(manifest)
        originals = {str(root): tree(root) for root in roots}
        write(folder / "source-before.json", source_before); write(folder / "runtimes-before.json", runtime_before); write(folder / "originals-before.json", originals)
        write(folder / "input-manifest.json", json.loads(manifest.read_bytes())); write(folder / "runtime-environment.json", {k: environment[k] for k in environment if k.startswith("HYBRID_")})
        write(folder / "manifest-admission.json", {"format": "has_source_choices_native_fresh_admission_1", "schema": "Only declared case control fields and explicit resource_root are admitted. Extra supplied original SHA/resource-lock fields are preserved in input-manifest.json but are not treated as historical pins.", "fresh_full_resource_tree_hashes": "originals-before.json", "per_case_expected_checks": {row["name"]: case_checks(row) for row in cases}, "writer_expected_checks": 1 + sum(case_checks(row) for row in cases), "reader_expected_checks": {"without_movie": 30, "with_movie": 34}})
        for original_root, inventory in originals.items():
            if len(inventory) > 10000 or sum(x["bytes"] for x in inventory.values()) > 2 * 1024**3:
                raise ValueError("Native family exceeds the explicitly bounded copy budget")
        copied_revision, frozen = freeze_source(ROOT, studio)
        if copied_revision != source_before["revision"] or frozen != {name: row["sha256"] for name, row in source_before["files"].items()}:
            raise RuntimeError("Snapshot source filenames/SHA do not bind to the recorded current-main source context")
        profile = "HAS Source Choices Native " + uuid.uuid4().hex
        (studio / "override.cfg").write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name=' + json.dumps(profile) + '\n', encoding="utf-8")
        frozen["override.cfg"] = sha(studio / "override.cfg")
        snapshot_before = {name: sha(studio / name) for name in frozen}
        if frozen != snapshot_before:
            raise RuntimeError("Snapshot bytes did not match current main")
        write(folder / "snapshot-source-before.json", snapshot_before)
        source_binding = dict(source_manifest_sha256=sha(folder / "snapshot-source-before.json"), source_revision=copied_revision)
        aliases = {}
        for index, root in enumerate(roots):
            target = folder / "inputs" / f"family-{index + 1:02d}"
            shutil.copytree(root, target, copy_function=shutil.copy2)
            if tree(target) != originals[str(root)]:
                raise RuntimeError("Complete owned native family copy differs")
            aliases[root] = target
        owned_before = tree(folder / "inputs"); write(folder / "owned-inputs-before.json", owned_before)
        absent_gmod, absent_workshop = folder / "absent-game", folder / "absent-workshop"
        for row in cases:
            old_root = Path(row["resource_root"]); old_source = Path(row["source"])
            row["source"] = str(aliases[old_root] / old_source.relative_to(old_root)); row["resource_root"] = str(aliases[old_root])
            row["folder"] = str(folder / "cases" / row["key"]); Path(row["folder"]).mkdir(parents=True)
            discovery = conversion_context(absent_gmod, absent_workshop, (), Path(row["source"]))["discovery"]
            row["mount_overrides"] = {provider["path"]: False for provider in discovery["providers"]}
        write(folder / "owned-cases.json", dict(format="has_source_appearance_native_cases_1", cases=cases))
        tone = folder / "tone.wav"
        with wave.open(str(tone), "wb") as stream:
            stream.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
            stream.writeframes(b"".join(int(12000 * math.sin(2 * math.pi * 1000 * i / 48000)).to_bytes(2, "little", signed=True) for i in range(24000)))
        spec = importlib.util.spec_from_file_location("source_choices_native_run_" + uuid.uuid4().hex, studio / "run.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        writer = launch(module, studio, folder / "writer", dict(mode="writer", cases=cases, tone=str(tone), absent_gmod=str(absent_gmod), absent_workshop=str(absent_workshop), watchdog_seconds=660 * len(cases) + 120, **source_binding), environment)
        if len(writer["result"]["cases"]) != len(cases) or any(not row.get("passed") for row in writer["result"]["cases"]):
            raise RuntimeError("Writer did not complete every requested native case")
        converted = [row for row in writer["result"]["cases"] if row.get("conversion_started")]
        if not converted:
            raise RuntimeError("At least one successful real conversion is required")
        for row in converted:
            request = json.loads(Path(row["conversion_request"]).read_bytes())
            planned = next(case for case in cases if case["name"] == row["name"])
            if Path(request["original_source"]).resolve() != Path(planned["source"]) or request["sha256"] != sha(planned["source"]) or Path(request["sourceio"]).resolve() != Path(environment["HYBRID_SOURCEIO"]).resolve():
                raise RuntimeError("Actual conversion request does not bind the admitted source/runtime")
            if any(not Path(mount).resolve().is_relative_to(folder / "inputs") and not Path(mount).resolve().is_relative_to(studio / "output/compatibility") for mount in request["mounts"]):
                raise RuntimeError("Conversion used an unowned installed fallback mount")
            bundle = Path(row["bundle"])
            expected_path = Path(row["expected"])
            destination = expected_path.parent / "conversion-metadata"
            destination.mkdir(exist_ok=False)
            paths = [bundle / name for name in ["conversion-request.json", "parameters.json", "worker.json", "conversion.log"]]
            paths += [bundle.with_name(bundle.name + suffix) for suffix in ["-result.json", "-appearance.json", "-mount-settings.json"]]
            for path in paths:
                if path.is_file():
                    conversion_metadata[str(path)] = stamp(path)
                    shutil.copy2(path, destination / path.name)
                    if stamp(destination / path.name) != conversion_metadata[str(path)]:
                        raise RuntimeError("Copied conversion metadata differs from the actual worker record")
        write(folder / "conversion-metadata-before.json", conversion_metadata)
        package_before = {str(path): stamp(path) for path in (folder / "cases").rglob("*") if path.is_file() and (path.suffix == ".has" or any(part.endswith(".assets") for part in path.parts))}
        write(folder / "packages-before-readers.json", package_before)
        # Only wholly new run-owned trees can be hidden. Linked HAS sidecars remain.
        transition = [folder / "inputs", studio / "output/compatibility", studio / "output/imports", folder / "writer/writer-cache", tone]
        write(folder / "offline-plan.json", [{"source": str(p), "offline": str(p.with_name(p.name + ".offline"))} for p in transition if p.exists()])
        for path in transition:
            offline = path.with_name(path.name + ".offline")
            if not path.exists():
                continue
            if not path.resolve().is_relative_to(folder) or not offline.resolve().is_relative_to(folder) or offline.exists():
                raise ValueError("Offline move escaped the fresh owned run")
            path.rename(offline); moved.append((path, offline))
        for index, row in enumerate(converted):
            request = dict(mode="reader", expected=row["expected"], export_movie=index == 0, watchdog_seconds=240, **source_binding)
            reader = launch(module, studio, folder / "readers" / f"{index + 1:02d}", request, environment)
            readers.append(reader)
            if index == 0:
                media = movie_gate(reader["result"]["movie"], folder / "readers/01", environment)
        if len(readers) != len(converted):
            raise RuntimeError("Not every converted case reached a cold reader")
    except BaseException as exc:
        errors.append(dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc()))
    finally:
        unreaped = []
        for record_path in folder.rglob("process-verification.json"):
            try:
                if json.loads(record_path.read_bytes()).get("retained_Popen_reaped") is not True:
                    unreaped.append(str(record_path))
            except BaseException:
                unreaped.append(str(record_path))
        if unreaped:
            errors.append(dict(phase="offline restore", message="Owned process cleanup is unproven; offline copies retained without moving", records=unreaped))
        for path, offline in (reversed(moved) if not unreaped else []):
            try:
                if path.exists() or not offline.resolve().is_relative_to(folder):
                    raise RuntimeError("Owned offline path was recreated or escaped; retained for review")
                offline.rename(path)
            except BaseException as exc:
                errors.append(dict(type=type(exc).__name__, message=str(exc), phase="offline restore"))
        gates = {}
        after = {}
        def capture(name, probe):
            value = probe(); after[name] = value; return value
        probes = {"main_sources_and_head": lambda: source_before is not None and capture("sources", source_state) == source_before,
                  "approved_runtimes": lambda: runtime_before is not None and capture("runtimes", lambda: runtime_state(environment)) == runtime_before,
                  "manifest": lambda: manifest_before is not None and capture("manifest", lambda: stamp(manifest)) == manifest_before,
                  "original_families": lambda: bool(originals) and capture("originals", lambda: {root: tree(root) for root in originals}) == originals,
                  "owned_native_copies": lambda: owned_before is not None and tree(folder / "inputs") == owned_before,
                  "snapshot_sources": lambda: snapshot_before is not None and {name: sha(studio / name) for name in snapshot_before} == snapshot_before,
                  "conversion_metadata": lambda: bool(conversion_metadata) and all(stamp(path) == expected for path, expected in conversion_metadata.items()),
                  "saved_packages_and_linked_assets": lambda: bool(package_before) and all(stamp(path) == expected for path, expected in package_before.items())}
        for name, probe in probes.items():
            try:
                gates[name] = bool(probe())
            except BaseException as exc:
                gates[name] = False; errors.append(dict(type=type(exc).__name__, message=str(exc), phase="preservation " + name))
        write(folder / "preservation-after.json", after)
        if "sources" in after:
            write(folder / "source-after.json", after["sources"])
        # Include every receipt that actually exists, even after failed attempts.
        receipt_files = sorted((studio / "output/private-desktop").glob("*.json")) if studio.exists() else []
        receipts = []
        for path in receipt_files:
            try:
                receipts.append({"path": str(path), "sha256": sha(path), "receipt": json.loads(path.read_bytes())})
            except BaseException as exc:
                errors.append(dict(type=type(exc).__name__, message=str(exc), phase="retained receipt read", path=str(path)))
        result = dict(format="has_source_choices_native_verification_1", source_context="main_working_source_snapshot", source_before=source_before,
                      folder=str(folder), passed=not errors and all(gates.values()) and writer is not None and len(readers) == len([r for r in writer["result"]["cases"] if r.get("conversion_started")]) and media is not None,
                      errors=errors, preservation=gates, writer=writer, readers=readers, movie=media, receipts=receipts,
                      original_families=originals, conversion_metadata=conversion_metadata, scope="Actual import-time static Source UI/conversion, Add/Undo/Redo, packed+linked cold persistence and one movie. Derived pixels only; no native Source shader/jiggle/assembly/artist fidelity claim.")
        write(folder / "verification.json", result)
    print(json.dumps(dict(folder=str(folder), passed=result["passed"], preservation=result["preservation"], errors=result["errors"], writer_checks=writer["result"]["checks"] if writer else None, reader_count=len(readers)), ensure_ascii=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
