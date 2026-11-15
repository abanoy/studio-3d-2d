"""Explicit background converter protocol; does not launch anything on import.

Original graphical private receipts are never edited or reinterpreted as clean.
Headless parent/Python/Blender attestation must independently close the gap.
"""
from __future__ import annotations
import hashlib
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
import stage_resources as S
import win_desktop_attestation as Win

HERE = Path(__file__).absolute().parent
TASK, ROOT = S.TASK, S.CHECKOUT
PROTOTYPE = ROOT  # Actual current main worker, not a prototype copy.
INPUT_STAGE = ROOT / "output/sfm-next-cases-20261112/stage"
PYTHON = Path(r"C:\Program Files\Python313\python.exe")
PYTHONW = Path(r"C:\Program Files\Python313\pythonw.exe")
BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
SOURCEIO = ROOT / "output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
PRIVATE = ROOT / "tools/private_desktop.py"
PREPARE = PROTOTYPE / "tools/prepare_source.py"
BRIDGE = PROTOTYPE / "tools/blender_source_bridge.py"
BOOTSTRAP = HERE / "background_python_bootstrap.py"
OBSERVER = HERE / "background_blender_observer.py"
WORKER_SHA = {str(ROOT / name): value for name, value in {'tools/prepare_source.py': '2d23571e8bbcfe8c5cbde98bce006282c991f7c2e08670215bc552dc69b3c23e', 'tools/blender_source_bridge.py': 'e885074a2cb8c21976b25429e9c09c43c976eca760b835bc4b295fcac6185f4d', 'tools/source_appearance.py': '97b54184b92b391feb55f91c9308a89821574dd16f1f292318c13ed07a521f7b', 'tools/source_mdl_choices.py': 'a0f5e551ba9e2e38e3a92ca1d824a09311bf4ec4979a0d9947c128d15666e555', 'tools/source_choice_io.py': '7d193d4e29389f27483ce3670ce240433af526bd8e186b6851a581fb22e70640', 'tools/source_archive.py': '44fc9c9ca6d3b81aa34d72634f3a23d57624d0e96c57599f3c03b9e7af4cc131'}.items()}

NATIVE_MODULES = {"python": {"asset_audit", "source_archive", "source_paths", "source_installation", "source_case", "source_content", "source_appearance"},
                  "blender": {"asset_audit", "source_archive", "source_texture", "source_case", "source_eyes", "source_lights", "source_lightmaps", "source_appearance"}}
ALL_NATIVE_MODULES = set.union(*NATIVE_MODULES.values())
REQUIRED_SOURCES = {*WORKER_SHA, *[str(HERE / name) for name in
                    ["background_route.py", "background_python_bootstrap.py", "background_blender_observer.py", "win_desktop_attestation.py", "stage_resources.py"]],
                    *[str(PROTOTYPE / "tools" / (name + ".py")) for name in ALL_NATIVE_MODULES]}


def normalized(path):
    return str(Path(path).absolute()).replace("\\", "/").rstrip("/").casefold()


def owned(path, root):
    path, root = Path(path).absolute(), Path(root).absolute()
    S.no_reparse(path)
    S.require(path != root and path.is_relative_to(root) and ".." not in path.parts, "Background path escaped owned case")
    return path


