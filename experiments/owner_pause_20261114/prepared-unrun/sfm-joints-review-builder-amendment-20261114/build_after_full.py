"""UNRUN preparation: copy a NEW review after a passed, released full run.

Filesystem and Git only. No app/native launch, install, delete, move, overwrite,
automatic cleanup or modification of any previous review/profile/recovery.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import time
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKSPACE = ROOT.parent
OLD_REVIEW = WORKSPACE/"HAS-Review-20261113-12071fe"
PIN = "fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
SOURCEIO = ROOT/"output/dependencies"/("sourceio-"+PIN)
NATIVE_RUN = ROOT/"output/sfm-bone-bindings-native-launch-20261114T033026205/run"
FUNCTIONAL = ("src", "tests", "tools", "data", "examples")
ENTRY = ("project.godot", "main.tscn", "run.py", "launch.pyw")
QUALIFIED_REVISION = "f380729cb170682068017b0d4c29b5f8425cdd14"
QUALIFIED_FULL = ROOT/"output/windows-canonical-bone-binding-20261114T040946652"
TEXT_SUFFIXES = {".py", ".pyw", ".gd", ".gdshader", ".tscn", ".tres", ".json", ".godot", ".cfg", ".uid", ".txt", ".md", ".svg"}
TEXT_PATHS = {"tests/blank", "tests/krita_fixture/has_fixture.desktop", "tools/docker/sourceio_metadata.Dockerfile",
              "tools/docker/sourceio_worker.Dockerfile", "tools/krita-runtime.Dockerfile"}


def need(condition, detail):
    if not condition: raise RuntimeError(detail)


def no_links(path):
    for item in (path, *path.parents):
        try: info = item.lstat()
        except FileNotFoundError: continue
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0)&0x400,
             "Link/reparse path refused: "+str(item))


def guarded(path, boundary, allow_boundary=False):
    path = Path(path).absolute(); boundary = Path(boundary).absolute()
    need(".." not in path.parts and (allow_boundary or path != boundary) and
         path.resolve().is_relative_to(boundary.resolve()), "Path escaped owned boundary")
    no_links(path); return path


def identity(path):
    no_links(path); before = path.stat(); need(path.is_file(), "Regular file required")
    with path.open("rb") as stream: digest = hashlib.file_digest(stream, "sha256").hexdigest()
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "Input changed while hashing")
    return {"bytes": after.st_size, "mtime_ns": after.st_mtime_ns, "sha256": digest}


def tree(folder):
    no_links(folder); result = {}
    for base, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs+files: no_links(Path(base)/name)
        for name in sorted(files):
            path = Path(base)/name
            result[path.relative_to(folder).as_posix()] = identity(path)
    return result


def exporter_sources(folder):
    result = {}
    for path in sorted(folder.rglob("*")):
        no_links(path)
        if path.is_file() and path.suffix != ".pyc" and "__pycache__" not in path.parts:
            result[path.relative_to(folder).as_posix()] = identity(path)
    return result


def source_map():
    paths = [p for name in FUNCTIONAL for p in (ROOT/name).rglob("*")
             if p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts]
    paths += [ROOT/name for name in ENTRY]
    return {p.relative_to(ROOT).as_posix(): identity(p)["sha256"] for p in sorted(paths)}


def load(path): return json.loads(path.read_bytes())


def git_blobs(revision, names):
    listing = subprocess.check_output(["git", "ls-tree", "-rz", revision, "--", *FUNCTIONAL, *ENTRY], cwd=ROOT)
    entries = {}
    for row in listing.split(b"\0"):
        if not row: continue
        metadata, path = row.split(b"\t", 1); mode, kind, oid = metadata.split(); name = path.decode("utf-8")
        if name in names:
            need(mode in (b"100644", b"100755") and kind == b"blob", "Unsupported committed functional entry")
            entries[name] = oid
    need(set(entries) == set(names), "Committed functional source membership differs")
    batch = subprocess.check_output(["git", "cat-file", "--batch"], input=b"".join(entries[n]+b"\n" for n in names), cwd=ROOT)
    result = {}; offset = 0
    for name in names:
        end = batch.index(b"\n", offset); oid, kind, size = batch[offset:end].split(); start = end+1; stop = start+int(size)
        need(oid == entries[name] and kind == b"blob" and stop < len(batch) and batch[stop:stop+1] == b"\n", "Invalid Git batch response")
        result[name] = batch[start:stop]; offset = stop+1
    need(offset == len(batch), "Unexpected trailing Git output")
    return result


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=True, allow_nan=False, indent=2); stream.write("\n")


def copy_new(source, target, boundary, expected):
    target = guarded(target, boundary); need(not target.exists(), "Copy destination already exists")
    need(identity(source) == expected, "Pinned copy source changed")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects the final target even if another creator races.
    with source.open("rb") as incoming, target.open("xb") as outgoing:
        shutil.copyfileobj(incoming, outgoing, 1024*1024)
    shutil.copystat(source, target, follow_symlinks=False)
    need(identity(target) == expected and identity(source) == expected, "Copied bytes/stamps differ")


def package_readback(path):
    with zipfile.ZipFile(path) as archive:
        rows = archive.infolist(); names = [row.filename for row in rows]
        need(len(rows) < 2000 and len(names) == len(set(names)) and sum(row.file_size for row in rows) <= 512*1024*1024,
             "Packed project exceeds bounded inventory")
        need(archive.getinfo("has.json").file_size <= 1024*1024 and archive.getinfo("project.json").file_size <= 1024*1024,
             "Packed metadata exceeds bound")
        header = json.loads(archive.read("has.json")); project = json.loads(archive.read("project.json"))
        need(header.get("storage") == "packed" and project.get("schema_version") == 4, "Expected packed schema4 project")
        need(set(names) == {"has.json"}|{row["path"] for row in header["payload"]}, "Unexpected packed members")
        for row in header["payload"]:
            name = row["path"]; parts = PurePosixPath(name)
            need(not parts.is_absolute() and ".." not in parts.parts and "\\" not in name and ":" not in name,
                 "Unsafe data-only archive member")
            item = archive.getinfo(name)
            need(not item.flag_bits&1 and item.compress_type in (0, 8) and item.file_size == row["bytes"], "Invalid packed declaration")
            digest = hashlib.sha256(); total = 0
            with archive.open(item) as stream:
                for chunk in iter(lambda: stream.read(1024*1024), b""): digest.update(chunk); total += len(chunk)
            need(total == row["bytes"] and digest.hexdigest() == row["sha256"], "Packed CRC/SHA readback differs")
        return {"packed": True, "all_payload_SHA_and_CRC_verified": True, "payload_files": len(header["payload"])}


def canonical_gate(folder, host_path, revision):
    folder = guarded(folder, ROOT/"output"); host_path = guarded(host_path, folder)
    state = load(folder/"state.json"); host = load(host_path)
    need(state.get("status") == "passed" and state.get("suite_exit") == 0 and state.get("source_unchanged") is True and
         state.get("source_commit") == revision, "Passed exact-revision complete suite required")
    need(host.get("format") == "has_canonical_authoritative_host_termination_1" and
         host.get("source_commit") == revision and host.get("canonical_run") == folder.name and
         host.get("coordinator_pid") == state["pid"] and host.get("expected_creation_utc") == state["process_started"] and
         all(host.get(k) is True for k in ("coordinator_absent", "python_absent", "owned_runtime_command_matches_absent", "no_process_killed")) and
         host.get("coordinator_matches") == [] and host.get("owned_runtime_matches") == [], "Authoritative exact full-run closure required")
    raw = folder/"authoritative-host-terminal.json"
    need(identity(raw)["sha256"] == host.get("raw_observation_sha256"), "Raw host observation binding differs")
    before = load(folder/"source-before.json"); after = load(folder/"source-after.json")
    need(before == after and before["commit"] == revision and before["source_sha256"] == source_map(), "Current functional bytes differ from full run")
    return {str(path): identity(path) for path in (folder/"state.json", host_path, raw, folder/"source-before.json", folder/"source-after.json")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--canonical-run", type=Path, required=True)
    parser.add_argument("--canonical-host-proof", type=Path, required=True)
    parser.add_argument("--final", type=Path, required=True)
    parser.add_argument("--execute-after-full", action="store_true", required=True)
    parser.add_argument("--allow-checkout-eol", action="store_true")
    parser.add_argument("--no-native-sources", action="store_true")
    args = parser.parse_args()
    need(os.name == "nt" and re.fullmatch("[0-9a-f]{40}", args.revision), "Approved Windows/full commit required")
    need(args.revision == QUALIFIED_REVISION and args.canonical_run.absolute() == QUALIFIED_FULL and
         args.canonical_host_proof.absolute() == QUALIFIED_FULL/"authoritative-host-termination.json",
         "Only the reviewed f380 revision and exact040946652 full run are admitted")
    final = guarded(args.final, WORKSPACE)
    need(final.parent == WORKSPACE and final.name == "HAS-Review-20261113-SFM-Joints-"+args.revision[:7] and not final.exists(), "Exact NEW review target required")
    need(final != OLD_REVIEW and OLD_REVIEW.is_dir(), "Preserve the existing12071fe review")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    need(revision == args.revision, "Current HEAD differs from requested source")
    full_gate = canonical_gate(args.canonical_run, args.canonical_host_proof, revision)
    lock = load(HERE/"input-lock.json")
    native_path = NATIVE_RUN/"verification.json"
    need(identity(native_path) == lock["native_verification"], "Fresh native verification identity differs")
    native = load(native_path)
    need(identity(native_path) == lock["native_verification"], "Fresh native verification changed while read")
    need(native["passed"] is True and all(native["preservation"].values()), "Fresh4case native verification required")
    preparation = {str(HERE/name): identity(HERE/name) for name in ("build_after_full.py", "input-lock.json", "README.template.md")}
    need(tree(SOURCEIO) == lock["sourceio_files"] and (SOURCEIO/"LICENSE").is_file(), "Approved local SourceIO differs")
    need(all(identity(Path(path)) == expected for path, expected in lock["runtime_executables"].items()), "Approved runtime file differs")
    exporter = Path(lock["exporter_root"])
    need(exporter_sources(exporter) == lock["exporter_noncache_sources"], "Installed exporter source catalogue differs")
    families = lock["native_families"]
    need(sum(len(rows) for rows in families.values()) == 495 and sum(row["bytes"] for rows in families.values() for row in rows.values()) == 451266730,
         "Expected current495file/451266730byte native catalogue")
    need(all(tree(Path(folder)) == rows for folder, rows in families.items()), "Native source family changed")
    for project in lock["projects"]:
        need(identity(Path(project["source"])) == project["identity"], "Packed review project changed")
        package_readback(Path(project["source"]))
    reviews = sorted(p for p in WORKSPACE.glob("HAS-Review-*") if p.is_dir())
    protected_reviews = {str(path): tree(path) for path in reviews}
    source_before = source_map(); sourceio_before = tree(SOURCEIO)
    for name, digest in source_before.items():
        if name.split("/", 1)[0] in ("src", "tools", "data", "examples") or name in ENTRY:
            need(native["source_before"]["files"].get(name, {}).get("sha256") == digest,
                 "Current app code differs from the actual4case native source context: "+name)
    scope = [*FUNCTIONAL, *ENTRY]
    changed = subprocess.check_output(["git", "diff", "HEAD", "--name-only", "--", *scope], cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "--", *scope], cwd=ROOT, text=True).splitlines()
    need(not [name for name in changed+untracked if "__pycache__" not in Path(name).parts and not name.endswith(".pyc")], "Uncommitted functional source remains")
    # Exact committed snapshot. Explicit EOL admission is recorded separately;
    # no working source, Git file or final Git blob is ever normalized in place.
    eol = []
    committed_files = git_blobs(revision, list(source_before))
    for name in source_before:
        committed = committed_files[name]
        working = (ROOT/name).read_bytes()
        text = Path(name).suffix in TEXT_SUFFIXES or name in TEXT_PATHS
        need(working == committed or args.allow_checkout_eol and text and
             working.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n"), "Working/Git content differs: "+name)
        if working != committed: eol.append({"path": name, "tested_working_sha256": hashlib.sha256(working).hexdigest(), "final_Git_blob_sha256": hashlib.sha256(committed).hexdigest()})
    helper = ROOT/"tools/build_owner_review_snapshot.py"
    spec = importlib.util.spec_from_file_location("sfm_review_snapshot_copy_only", helper)
    snapshot = importlib.util.module_from_spec(spec); spec.loader.exec_module(snapshot)
    # First mutation: reserve the final exact fresh sibling. Failures leave this
    # owned partial review for root inspection; there is deliberately no cleanup.
    final.mkdir(exist_ok=False); write_new(final/"BUILD-STARTED.json", {"source_commit": revision, "graphics_launched": False})
    studio = final/"Studio"; actual_revision, frozen = snapshot.freeze_source(ROOT, studio, revision)
    need(actual_revision == revision and not (studio/"output").exists() and not (studio/".godot").exists(), "Exact clean source snapshot required")
    profile = "HAS SFM Joints Review "+revision[:7]+" "+str(time.time_ns())
    need(not (studio/"override.cfg").exists(), "Snapshot unexpectedly contains a committed profile override")
    (studio/"override.cfg").write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n', encoding="utf-8", newline="\n")
    dependency = final/"Dependencies"/("sourceio-"+PIN)
    for name, expected in sourceio_before.items(): copy_new(SOURCEIO/name, dependency/name, final, expected)
    projects = []
    for row in lock["projects"]:
        target = final/"Examples"/(row["title"]+".has")
        copy_new(Path(row["source"]), target, final, row["identity"])
        projects.append({"title": row["title"], "file": target.relative_to(final).as_posix(), **identity(target), **package_readback(target)})
    native_rows = []
    if not args.no_native_sources:
        for row in lock["source_chooser"]:
            source_root = Path(row["resource_root"]); destination = final/"Native sources"/row["folder"]
            for name, expected in families[str(source_root)].items(): copy_new(source_root/name, destination/name, final, expected)
            native_rows.append({"name": row["name"], "MDL": (destination/row["relative_MDL"]).relative_to(final).as_posix()})
    runtime = lock["runtime_paths"]
    lines = ["@echo off", "setlocal", 'set "HYBRID_PYTHON='+runtime["python"]+'"', 'set "HYBRID_GODOT='+runtime["godot"]+'"',
             'set "HYBRID_FFMPEG='+runtime["ffmpeg"]+'"', 'set "HYBRID_SOURCE_BLENDER='+runtime["blender"]+'"',
             'set "HYBRID_SOURCEIO=%~dp0Dependencies\\sourceio-'+PIN+'"', 'set "PYTHONDONTWRITEBYTECODE=1"']
    def launcher(name, project=None):
        command = 'start "" "'+runtime["pythonw"]+'" "%~dp0Studio\\launch.pyw"'
        if project is not None: command += ' "%~dp0'+project.replace("/", "\\")+'"'
        (final/name).write_bytes(("\r\n".join([*lines, command])+"\r\n").encode("utf-8"))
    launcher("Start review.bat")
    for project in projects: launcher("Open "+project["title"]+".bat", project["file"])
    guide = (HERE/"README.template.md").read_text(encoding="utf-8").replace("{{REVISION}}", revision)
    guide += "\nNative source copies are "+("included; use the four copied-MDL paths above." if native_rows else "omitted for this build; the four packed examples remain self-contained.")+"\n"
    (final/"README.md").write_text(guide, encoding="utf-8", newline="\n")
    write_new(final/"Native-source-chooser.json", {"format": "has_private_SFM_source_chooser_1", "models": native_rows})
    need(source_map() == source_before and tree(SOURCEIO) == sourceio_before, "Main source/SourceIO changed during build")
    need(all(tree(Path(path)) == expected for path, expected in protected_reviews.items()), "A previous review changed during build")
    need(all(tree(Path(path)) == expected for path, expected in families.items()), "Original native family changed during build")
    need(all(identity(Path(path)) == expected for path, expected in lock["runtime_executables"].items()), "Shared runtime changed during build")
    need(exporter_sources(exporter) == lock["exporter_noncache_sources"], "Installed exporter source changed during build")
    need(all(hashlib.sha256((studio/name).read_bytes()).hexdigest() == digest for name, digest in frozen.items()), "Final committed source differs")
    need(tree(dependency) == sourceio_before, "Final SourceIO copy differs")
    need(all(identity(Path(path)) == expected for path, expected in full_gate.items()), "Full-run gate changed")
    need(all(identity(Path(path)) == expected for path, expected in preparation.items()), "Reviewed builder preparation changed")
    report = {"format": "has_new_SFM_joints_review_build_1", "passed": True, "final": str(final), "source_commit": revision,
              "builder_preparation": preparation,
              "profile": profile, "source_mode": "exact_Git_blobs", "source_hashes": frozen, "checkout_EOL_admission": eol,
              "projects": projects, "native_sources_included": bool(native_rows), "native_source_files": 495 if native_rows else 0,
              "native_source_bytes": 451266730 if native_rows else 0, "SourceIO_local_copy_exact": True,
              "sourceio_revision": PIN, "sourceio_files": len(sourceio_before), "full_run_gate": full_gate,
              "installed_exporter_sources_preserved": len(lock["exporter_noncache_sources"]),
              "previous_reviews_preserved": list(protected_reviews), "original_native_families_preserved": True,
              "shared_runtimes_preserved": True, "installed_Studio_not_written": True,
              "write_boundaries": [str(final)], "graphics_launched": False, "startup_or_final_replay": "UNRUN_root_private_validation_next",
              "native_Source_solver": "not_implemented", "owner_participation_requested": False}
    write_new(final/"BUILD-VERIFICATION.json", report)
    print(json.dumps({"final": str(final), "source_commit": revision, "passed": True, "graphics_launched": False}))


if __name__ == "__main__": main()