def read_bound(path, digest):
    S.no_reparse(path)
    S.require(re.fullmatch("[0-9a-f]{64}", digest or "") and path.stat().st_size <= 128 * 1024, "Invalid background request bounds/hash")
    raw = path.read_bytes()
    S.require(hashlib.sha256(raw).hexdigest() == digest, "Background request bytes changed")
    return json.loads(raw, object_pairs_hook=S.unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite background JSON")))


def source_observation(expected):
    S.require(isinstance(expected, dict) and set(expected) == REQUIRED_SOURCES, "Background source catalogue differs")
    observed = {}
    for source, digest in expected.items():
        S.require(re.fullmatch("[0-9a-f]{64}", digest) is not None, "Invalid frozen source hash")
        observed[source] = S.identity(Path(source))["sha256"]
        S.require(observed[source] == digest, "Background/native worker source changed")
    S.require(all(observed[source] == digest for source, digest in WORKER_SHA.items()), "Frozen native worker overlay changed")
    return observed


def expected_native_imports(role, sources):
    S.require(role in NATIVE_MODULES, "Unknown native import role")
    return {name: {"path": str(PROTOTYPE / "tools" / (name + ".py")),
                   "sha256": sources[str(PROTOTYPE / "tools" / (name + ".py"))]} for name in sorted(NATIVE_MODULES[role])}


@contextmanager
def native_import_context(role, sources):
    """Restore normal script-local resolution, including already cached guards."""
    expected = expected_native_imports(role, sources)
    original_path = list(sys.path)
    original_modules = {name: sys.modules.get(name) for name in ALL_NATIVE_MODULES}
    for name in ALL_NATIVE_MODULES:
        sys.modules.pop(name, None)
    sys.path.insert(0, str(PROTOTYPE / "tools"))
    def observe():
        observed = {}
        for name, value in expected.items():
            module = sys.modules.get(name)
            path = Path(getattr(module, "__file__", "")).absolute()
            S.require(normalized(path) == normalized(value["path"]), "Native helper resolved outside frozen prototype: " + name)
            observed[name] = {"path": str(path), "sha256": S.identity(path)["sha256"]}
            S.require(observed[name]["sha256"] == value["sha256"], "Native imported helper bytes differ: " + name)
        return observed
    try:
        yield observe
    finally:
        for name, module in original_modules.items():
            sys.modules.pop(name, None)
            if module is not None:
                sys.modules[name] = module
        sys.path[:] = original_path


def native_options(command, case):
    S.require(isinstance(command, list) and all(isinstance(value, str) for value in command) and len(command) >= 5,
              "Invalid original native command")
    S.require([normalized(command[0]), *command[1:3], normalized(command[3])] == [normalized(PYTHON), "-B", "-u", normalized(PREPARE)],
              "Unreviewed native worker command prefix")
    source = owned(command[4], INPUT_STAGE)
    S.require(source.suffix.casefold() == ".mdl", "Background route applies only to selected staged MDL")
    tail = command[5:]
    S.require(len(tail) % 2 == 0, "Invalid original native command options")
    options = dict(zip(tail[::2], tail[1::2]))
    required = {"--output", "--sourceio", "--blender", "--mount-plan", "--gmod", "--workshop"}
    S.require(len(options) * 2 == len(tail) and set(options) in [required, required | {"--appearance"}], "Unexpected/duplicate native command option")
    expected = {"--output": case / "bundle", "--sourceio": SOURCEIO, "--blender": BLENDER,
                "--mount-plan": TASK / "empty-mount-plan.json", "--gmod": case / "absent-gmod", "--workshop": case / "absent-workshop"}
    S.require(all(normalized(options[key]) == normalized(value) for key, value in expected.items()), "Native command changed its approved output/runtime/mounts")
    if "--appearance" in options:
        owned(options["--appearance"], TASK / "requests")
    return options


def validate_request(request, case):
    S.require(request.get("format") == "has_background_python_request_1" and normalized(request["case"]) == normalized(case), "Wrong background request/case")
    S.require(re.fullmatch("[0-9a-f]{32}", request.get("nonce", "")) is not None and
              re.fullmatch("[0-9a-f]{40}", request.get("root_revision", "")) is not None and
              re.fullmatch("[0-9a-f]{64}", request.get("input_lock_sha256", "")) is not None, "Invalid background nonce/checkpoint binding")
    native_options(request["native_command"], case)
    S.require(type(request["earliest_filetime"]) is int and request["earliest_filetime"] > 0
              and request["expected_window_station"], "Invalid background freshness/window station")
    for role, path in [("python", PYTHON), ("blender", BLENDER)]:
        expected = request["executables"][role]
        S.require(normalized(expected["path"]) == normalized(path) and re.fullmatch("[0-9a-f]{64}", expected["sha256"]), "Unreviewed background executable")


def prepare(case, native_command, frozen_files, root_revision, input_lock_sha256, parent_observation):
    """Write one fresh case request; no child/private/Blender process is started."""
    case = owned(case, TASK)
    S.require(case.is_dir() and not (case / "bundle").exists(), "Background case must exist with a fresh bundle")
    native_options(native_command, case)
    expected_sources = {source: frozen_files[source]["sha256"] for source in REQUIRED_SOURCES}
    source_observation(expected_sources)
    request = {"format": "has_background_python_request_1", "case": str(case), "nonce": uuid.uuid4().hex,
               "root_revision": root_revision, "input_lock_sha256": input_lock_sha256,
               "earliest_filetime": parent_observation["observed_filetime"], "expected_window_station": parent_observation["window_station"],
               "native_command": native_command, "sources": expected_sources,
               "executables": {role: {"path": str(path), "sha256": frozen_files[str(path)]["sha256"]}
                               for role, path in [("python", PYTHON), ("blender", BLENDER)]}}
    validate_request(request, case)
    path = case / "background-request.json"
    S.save(path, request)
    digest = S.identity(path)["sha256"]
    child = [str(PYTHON), "-B", "-u", str(BOOTSTRAP), "--headless", "--request", str(path), "--request-sha256", digest]
    private = [str(PYTHONW), str(PRIVATE), "--receipt", str(case / "private-receipt.json"), "--timeout", "700",
               "--cancel-file", str(case / "cancel.flag"), "--", *child]
    return {"request": request, "request_path": str(path), "request_sha256": digest, "child_command": child, "private_command": private}


def observation(role, request, request_sha256):
    snapshot = Win.capture_self()
    expected = request["executables"][role]
    S.require(normalized(snapshot["executable"]) == normalized(expected["path"]) and snapshot["executable_sha256"] == expected["sha256"], "Actual background executable differs")
    S.require(re.fullmatch("HAS_Test_[0-9a-f]{32}", snapshot["desktop"]) and snapshot["window_station"] == request["expected_window_station"],
              "Background child is not on a fresh private desktop/window station")
    return {"format": "has_background_desktop_attestation_1", "role": role, "nonce": request["nonce"],
            "root_revision": request["root_revision"], "input_lock_sha256": request["input_lock_sha256"],
            "request_sha256": request_sha256, "sources": source_observation(request["sources"]), "self": snapshot}


def blender_command(request, conversion_request):
    return [str(BLENDER), "--background", "--factory-startup", "--disable-autoexec", "--offline-mode",
            "--python-exit-code", "1", "--python", str(BRIDGE), "--", str(conversion_request)]


def instrument_blender(command, request, case, python_attestation, original_request_sha256, environment):
    """Validate the exact worker command; replace only its script and add two env keys."""
    conversion_request = case / "bundle/conversion-request.json"
    S.require(command == blender_command(request, conversion_request), "Unreviewed subprocess command; observer refused")
    observer_request = {"format": "has_background_blender_request_1", "case": str(case), "nonce": request["nonce"],
                        "root_revision": request["root_revision"], "input_lock_sha256": request["input_lock_sha256"],
                        "earliest_filetime": request["earliest_filetime"], "expected_window_station": request["expected_window_station"],
                        "expected_desktop": python_attestation["self"]["desktop"], "sources": request["sources"],
                        "executables": request["executables"], "python_pid": python_attestation["self"]["pid"],
                        "python_creation_filetime": python_attestation["self"]["creation_filetime"],
                        "python_request_sha256": original_request_sha256, "conversion_request": str(conversion_request),
                        "conversion_request_sha256": S.identity(conversion_request)["sha256"]}
    observer_path = case / "blender-observer-request.json"
    S.save(observer_path, observer_request)
    observer_sha = S.identity(observer_path)["sha256"]
    changed = list(command); changed[changed.index("--python") + 1] = str(OBSERVER)
    child_environment = dict(environment)
    child_environment["HAS_BACKGROUND_OBSERVER_REQUEST"] = str(observer_path)
    child_environment["HAS_BACKGROUND_OBSERVER_SHA256"] = observer_sha
    return changed, child_environment, observer_sha


def validate_proof(request, request_sha, private, python, blender, spawn, outer, python_done, blender_done, worker, latest_filetime):
    """Pure fail-closed contract, usable by CPU negative controls without WinAPI."""
    expected_exit = python_done.get("worker_exit")
    S.require(type(expected_exit) is int and expected_exit in {0, 1} and private.get("exit") == expected_exit and not private.get("error"), "Background wrapper/worker exit was not clean")
    S.require(private.get("format") == "studio_private_desktop_1" and private.get("job_closed") and private.get("desktop_closed")
              and not private.get("foreground_child_observed", True) and not private.get("desktop_switch_requested", True), "Private background job/desktop did not close cleanly")
    desktop = private.get("desktop", "")
    S.require(re.fullmatch("HAS_Test_[0-9a-f]{32}", desktop), "Invalid fresh private desktop name")
    earliest = request["earliest_filetime"]
    S.require(type(latest_filetime) is int and latest_filetime >= earliest, "Invalid parent observation interval")
    S.require(spawn.get("format") == "has_background_blender_spawn_1" and spawn.get("nonce") == request["nonce"]
              and spawn.get("python_request_sha256") == request_sha and type(spawn.get("observed_filetime")) is int
              and earliest <= spawn["observed_filetime"] <= latest_filetime, "Missing/wrong/stale Blender spawn binding")
    S.require(outer.get("format") == "has_background_outer_launch_1" and outer.get("nonce") == request["nonce"]
              and type(outer.get("creation_filetime")) is int and earliest <= outer["creation_filetime"] <= latest_filetime,
              "Missing/wrong/stale private-wrapper launch binding")
    for role, attestation in [("python", python), ("blender", blender)]:
        snapshot = attestation.get("self", {})
        S.require(attestation.get("format") == "has_background_desktop_attestation_1" and attestation.get("role") == role
                  and attestation.get("nonce") == request["nonce"] and attestation.get("root_revision") == request["root_revision"]
                  and attestation.get("input_lock_sha256") == request["input_lock_sha256"] and attestation.get("sources") == request["sources"], "Missing/wrong/stale background attestation binding")
        expected_request_sha = request_sha if role == "python" else spawn["observer_request_sha256"]
        S.require(attestation.get("request_sha256") == expected_request_sha, "Attestation request hash differs")
        S.require(snapshot.get("api") == "WinAPI self observation" and snapshot.get("desktop") == desktop
                  and snapshot.get("window_station") == request["expected_window_station"], "Attested child desktop/window station differs")
        S.require(type(snapshot.get("pid")) is int and snapshot["pid"] > 0 and type(snapshot.get("thread_id")) is int and snapshot["thread_id"] > 0,
                  "Missing actual process/thread identity")
        S.require(type(snapshot.get("creation_filetime")) is int and type(snapshot.get("observed_filetime")) is int
                  and earliest <= snapshot["creation_filetime"] <= snapshot["observed_filetime"] <= latest_filetime, "Stale/out-of-range background process observation")
        expected = request["executables"][role]
        S.require(normalized(snapshot.get("executable", "")) == normalized(expected["path"])
                  and snapshot.get("executable_sha256") == expected["sha256"], "Attested executable differs")
    p, b = python["self"], blender["self"]
    S.require(p["pid"] == private.get("child_pid") == spawn.get("python_pid") and p["parent_pid"] == outer.get("pid")
              and p["parent_creation_filetime"] == outer.get("creation_filetime") <= p["creation_filetime"], "Python child/wrapper PID or creation identity differs")
    S.require(b["pid"] == spawn.get("blender_pid") == worker.get("blender_pid") and b["parent_pid"] == p["pid"]
              and b["parent_creation_filetime"] == p["creation_filetime"] and b["creation_filetime"] == spawn.get("blender_creation_filetime")
              and p["creation_filetime"] == spawn.get("python_creation_filetime"), "Blender child/parent/creation identity differs")
    S.require(p["observed_filetime"] <= b["creation_filetime"], "Blender observation precedes bootstrap identity")
    for role, completion in [("python", python_done), ("blender", blender_done)]:
        S.require(completion.get("format") == "has_background_completion_1" and completion.get("role") == role
                  and completion.get("nonce") == request["nonce"] and completion.get("sources_after") == request["sources"]
                  and type(completion.get("observed_filetime")) is int and b["observed_filetime"] <= completion["observed_filetime"] <= latest_filetime,
                  "Missing/wrong/stale background completion")
        S.require(completion.get("native_import_origins") == expected_native_imports(role, request["sources"]), "Native worker/bridge import provenance differs")
    S.require(python_done.get("intercepted_blender_commands") == 1 and python_done.get("worker_exit") == expected_exit,
              "Unexpected instrumented worker invocation")
    S.require(python_done.get("exception") is None, "Python observation bootstrap did not complete normally")
    S.require((expected_exit == 0 and blender_done.get("status") == "ok") or
              (expected_exit == 1 and blender_done.get("status") == "exception"), "Blender observer completion disagrees with worker exit")
    S.require((blender_done["status"] == "ok" and blender_done.get("exception") is None) or
              (blender_done["status"] == "exception" and isinstance(blender_done.get("exception"), dict)
               and bool(blender_done["exception"].get("type"))), "Blender observation completion lacks actual exception/normal status")
    S.require(blender_done.get("conversion_request_sha256") == spawn.get("conversion_request_sha256"), "Observed conversion request differs")
    S.require(spawn.get("original_command") == blender_command(request, Path(request["case"]) / "bundle/conversion-request.json"), "Observed original Blender command differs")
    changed = list(spawn["original_command"]); changed[changed.index("--python") + 1] = str(OBSERVER)
    S.require(spawn.get("observed_command") == changed, "Blender instrumentation changed more than the observation script")
    return {"format": "has_background_isolation_verification_1", "passed": True, "expected_worker_exit": expected_exit,
            "desktop": desktop, "window_station": request["expected_window_station"], "python_pid": p["pid"], "blender_pid": b["pid"],
            "private_monitor_child_desktop_confirmed": private.get("child_desktop_confirmed"),
            "independent_python_and_blender_self_attestation": True,
            "original_private_receipt_edited": False, "scope": "Explicit headless background route only; graphical private receipt rules remain unchanged."}


def read_fresh(case, name, earliest_filetime, latest_filetime):
    path = owned(case / name, case)
    S.require(path.is_file() and path.stat().st_size <= 128 * 1024, "Missing/excessive background observation file: " + name)
    before = S.identity(path)
    # FILETIME is100ns since1601; file stamps are Unix nanoseconds. The same
    # machine's recorded launch/finish interval bounds every fresh proof file.
    stamp_filetime = path.stat().st_mtime_ns // 100 + 116444736000000000
    S.require(earliest_filetime <= stamp_filetime <= latest_filetime, "Stale/out-of-range background observation file: " + name)
    value = json.loads(path.read_bytes(), object_pairs_hook=S.unique_object)
    S.require(S.identity(path) == before, "Background observation file changed while reading")
    return value, before


def verify_case(case, launch, expected_exit, latest_filetime):
    """Read exact fresh evidence files, preserving the original private receipt."""
    request = read_bound(Path(launch["request_path"]), launch["request_sha256"])
    validate_request(request, case)
    S.require(request == launch["request"], "Parent launch request changed")
    earliest = request["earliest_filetime"]
    paths = ["private-receipt.json", "python-desktop-attestation.json", "blender-desktop-attestation.json",
             "blender-spawn.json", "background-outer-launch.json", "python-background-completion.json", "blender-background-completion.json"]
    values, before = {}, {}
    for name in paths:
        values[name], before[name] = read_fresh(case, name, earliest, latest_filetime)
    observer = read_bound(case / "blender-observer-request.json", values["blender-spawn.json"]["observer_request_sha256"])
    S.require(observer["nonce"] == request["nonce"] and observer["sources"] == request["sources"]
              and observer["expected_desktop"] == values["python-desktop-attestation.json"]["self"]["desktop"]
              and observer["python_request_sha256"] == launch["request_sha256"], "Blender observer request binding differs")
    worker, worker_before = read_fresh(case / "bundle", "worker.json", earliest, latest_filetime)
    proof = validate_proof(request, launch["request_sha256"], values["private-receipt.json"],
                           values["python-desktop-attestation.json"], values["blender-desktop-attestation.json"], values["blender-spawn.json"],
                           values["background-outer-launch.json"], values["python-background-completion.json"], values["blender-background-completion.json"],
                           worker, latest_filetime)
    S.require(type(expected_exit) is int and proof["expected_worker_exit"] == expected_exit, "Unexpected native worker result")
    source_observation(request["sources"])
    for name in paths:
        S.require(S.identity(case / name) == before[name], "Background proof mutated while validating")
    S.require(S.identity(case / "bundle/worker.json") == worker_before, "Native worker PID file changed")
    proof["evidence_hashes"] = before
    proof["native_worker_pid_file"] = worker_before
    return proof


def run_outer(launch, case, bundle, environment, *, lease_confirmed=False):
    """Future exclusive-lease execution only; reuses the unchanged private tool."""
    S.require(lease_confirmed and os.name == "nt", "Background execution requires explicit Windows conversion lease")
    args = launch["private_command"]
    S.require("--headless" in args and str(PRIVATE) == args[1], "Explicit background private command required")
    with (case / "process.log").open("x", encoding="utf-8") as log:
        process = subprocess.Popen(args, cwd=PROTOTYPE, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        start = time.monotonic()
        try:
            S.save(case / "background-outer-launch.json", {"format": "has_background_outer_launch_1",
                   "nonce": launch["request"]["nonce"], "pid": process.pid,
                   "creation_filetime": Win.process_creation(process.pid), "observed_filetime": Win.system_filetime()})
            while process.poll() is None:
                excessive = any(path.exists() and path.stat().st_size > maximum for path, maximum in
                                [(case / "process.log", 16 * 1024 * 1024), (bundle / "conversion.log", 32 * 1024 * 1024)])
                if excessive or time.monotonic() - start > 720:
                    (case / "cancel.flag").write_text("Owned background driver timeout/log budget; cancel this private job only.\n")
                    try: process.wait(timeout=15)
                    except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
                    raise ValueError("Owned background converter exceeded time/log budget; evidence retained")
                time.sleep(.1)
            return process.returncode, time.monotonic() - start
        finally:
            if process.poll() is None:
                (case / "cancel.flag").write_text("Owned background driver stopping; cancel this private job only.\n")
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
